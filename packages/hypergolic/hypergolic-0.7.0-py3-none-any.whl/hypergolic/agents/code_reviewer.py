"""Code reviewer sub-agent implementation."""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

from anthropic import AsyncAnthropic

from hypergolic.agents.roles import AgentRole
from hypergolic.agents.sub_agent import SubAgentCallbacks, SubAgentRunner
from hypergolic.config import HypergolicConfig
from hypergolic.prompts.resolvers import build_code_reviewer_system_prompt
from hypergolic.session_context import SessionContext
from hypergolic.tools.common import perform_command
from hypergolic.tools.enums import ToolName
from hypergolic.tools.file_explorer import FileExplorerToolInput, file_explorer
from hypergolic.tools.read_file import ReadFileToolInput, read_file
from hypergolic.tools.search_files import SearchFilesToolInput, search_files
from hypergolic.tools.tool_list import CODE_REVIEW_TOOLS

logger = logging.getLogger(__name__)


@dataclass
class CodeReviewParams:
    """Parameters for a code review."""

    base_branch: str
    feature_branch: str
    summary: str = ""


class CodeReviewToolHandler:
    """Handles tool calls for the code reviewer sub-agent."""

    async def handle_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool and return the result."""
        # Run tool execution in thread pool since tools are sync
        return await asyncio.to_thread(self._handle_tool_sync, tool_name, tool_input)

    def _handle_tool_sync(self, tool_name: str, tool_input: dict) -> str:
        """Synchronous tool execution."""
        try:
            match tool_name:
                case ToolName.FILE_EXPLORER:
                    params = FileExplorerToolInput.model_validate(tool_input)
                    result = file_explorer(params)
                case ToolName.READ_FILE:
                    params = ReadFileToolInput.model_validate(tool_input)
                    result = read_file(params)
                case ToolName.SEARCH_FILES:
                    params = SearchFilesToolInput.model_validate(tool_input)
                    result = search_files(params)
                case _:
                    return f"Unknown tool: {tool_name}"

            # Extract text from result
            text_parts = []
            for item in result:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            return "\n".join(text_parts) if text_parts else str(result)

        except Exception as e:
            logger.exception("Tool error: %s", e)
            return f"Tool error: {e}"


def build_code_review_prompt(params: CodeReviewParams, git_diff: str) -> str:
    """Build the prompt for the code review sub-agent."""
    return f"""# CODE REVIEW

Perform a code review between the following two branches:
- Base Branch: {params.base_branch}
- Feature Branch: {params.feature_branch}

## Summary of Changes:
{params.summary or "No summary provided."}

## Git Diff:
{git_diff}
"""


def get_code_review_diff(base_branch: str, feature_branch: str) -> str:
    """Get the git diff between two branches."""
    return perform_command(
        parts=["git", "diff", f"{base_branch}..{feature_branch}"],
        cwd=Path.cwd(),
    )


class NoOpCallbacks:
    """No-op callbacks for headless sub-agent execution."""

    def on_sub_agent_start(self, role: AgentRole) -> None:
        pass

    def on_sub_agent_text(self, text: str) -> None:
        pass

    def on_sub_agent_tool_start(self, tool_name: str, tool_input: dict) -> None:
        pass

    def on_sub_agent_tool_complete(self, tool_name: str, result: str) -> None:
        pass

    def on_sub_agent_complete(self, final_text: str) -> None:
        pass

    def on_sub_agent_error(self, error: Exception) -> None:
        pass


async def run_code_review(
    client: AsyncAnthropic,
    config: HypergolicConfig,
    params: CodeReviewParams,
    callbacks: SubAgentCallbacks | None = None,
    prompt: str | None = None,
    session_context: SessionContext | None = None,
) -> str:
    """Run a code review as a sub-agent and return the review text.

    Args:
        client: The Anthropic API client
        config: Hypergolic configuration
        params: Code review parameters
        callbacks: Progress callbacks for UI updates
        prompt: Optional pre-built prompt (if None, will be generated)
        session_context: Session context for worktree information
    """
    if prompt is None:
        # Get git diff and build prompt
        git_diff = await asyncio.to_thread(
            get_code_review_diff,
            params.base_branch,
            params.feature_branch,
        )
        prompt = build_code_review_prompt(params, git_diff)

    # Use no-op callbacks if none provided (headless mode)
    actual_callbacks = callbacks if callbacks is not None else NoOpCallbacks()

    system_prompt = build_code_reviewer_system_prompt(session_context)
    tool_handler = CodeReviewToolHandler()

    runner = SubAgentRunner(
        client=client,
        role=AgentRole.CODE_REVIEWER,
        system_prompt=system_prompt,
        tools=CODE_REVIEW_TOOLS,
        model=config.provider.model,
        max_tokens=config.provider.max_tokens,
        callbacks=actual_callbacks,
        tool_handler=tool_handler,
    )

    return await runner.run(prompt)
