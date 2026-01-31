from anthropic.types import ToolUnionParam

from hypergolic.tools.browser import BrowserTool
from hypergolic.tools.code_review.schemas import CodeReviewTool
from hypergolic.tools.command_line import CommandLineTool
from hypergolic.tools.file_explorer import FileExplorerTool
from hypergolic.tools.file_operations import FileOperationsTool
from hypergolic.tools.git import GitTool
from hypergolic.tools.lsp import LSPTool
from hypergolic.tools.merge_branch import MergeBranchTool
from hypergolic.tools.read_file import ReadFileTool
from hypergolic.tools.screenshot import ScreenshotTool
from hypergolic.tools.search_files import SearchFilesTool
from hypergolic.tools.window_management import WindowManagementTool

BUILTIN_TOOLS: list[ToolUnionParam] = [
    BrowserTool,
    CodeReviewTool,
    CommandLineTool,
    FileExplorerTool,
    FileOperationsTool,
    GitTool,
    LSPTool,
    MergeBranchTool,
    ReadFileTool,
    ScreenshotTool,
    SearchFilesTool,
    WindowManagementTool,
]


def get_tools() -> list[ToolUnionParam]:
    """Get the list of tools available for the session."""
    return list(BUILTIN_TOOLS)


CODE_REVIEW_TOOLS: list[ToolUnionParam] = [
    FileExplorerTool,
    ReadFileTool,
    SearchFilesTool,
]
