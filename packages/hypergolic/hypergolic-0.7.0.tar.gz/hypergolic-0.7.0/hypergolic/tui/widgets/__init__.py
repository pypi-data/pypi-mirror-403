"""CLI widgets for the Hypergolic TUI."""

from hypergolic.tui.widgets.diff_view import MergeDiffView
from hypergolic.tui.widgets.file_browser import FileBrowser, FileBrowserFileSelected
from hypergolic.tui.widgets.merge_approval import MergeApprovalScreen
from hypergolic.tui.widgets.tool_approval import (
    DenialInput,
    ParameterBox,
    ParameterDetailScreen,
    ToolApprovalResult,
    ToolApprovalScreen,
)
from hypergolic.tui.widgets.tool_displays import create_tool_display
from hypergolic.tui.widgets.tool_status import (
    ToolDeniedStatus,
    ToolExecutingStatus,
)

__all__ = [
    # File browser
    "FileBrowser",
    "FileBrowserFileSelected",
    # Diff/merge
    "MergeDiffView",
    "MergeApprovalScreen",
    # Tool approval
    "ToolApprovalResult",
    "ToolApprovalScreen",
    "ParameterDetailScreen",
    "ParameterBox",
    "DenialInput",
    # Tool status
    "ToolExecutingStatus",
    "ToolDeniedStatus",
    "create_tool_display",
]
