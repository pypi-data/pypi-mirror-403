import subprocess

from anthropic.types import ToolParam
from anthropic.types.tool_result_block_param import Content
from pydantic import BaseModel

from hypergolic.tools.enums import ToolName

ReadFileTool: ToolParam = {
    "name": ToolName.READ_FILE,
    "description": "Read the contents of one or more files",
    "input_schema": {
        "type": "object",
        "properties": {
            "paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of file paths to read",
            },
        },
        "required": ["paths"],
    },
}


class ReadFileToolInput(BaseModel):
    paths: list[str]


def read_file(params: ReadFileToolInput) -> list[Content]:
    if len(params.paths) == 1:
        return _read_single_file(params.paths[0])
    return _read_multiple_files(params.paths)


def _read_single_file(path: str) -> list[Content]:
    result = subprocess.run(["cat", path.strip()], capture_output=True, text=True)

    if result.returncode != 0:
        error_msg = result.stderr.strip() or f"Failed to read file (exit code {result.returncode})"
        return [{"type": "text", "text": f"Error: {error_msg}"}]

    return [{"type": "text", "text": result.stdout}]


def _read_multiple_files(paths: list[str]) -> list[Content]:
    results: list[str] = []

    for path in paths:
        path = path.strip()
        result = subprocess.run(["cat", path], capture_output=True, text=True)

        if result.returncode != 0:
            error_msg = result.stderr.strip() or f"Failed to read file (exit code {result.returncode})"
            results.append(f"=== {path} ===\nError: {error_msg}")
        else:
            results.append(f"=== {path} ===\n{result.stdout}")

    return [{"type": "text", "text": "\n\n".join(results)}]
