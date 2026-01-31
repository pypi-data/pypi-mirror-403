import re
import subprocess
from enum import Enum

from anthropic.types import ToolParam
from anthropic.types.tool_result_block_param import Content
from pydantic import BaseModel, Field

from hypergolic.session_context import SessionContext
from hypergolic.tools.enums import ToolName
from hypergolic.tools.schemas import CommandToolOutput


class GitOperation(str, Enum):
    ADD = "add"
    STATUS = "status"
    COMMIT = "commit"
    ADD_COMMIT = "add_commit"


class GitToolInput(BaseModel):
    operation: GitOperation = Field(
        description="The git operation to perform: 'add', 'status', 'commit', or 'add_commit'"
    )
    message: str | None = Field(
        default=None,
        description="Commit message (required for 'commit' and 'add_commit' operations, ignored for others)",
    )


def _sanitize_commit_message(message: str) -> str:
    return re.sub(r"[^a-zA-Z0-9 ]", "", message) or "commit"


def git_operation(
    params: GitToolInput, session_context: SessionContext
) -> list[Content]:
    match params.operation:
        case GitOperation.ADD:
            command = ["git", "add", "-A"]
        case GitOperation.STATUS:
            command = ["git", "status"]
        case GitOperation.COMMIT:
            if not params.message:
                return [
                    {
                        "type": "text",
                        "text": CommandToolOutput(
                            returncode=1,
                            stderr="Commit message is required for commit operation",
                            stdout="",
                        ).model_dump_json(),
                    }
                ]
            clean_message = _sanitize_commit_message(params.message)
            command = ["git", "commit", "-m", clean_message]
        case GitOperation.ADD_COMMIT:
            if not params.message:
                return [
                    {
                        "type": "text",
                        "text": CommandToolOutput(
                            returncode=1,
                            stderr="Commit message is required for add_commit operation",
                            stdout="",
                        ).model_dump_json(),
                    }
                ]
            add_output = subprocess.run(
                ["git", "add", "-A"],
                capture_output=True,
                text=True,
                cwd=session_context.worktree_root,
            )
            if add_output.returncode != 0:
                result = CommandToolOutput(
                    returncode=add_output.returncode,
                    stderr=add_output.stderr,
                    stdout=add_output.stdout,
                )
                return [{"type": "text", "text": result.model_dump_json()}]

            clean_message = _sanitize_commit_message(params.message)
            commit_output = subprocess.run(
                ["git", "commit", "-m", clean_message],
                capture_output=True,
                text=True,
                cwd=session_context.worktree_root,
            )
            if commit_output.returncode == 0:
                return [{"type": "text", "text": "Commit successful"}]
            result = CommandToolOutput(
                returncode=commit_output.returncode,
                stderr=commit_output.stderr,
                stdout=commit_output.stdout,
            )
            return [{"type": "text", "text": result.model_dump_json()}]

    output = subprocess.run(
        command, capture_output=True, text=True, cwd=session_context.worktree_root
    )
    if params.operation == GitOperation.COMMIT and output.returncode == 0:
        return [{"type": "text", "text": "Commit successful"}]
    result = CommandToolOutput(
        returncode=output.returncode,
        stderr=output.stderr,
        stdout=output.stdout,
    )
    return [{"type": "text", "text": result.model_dump_json()}]


GitTool: ToolParam = {
    "name": ToolName.GIT,
    "description": (
        "Perform git operations in the current repository. Supports 'add' (stages all changes), "
        "'status' (shows working tree status), 'commit' (commits staged changes with a message), "
        "and 'add_commit' (stages all changes and commits them in one operation). "
        "Use this instead of git commands via command_line for a smoother workflow. "
        "Pre-commit hooks will run on commit, providing feedback from linters, type checkers, and tests."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["add", "status", "commit", "add_commit"],
                "description": "The git operation to perform",
            },
            "message": {
                "type": "string",
                "description": "Commit message (required for 'commit' and 'add_commit' operations)",
            },
        },
        "required": ["operation"],
    },
}
