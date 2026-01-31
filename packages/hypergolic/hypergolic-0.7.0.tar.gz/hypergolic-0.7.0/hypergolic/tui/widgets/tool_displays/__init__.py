from datetime import datetime
from typing import Any

from hypergolic.tools.enums import ToolName
from hypergolic.tui.widgets.token_usage import TokenUsage
from hypergolic.tui.widgets.tool_displays.base import BaseToolDisplay
from hypergolic.tui.widgets.tool_displays.browser import BrowserDisplay
from hypergolic.tui.widgets.tool_displays.code_review import CodeReviewDisplay
from hypergolic.tui.widgets.tool_displays.command_line import CommandLineDisplay
from hypergolic.tui.widgets.tool_displays.default import DefaultToolDisplay
from hypergolic.tui.widgets.tool_displays.file_explorer import FileExplorerDisplay
from hypergolic.tui.widgets.tool_displays.file_operations import FileOperationsDisplay
from hypergolic.tui.widgets.tool_displays.git import GitDisplay
from hypergolic.tui.widgets.tool_displays.merge_branch import MergeBranchDisplay
from hypergolic.tui.widgets.tool_displays.read_file import ReadFileDisplay
from hypergolic.tui.widgets.tool_displays.screenshot import ScreenshotDisplay
from hypergolic.tui.widgets.tool_displays.search_files import SearchFilesDisplay
from hypergolic.tui.widgets.tool_displays.window_management import (
    WindowManagementDisplay,
)

TOOL_DISPLAY_REGISTRY: dict[ToolName, type[BaseToolDisplay]] = {
    ToolName.BROWSER: BrowserDisplay,
    ToolName.CODE_REVIEW: CodeReviewDisplay,
    ToolName.COMMAND_LINE: CommandLineDisplay,
    ToolName.FILE_EXPLORER: FileExplorerDisplay,
    ToolName.READ_FILE: ReadFileDisplay,
    ToolName.SEARCH_FILES: SearchFilesDisplay,
    ToolName.FILE_OPERATIONS: FileOperationsDisplay,
    ToolName.GIT: GitDisplay,
    ToolName.SCREENSHOT: ScreenshotDisplay,
    ToolName.WINDOW_MANAGEMENT: WindowManagementDisplay,
    ToolName.MERGE_BRANCH: MergeBranchDisplay,
}


def create_tool_display(
    tool_name: str,
    tool_input: dict[str, Any],
    tool_output: str,
    timestamp: datetime | None = None,
    is_error: bool = False,
    interrupted: bool = False,
    token_usage: TokenUsage | None = None,
) -> BaseToolDisplay:
    try:
        tool_enum = ToolName(tool_name)
        display_cls = TOOL_DISPLAY_REGISTRY.get(tool_enum, DefaultToolDisplay)
    except ValueError:
        display_cls = DefaultToolDisplay

    return display_cls(
        tool_name=tool_name,
        tool_input=tool_input,
        tool_output=tool_output,
        timestamp=timestamp,
        is_error=is_error,
        interrupted=interrupted,
        token_usage=token_usage,
    )


__all__ = [
    "BaseToolDisplay",
    "create_tool_display",
    "TOOL_DISPLAY_REGISTRY",
    "BrowserDisplay",
    "CodeReviewDisplay",
    "CommandLineDisplay",
    "DefaultToolDisplay",
    "FileExplorerDisplay",
    "FileOperationsDisplay",
    "GitDisplay",
    "MergeBranchDisplay",
    "ReadFileDisplay",
    "ScreenshotDisplay",
    "SearchFilesDisplay",
    "WindowManagementDisplay",
]
