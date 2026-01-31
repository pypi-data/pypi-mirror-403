from enum import Enum
from pathlib import Path

from anthropic.types import ToolParam
from anthropic.types.tool_result_block_param import Content
from pydantic import BaseModel, Field

from hypergolic.session_context import SessionContext
from hypergolic.tools.enums import ToolName


class FileOperation(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    RENAME = "rename"
    DELETE = "delete"


class FileTarget(str, Enum):
    FILE = "file"
    DIRECTORY = "directory"


class FileChange(BaseModel):
    old: str = Field(description="Exact text to find in the file")
    new: str = Field(description="Text to replace it with")


class FileOperationsToolInput(BaseModel):
    operation: FileOperation = Field(
        description="The operation to perform: 'create', 'update', 'rename', or 'delete'"
    )
    target: FileTarget = Field(
        description="Whether operating on a 'file' or 'directory'"
    )
    path: str = Field(
        description="Path to the file or directory (relative to git root or absolute)"
    )
    content: str | None = Field(
        default=None,
        description="Full file content (for 'create' only)",
    )
    changes: list[FileChange] | None = Field(
        default=None,
        description="List of search/replace changes (for 'update' only). Each change has 'old' (text to find) and 'new' (replacement text).",
    )
    new_path: str | None = Field(
        default=None,
        description="New path for 'rename' operation",
    )


def validate_path_in_worktree(path: Path, worktree_root: Path) -> Path:
    resolved = path.resolve()
    worktree_root_resolved = worktree_root.resolve()

    try:
        resolved.relative_to(worktree_root_resolved)
        return resolved
    except ValueError as err:
        raise ValueError(f"Path '{path}' is outside the worktree") from err


def resolve_path(path_str: str, git_root: Path) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = git_root / path
    return path


def make_error(message: str) -> list[Content]:
    return [{"type": "text", "text": f"Error: {message}"}]


def make_success(message: str) -> list[Content]:
    return [{"type": "text", "text": message}]


def truncate_for_error(text: str, max_len: int = 50) -> str:
    if len(text) <= max_len:
        return repr(text)
    return f"{text[:max_len]!r}..."


def apply_changes(content: str, changes: list[FileChange]) -> tuple[str, list[str]]:
    # Validate all changes against original content first (fail-fast)
    errors: list[str] = []
    for i, change in enumerate(changes):
        if change.old not in content:
            errors.append(
                f"Change {i + 1}: text not found: {truncate_for_error(change.old)}"
            )
            continue
        count = content.count(change.old)
        if count > 1:
            errors.append(
                f"Change {i + 1}: text appears {count} times, must be unique: {truncate_for_error(change.old)}"
            )

    if errors:
        return content, errors

    # Apply all changes
    for change in changes:
        content = content.replace(change.old, change.new, 1)
    return content, []


def file_operations(
    params: FileOperationsToolInput, session_context: SessionContext
) -> list[Content]:
    worktree_root = session_context.worktree_root

    try:
        target_path = resolve_path(params.path, worktree_root)
        target_path = validate_path_in_worktree(target_path, worktree_root)
    except ValueError as e:
        return make_error(str(e))

    new_target_path: Path | None = None
    if params.operation == FileOperation.RENAME:
        if not params.new_path:
            return make_error("'new_path' is required for rename operation")
        try:
            new_target_path = resolve_path(params.new_path, worktree_root)
            new_target_path = validate_path_in_worktree(new_target_path, worktree_root)
        except ValueError as e:
            return make_error(str(e))

    match params.target:
        case FileTarget.FILE:
            return handle_file_operation(
                params.operation,
                target_path,
                params.content,
                params.changes,
                new_target_path,
            )
        case FileTarget.DIRECTORY:
            return handle_directory_operation(
                params.operation, target_path, new_target_path
            )


def handle_file_operation(
    operation: FileOperation,
    path: Path,
    content: str | None,
    changes: list[FileChange] | None,
    new_path: Path | None,
) -> list[Content]:
    match operation:
        case FileOperation.CREATE:
            if content is None:
                return make_error("'content' is required when creating a file")
            if path.exists():
                return make_error(f"File already exists: {path}")
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            except OSError as e:
                return make_error(f"Failed to create file: {e}")
            return make_success(f"Created file: {path} ({len(content)} bytes)")

        case FileOperation.UPDATE:
            if not changes:
                return make_error("'changes' list is required when updating a file")
            if not path.exists():
                return make_error(f"File does not exist: {path}")
            if not path.is_file():
                return make_error(f"Path is not a file: {path}")
            try:
                original = path.read_text()
                updated, errors = apply_changes(original, changes)
                if errors:
                    return make_error("Failed to apply changes:\n" + "\n".join(errors))
                path.write_text(updated)
            except OSError as e:
                return make_error(f"Failed to update file: {e}")
            return make_success(
                f"Updated file: {path} ({len(changes)} change(s) applied)"
            )

        case FileOperation.RENAME:
            if new_path is None:
                return make_error("'new_path' is required for rename operation")
            if not path.exists():
                return make_error(f"File does not exist: {path}")
            if not path.is_file():
                return make_error(f"Path is not a file: {path}")
            if new_path.exists():
                return make_error(f"Destination already exists: {new_path}")
            try:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                path.rename(new_path)
            except OSError as e:
                return make_error(f"Failed to rename file: {e}")
            return make_success(f"Renamed file: {path} -> {new_path}")

        case FileOperation.DELETE:
            if not path.exists():
                return make_error(f"File does not exist: {path}")
            if not path.is_file():
                return make_error(f"Path is not a file: {path}")
            try:
                path.unlink()
            except OSError as e:
                return make_error(f"Failed to delete file: {e}")
            return make_success(f"Deleted file: {path}")


def handle_directory_operation(
    operation: FileOperation,
    path: Path,
    new_path: Path | None,
) -> list[Content]:
    match operation:
        case FileOperation.CREATE:
            if path.exists():
                return make_error(f"Directory already exists: {path}")
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                return make_error(f"Failed to create directory: {e}")
            return make_success(f"Created directory: {path}")

        case FileOperation.UPDATE:
            return make_error("'update' operation is not valid for directories")

        case FileOperation.RENAME:
            if new_path is None:
                return make_error("'new_path' is required for rename operation")
            if not path.exists():
                return make_error(f"Directory does not exist: {path}")
            if not path.is_dir():
                return make_error(f"Path is not a directory: {path}")
            if new_path.exists():
                return make_error(f"Destination already exists: {new_path}")
            try:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                path.rename(new_path)
            except OSError as e:
                return make_error(f"Failed to rename directory: {e}")
            return make_success(f"Renamed directory: {path} -> {new_path}")

        case FileOperation.DELETE:
            if not path.exists():
                return make_error(f"Directory does not exist: {path}")
            if not path.is_dir():
                return make_error(f"Path is not a directory: {path}")
            try:
                path.rmdir()
            except OSError as e:
                return make_error(f"Failed to delete directory: {e}")
            return make_success(f"Deleted directory: {path}")


FileOperationsTool: ToolParam = {
    "name": ToolName.FILE_OPERATIONS,
    "description": (
        "Perform file system operations within the git repository. Supports creating, updating, "
        "renaming, and deleting files and directories. All paths must be within the repository "
        "for safety. Use 'create' to make new files/directories, 'update' to modify existing files "
        "with surgical search/replace changes, 'rename' to move files/directories, and 'delete' to remove them."
        "When changing a file, the 'changes' list is required"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["create", "update", "rename", "delete"],
                "description": "The operation to perform",
            },
            "target": {
                "type": "string",
                "enum": ["file", "directory"],
                "description": "Whether operating on a file or directory",
            },
            "path": {
                "type": "string",
                "description": "Path to the file or directory (relative to git root or absolute)",
            },
            "content": {
                "type": "string",
                "description": "File content (required for 'create' on files)",
            },
            "changes": {
                "type": "array",
                "description": "List of changes to apply (required for 'update'). Each change finds exact text and replaces it.",
                "items": {
                    "type": "object",
                    "properties": {
                        "old": {
                            "type": "string",
                            "description": "Exact text to find (must appear exactly once in file)",
                        },
                        "new": {
                            "type": "string",
                            "description": "Text to replace it with",
                        },
                    },
                    "required": ["old", "new"],
                },
            },
            "new_path": {
                "type": "string",
                "description": "Destination path for 'rename' operation",
            },
        },
        "required": ["operation", "target", "path"],
    },
}
