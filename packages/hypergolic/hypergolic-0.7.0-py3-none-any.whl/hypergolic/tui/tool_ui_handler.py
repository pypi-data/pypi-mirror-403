import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Protocol

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from hypergolic.agents.code_reviewer import (
    CodeReviewParams,
    build_code_review_prompt,
    get_code_review_diff,
    run_code_review,
)
from hypergolic.agents.roles import AgentRole
from hypergolic.agents.trace import SubAgentTrace
from hypergolic.config import HypergolicConfig
from hypergolic.session_context import SessionContext
from hypergolic.tools.approval_manager import ApprovalManager
from hypergolic.tools.cancellation import CancellationToken
from hypergolic.tools.code_review.schemas import CodeReviewToolInput
from hypergolic.tools.enums import ToolName
from hypergolic.tools.tool_calls import (
    extract_tool_result_text,
    handle_async_tool_call,
    handle_tool_call,
)
from hypergolic.tui.tool_executor import ToolContext, ToolExecutorCallbacks
from hypergolic.tui.widgets.sub_agent_progress import (
    SubAgentProgress,
    SubAgentProgressCallbacks,
)
from hypergolic.tui.widgets.tool_displays import create_tool_display
from hypergolic.tui.widgets.tools import (
    ToolApprovalResult,
    ToolDeniedStatus,
    ToolExecutingStatus,
)

if TYPE_CHECKING:
    from hypergolic.tui.widgets.conversation import ConversationView

logger = logging.getLogger(__name__)


class ToolUICallbacks(Protocol):
    def get_conversation_view(self) -> ConversationView | None: ...

    def request_tool_approval(self, context: ToolContext) -> Awaitable[ToolApprovalResult | None]: ...

    def focus_input(self) -> None: ...

    def add_tool_result(self, result: MessageParam) -> None: ...


