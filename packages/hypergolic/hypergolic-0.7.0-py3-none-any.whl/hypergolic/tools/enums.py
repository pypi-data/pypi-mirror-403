from enum import Enum


class ToolName(str, Enum):
    BROWSER = "browser"
    CODE_REVIEW = "code_review"
    COMMAND_LINE = "command_line"
    FILE_EXPLORER = "file_explorer"
    FILE_OPERATIONS = "file_operations"
    GIT = "git"
    LSP = "lsp"
    MERGE_BRANCH = "merge_branch"
    READ_FILE = "read_file"
    SCREENSHOT = "screenshot"
    SEARCH_FILES = "search_files"
    WINDOW_MANAGEMENT = "window_management"
