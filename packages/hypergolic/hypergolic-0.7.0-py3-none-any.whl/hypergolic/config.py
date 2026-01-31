import os
from pathlib import Path

from pydantic import BaseModel, Field

from hypergolic.providers import Provider, get_default_provider
from hypergolic.tools.enums import ToolName

USER_PROMPT_PATH = Path.home() / ".hypergolic" / "user_prompt.md"
PROJECT_PROMPT_FILENAME = "AGENTS.md"

# Environment variable names
ENV_BROWSER_AUTO_APPROVE = "HYPERGOLIC_BROWSER_AUTO_APPROVE"
ENV_ALL_TOOLS_AUTO_APPROVE = "HYPERGOLIC_ALL_TOOLS_AUTO_APPROVE"
ENV_AUTO_SUMMARIZE = "HYPERGOLIC_AUTO_SUMMARIZE"


def _env_bool(var_name: str, default: bool = False) -> bool:
    """Read a boolean from an environment variable."""
    val = os.environ.get(var_name, "").lower()
    if val in ("1", "true", "yes"):
        return True
    if val in ("0", "false", "no"):
        return False
    return default


def get_default_auto_approved_tools() -> set[ToolName]:
    return {
        ToolName.CODE_REVIEW,
        ToolName.FILE_EXPLORER,
        ToolName.FILE_OPERATIONS,
        ToolName.GIT,
        ToolName.LSP,
        ToolName.READ_FILE,
        ToolName.SEARCH_FILES,
        ToolName.WINDOW_MANAGEMENT,
    }


class HypergolicConfig(BaseModel):
    provider: Provider = Field(
        description="LLM providers",
        default_factory=get_default_provider,
    )
    require_tool_approval: bool = Field(
        default_factory=lambda: not _env_bool(ENV_ALL_TOOLS_AUTO_APPROVE),
        description="If True, prompts the user to approve each tool call before execution",
    )
    auto_approved_tools: set[ToolName] = Field(
        default_factory=get_default_auto_approved_tools,
        description="Set of tools that don't require user approval, even when require_tool_approval is True",
    )
    browser_auto_approve: bool = Field(
        default_factory=lambda: _env_bool(ENV_BROWSER_AUTO_APPROVE),
        description="If True, browser tool does not require approval for external URLs. "
        "WARNING: Only enable in trusted/automated environments. "
        f"Can be set via {ENV_BROWSER_AUTO_APPROVE} env var.",
    )
    auto_summarize: bool = Field(
        default_factory=lambda: _env_bool(ENV_AUTO_SUMMARIZE),
        description="If True, automatically summarize when context thresholds are hit "
        "without prompting. Default is False (prompts user). "
        f"Can be set via {ENV_AUTO_SUMMARIZE} env var.",
    )