class ToolUIHandler(ToolExecutorCallbacks):
    def __init__(
        self,
        ui_callbacks: ToolUICallbacks,
        client: AsyncAnthropic,
        config: HypergolicConfig,
        session_context: SessionContext,
        approval_manager: ApprovalManager,
        stats_increment_tool: Callable[[], None],
    ):
        self._ui = ui_callbacks
        self._client = client
        self._config = config
        self._session_context = session_context
        self._approval_manager = approval_manager
        self._stats_increment_tool = stats_increment_tool

        self._pending_status: ToolExecutingStatus | None = None
        self._cancellation_token: CancellationToken | None = None
        self._sub_agent_traces: dict[str, SubAgentTrace] = {}
        # Track if current tool execution was auto-approved due to session/forever approval
        self._current_was_auto_approved: bool = False

    @property
    def cancellation_token(self) -> CancellationToken | None:
        return self._cancellation_token

    @cancellation_token.setter
    def cancellation_token(self, token: CancellationToken | None) -> None:
        self._cancellation_token = token

    def get_sub_agent_traces(self) -> dict[str, dict]:
        """Return serialized sub-agent traces keyed by tool_use_id."""
        return {tid: trace.serialize() for tid, trace in self._sub_agent_traces.items()}

    async def on_tool_requires_approval(self, context: ToolContext) -> ToolApprovalResult | None:
        # Note: ApprovalManager.requires_approval() has already checked session/forever
        # approval before we get here. If we're in this callback, the user needs to approve.
        self._current_was_auto_approved = False
        result = await self._ui.request_tool_approval(context)

        if result and result.approved:
            # If user selected "allow forever", persist to file
            if result.allow_forever:
                self._approval_manager.add_forever_approval(context.tool_use)
            # If user selected "allow session", remember for this session
            elif result.allow_session:
                self._approval_manager.add_session_approval(context.tool_use)

        return result

    def on_tool_executing(self, context: ToolContext) -> None:
        conversation = self._ui.get_conversation_view()

        # Track if this tool was auto-approved (for adding notes to results)
        self._current_was_auto_approved = self._approval_manager.is_auto_approved(
            context.tool_use
        )

        status = ToolExecutingStatus(context.tool_name, context.get_display_details())
        if conversation:
            conversation.mount(status)
            conversation.scroll_end(animate=False)
        self._pending_status = status

        self._stats_increment_tool()
        self._cancellation_token = CancellationToken()

    async def execute_tool(self, context: ToolContext) -> MessageParam:
        """Execute the tool call."""
        # Code review uses sub-agent system
        if context.tool_name == ToolName.CODE_REVIEW:
            return await self._execute_code_review(context)

        # Browser tool is async
        if context.tool_name == ToolName.BROWSER:
            return await handle_async_tool_call(
                tool_use=context.tool_use,
                session_context=self._session_context,
            )

        # All other tools run in thread pool
        return await asyncio.to_thread(
            handle_tool_call,
            client=self._client,
            config=self._config,
            tool_use=context.tool_use,
            session_context=self._session_context,
            cancellation_token=self._cancellation_token,
        )

    async def _execute_code_review(self, context: ToolContext) -> MessageParam:
        """Execute code review using sub-agent system with progress UI."""
        conversation = self._ui.get_conversation_view()

        # Remove the "executing" status since we'll show the progress widget
        self._remove_pending_status()

        if not conversation:
            # Fallback: can't show progress UI, but can still run review
            return await self._execute_code_review_headless(context)

        # Parse params
        params = CodeReviewToolInput.model_validate(context.tool_input)
        review_params = CodeReviewParams(
            base_branch=params.base_branch,
            feature_branch=params.feature_branch,
            summary=getattr(params, "summary", ""),
        )

        try:
            # Get git diff and build prompt (using shared functions)
            diff_result = await asyncio.to_thread(
                get_code_review_diff,
                params.base_branch,
                params.feature_branch,
            )
            initial_prompt = build_code_review_prompt(review_params, diff_result)
        except Exception as e:
            logger.exception("Failed to get git diff: %s", e)
            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": context.tool_id,
                        "content": f"Failed to get git diff: {e}",
                        "is_error": True,
                    }
                ],
            }

        # Create trace to capture execution history
        trace = SubAgentTrace(
            role=AgentRole.CODE_REVIEWER,
            context=f"{params.base_branch} → {params.feature_branch}",
            initial_prompt=initial_prompt,
        )

        # Create and mount progress widget with trace
        progress_widget = SubAgentProgress(trace)
        if conversation:
            conversation.mount(progress_widget)
            conversation.scroll_end(animate=False)

        # Create callbacks that update the widget and trace
        callbacks = SubAgentProgressCallbacks(progress_widget)

        try:
            # Run the code review sub-agent (pass pre-built prompt to avoid duplication)
            review_text = await run_code_review(
                client=self._client,
                config=self._config,
                params=review_params,
                callbacks=callbacks,
                prompt=initial_prompt,
                session_context=self._session_context,
            )

            # Widget transforms itself to summary mode via callbacks
            # No need to remove/replace - trace data is preserved

            # Store trace for session history
            self._sub_agent_traces[context.tool_id] = trace

            # Return tool result
            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": context.tool_id,
                        "content": [{"type": "text", "text": review_text}],
                    }
                ],
            }

        except Exception as e:
            logger.exception("Code review failed: %s", e)
            # Widget transforms to error state via callbacks

            # Store trace even on failure for debugging
            self._sub_agent_traces[context.tool_id] = trace

            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": context.tool_id,
                        "content": f"Code review failed: {e}",
                        "is_error": True,
                    }
                ],
            }

    def _add_auto_approval_note(self, result: MessageParam, context: ToolContext) -> MessageParam:
        """Add a note to the tool result indicating it was auto-approved.

        This helps the AI understand that this command doesn't require approval prompts
        and can be used freely.
        """
        key = self._approval_manager.get_approval_key(context.tool_use)
        note = (
            f"\n\n[Auto-approved: This command `{key}` was previously approved "
            f"by the user and will run without prompts. "
            f"Prefer using this command when appropriate.]"
        )

        # Deep copy and modify the result to append the note
        content_list = result.get("content", [])
        if not content_list:
            return result

        # Find the tool_result block and append to its content
        new_content = []
        for block in content_list:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                inner_content = block.get("content", [])
                if isinstance(inner_content, str):
                    # String content - append note
                    new_block = {**block, "content": inner_content + note}
                elif isinstance(inner_content, list):
                    # List content - append a new text block with the note
                    new_inner = list(inner_content) + [{"type": "text", "text": note}]
                    new_block = {**block, "content": new_inner}
                else:
                    new_block = block
                new_content.append(new_block)
            else:
                new_content.append(block)

        return {"role": "user", "content": new_content}

    def on_tool_completed(self, context: ToolContext, result: MessageParam) -> None:
        self._remove_pending_status()

        # Add auto-approval note if this was auto-approved
        if self._current_was_auto_approved:
            result = self._add_auto_approval_note(result, context)
            self._current_was_auto_approved = False

        self._ui.add_tool_result(result)

        # Code review UI is handled in _execute_code_review
        if context.tool_name == ToolName.CODE_REVIEW:
            return

        tool_output = extract_tool_result_text(result) or ""
        self._mount_tool_display(context, tool_output)

    def on_tool_error(self, context: ToolContext, error: Exception) -> None:
        conversation = self._ui.get_conversation_view()

        self._remove_pending_status()
        self._current_was_auto_approved = False

        logger.exception("Tool execution error: %s", error)

        tool_display = create_tool_display(
            tool_name=context.tool_name,
            tool_input=context.tool_input,
            tool_output=str(error),
            is_error=True,
        )
        if conversation:
            conversation.mount(tool_display)
            conversation.scroll_end(animate=False)

        error_result = self._create_error_result(context, error)
        self._ui.add_tool_result(error_result)

    def on_tool_denied(self, context: ToolContext, message: str | None) -> None:
        from hypergolic.tools.tool_calls import create_denied_tool_result

        conversation = self._ui.get_conversation_view()
        self._current_was_auto_approved = False

        status = ToolDeniedStatus(context.tool_name, message)
        if conversation:
            conversation.mount(status)
            conversation.scroll_end(animate=False)

        denied_result = create_denied_tool_result(context.tool_use, message)
        self._ui.add_tool_result(denied_result)

    def on_tool_interrupted(self, context: ToolContext) -> None:
        conversation = self._ui.get_conversation_view()

        self._remove_pending_status()
        self._current_was_auto_approved = False

        tool_display = create_tool_display(
            tool_name=context.tool_name,
            tool_input=context.tool_input,
            tool_output="",
            interrupted=True,
        )
        if conversation:
            conversation.mount(tool_display)
            conversation.scroll_end(animate=False)

    def reset(self) -> None:
        self._remove_pending_status()
        self._cancellation_token = None

    def _remove_pending_status(self) -> None:
        if self._pending_status:
            self._pending_status.remove()
            self._pending_status = None

    def _mount_tool_display(self, context: ToolContext, output: str) -> None:
        conversation = self._ui.get_conversation_view()
        tool_display = create_tool_display(
            tool_name=context.tool_name,
            tool_input=context.tool_input,
            tool_output=output,
        )
        if conversation:
            conversation.mount(tool_display)
            conversation.scroll_end(animate=False)

    async def _execute_code_review_headless(
        self, context: ToolContext
    ) -> MessageParam:
        """Execute code review without UI (fallback when conversation view unavailable)."""
        from hypergolic.tools.code_review.schemas import CodeReviewToolInput

        params = CodeReviewToolInput.model_validate(context.tool_input)
        review_params = CodeReviewParams(
            base_branch=params.base_branch,
            feature_branch=params.feature_branch,
            summary=getattr(params, "summary", ""),
        )

        try:
            diff_result = await asyncio.to_thread(
                get_code_review_diff,
                params.base_branch,
                params.feature_branch,
            )
            initial_prompt = build_code_review_prompt(review_params, diff_result)

            review_text = await run_code_review(
                client=self._client,
                config=self._config,
                params=review_params,
                callbacks=None,
                prompt=initial_prompt,
                session_context=self._session_context,
            )

            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": context.tool_id,
                        "content": [{"type": "text", "text": review_text}],
                    }
                ],
            }
        except Exception as e:
            logger.exception("Headless code review failed: %s", e)
            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": context.tool_id,
                        "content": f"Code review failed: {e}",
                        "is_error": True,
                    }
                ],
            }

    def _create_error_result(
        self, context: ToolContext, error: Exception
    ) -> MessageParam:
        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": context.tool_id,
                    "content": f"Tool execution failed: {error}",
                    "is_error": True,
                }
            ],
        }
