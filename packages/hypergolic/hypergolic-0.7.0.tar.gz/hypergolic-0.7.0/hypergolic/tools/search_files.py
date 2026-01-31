import shutil
import subprocess

from anthropic.types import ToolParam
from anthropic.types.tool_result_block_param import Content
from pydantic import BaseModel

from hypergolic.tools.enums import ToolName

SearchFilesTool: ToolParam = {
    "name": ToolName.SEARCH_FILES,
    "description": "Search for patterns within files. Uses ripgrep if available, falls back to grep. Respects .gitignore by default when using ripgrep.",
    "input_schema": {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "The pattern to search for",
            },
            "path": {
                "type": "string",
                "description": "Directory to search in (default: current directory)",
            },
            "include_glob": {
                "type": "string",
                "description": "Only search files matching this glob pattern (e.g., '*.py', '*.ts')",
            },
            "exclude_glob": {
                "type": "string",
                "description": "Exclude files matching this glob pattern (e.g., '*.min.js')",
            },
            "case_sensitive": {
                "type": "boolean",
                "description": "Whether the search is case-sensitive (default: true)",
            },
            "regex": {
                "type": "boolean",
                "description": "Treat pattern as a regular expression (default: false, uses literal matching)",
            },
            "context_lines": {
                "type": "integer",
                "description": "Number of context lines to show around each match (default: 0)",
            },
        },
        "required": ["pattern"],
    },
}


class SearchFilesToolInput(BaseModel):
    pattern: str
    path: str = "."
    include_glob: str | None = None
    exclude_glob: str | None = None
    case_sensitive: bool = True
    regex: bool = False
    context_lines: int = 0


def search_files(params: SearchFilesToolInput) -> list[Content]:
    use_ripgrep = shutil.which("rg") is not None

    if use_ripgrep:
        cmd = _build_ripgrep_command(params)
    else:
        cmd = _build_grep_command(params)

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Exit code 1 with no stderr means "no matches" for grep/rg
    if result.returncode == 1 and not result.stderr:
        return [{"type": "text", "text": "No matches found."}]

    if result.returncode != 0:
        error_msg = result.stderr.strip() or f"Search failed (exit code {result.returncode})"
        return [{"type": "text", "text": f"Error: {error_msg}"}]

    return [{"type": "text", "text": result.stdout}]


def _build_ripgrep_command(params: SearchFilesToolInput) -> list[str]:
    cmd = ["rg", "--line-number", "--with-filename"]

    if not params.case_sensitive:
        cmd.append("--ignore-case")
    if not params.regex:
        cmd.append("--fixed-strings")
    if params.include_glob:
        cmd.extend(["--glob", params.include_glob])
    if params.exclude_glob:
        cmd.extend(["--glob", f"!{params.exclude_glob}"])
    if params.context_lines > 0:
        cmd.extend(["--context", str(params.context_lines)])

    cmd.append(params.pattern)
    cmd.append(params.path)

    return cmd


def _build_grep_command(params: SearchFilesToolInput) -> list[str]:
    cmd = ["grep", "-rnH"]

    if not params.case_sensitive:
        cmd.append("-i")
    if not params.regex:
        cmd.append("-F")
    if params.context_lines > 0:
        cmd.extend(["-C", str(params.context_lines)])
    if params.include_glob:
        cmd.extend(["--include", params.include_glob])
    if params.exclude_glob:
        cmd.extend(["--exclude", params.exclude_glob])

    cmd.append(params.pattern)
    cmd.append(params.path)

    return cmd
