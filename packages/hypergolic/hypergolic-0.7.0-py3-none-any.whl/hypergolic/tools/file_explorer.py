from typing import Literal

from anthropic.types import ToolParam
from anthropic.types.tool_result_block_param import Content
from pydantic import BaseModel

from hypergolic.exploration import ExplorationResult, explore_directory
from hypergolic.tools.enums import ToolName

FileExplorerTool: ToolParam = {
    "name": ToolName.FILE_EXPLORER,
    "description": (
        "Explore directory contents. Supports two styles: "
        "'flat' for simple ls-style listing of immediate contents, or "
        "'tree' for recursive hierarchical view (default). Ideal for quickly understanding project structure"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path to the directory to explore",
            },
            "style": {
                "type": "string",
                "enum": ["flat", "tree"],
                "description": (
                    "Exploration style: 'flat' for ls-style listing of immediate contents, "
                    "'tree' for recursive hierarchical view showing nested structure. "
                    "Defaults to 'tree' for comprehensive exploration."
                ),
            },
            "depth": {
                "type": "integer",
                "description": (
                    "Maximum recursion depth for tree style (default: 3). "
                    "Use 1-2 for large projects, 3-4 for smaller ones. "
                    "Ignored for flat style."
                ),
            },
            "respect_gitignore": {
                "type": "boolean",
                "description": (
                    "Whether to exclude files matching .gitignore patterns (default: true). "
                    "Only applies to tree style."
                ),
            },
        },
        "required": ["path"],
    },
}


class FileExplorerToolInput(BaseModel):
    path: str
    style: Literal["flat", "tree"] = "tree"
    depth: int = 3
    respect_gitignore: bool = True


def file_explorer(params: FileExplorerToolInput) -> list[Content]:
    result: ExplorationResult = explore_directory(
        path=params.path.strip(),
        depth=params.depth,
        style=params.style,
        respect_gitignore=params.respect_gitignore,
    )

    if result.error:
        return [{"type": "text", "text": f"Error: {result.error}"}]

    output_parts = [result.output]

    if params.style == "tree":
        metadata = []
        if result.truncated:
            metadata.append(f"[Output truncated - showing {result.file_count} items]")
        if result.depth_used != params.depth:
            metadata.append(
                f"[Depth auto-reduced from {params.depth} to {result.depth_used} due to size]"
            )

        if metadata:
            output_parts.append("\n" + "\n".join(metadata))

    return [{"type": "text", "text": "\n".join(output_parts)}]
