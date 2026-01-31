"""LSP tool for code intelligence via Language Server Protocol.

Provides efficient codebase navigation without reading entire files.
Supports:
- Python via ty (Astral's type checker)
- TypeScript/JavaScript via typescript-language-server
"""

import atexit
import json
import logging
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from anthropic.types import ToolParam
from anthropic.types.tool_result_block_param import Content
from pydantic import BaseModel

from hypergolic.tools.enums import ToolName

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx"}

# Map file extensions to LSP language IDs and server types
LANGUAGE_INFO: dict[str, tuple[str, str]] = {
    ".py": ("python", "python"),
    ".ts": ("typescript", "typescript"),
    ".tsx": ("typescriptreact", "typescript"),
    ".js": ("javascript", "typescript"),
    ".jsx": ("javascriptreact", "typescript"),
}


def _get_language_info(path: Path) -> tuple[str, str]:
    """Get (languageId, serverType) for a file."""
    return LANGUAGE_INFO.get(path.suffix, ("unknown", "unknown"))


@dataclass
class LSPServer:
    """Manages a single LSP server process."""

    process: subprocess.Popen[bytes]
    request_id: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def next_id(self) -> int:
        with self._lock:
            self.request_id += 1
            return self.request_id

    def send_request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = self.next_id()
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
        return self._send(request, request_id=request_id)

    def send_notification(self, method: str, params: dict[str, Any]) -> None:
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        self._send(notification, expect_response=False)

    def _send(
        self,
        message: dict[str, Any],
        expect_response: bool = True,
        request_id: int | None = None,
    ) -> dict[str, Any]:
        content = json.dumps(message)
        packet = f"Content-Length: {len(content)}\r\n\r\n{content}"

        assert self.process.stdin is not None
        assert self.process.stdout is not None

        self.process.stdin.write(packet.encode())
        self.process.stdin.flush()

        if not expect_response:
            return {}

        return self._read_response(request_id=request_id)

    def _read_response(self, request_id: int | None = None) -> dict[str, Any]:
        assert self.process.stdout is not None

        # Keep reading until we get the response matching our request ID
        # (skip any notifications the server pushes)
        while True:
            headers: dict[str, str] = {}
            while True:
                line = self.process.stdout.readline().decode()
                if line == "\r\n":
                    break
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip()] = value.strip()

            content_length = int(headers.get("Content-Length", 0))
            content = self.process.stdout.read(content_length).decode()
            response = json.loads(content)

            # If we're waiting for a specific request ID, skip notifications
            if request_id is not None:
                if response.get("id") == request_id:
                    return response
                # This is a notification (no id) or different request, continue
                continue

            return response

    def shutdown(self) -> None:
        try:
            self.send_request("shutdown", {})
            self.send_notification("exit", {})
        except Exception:
            pass
        finally:
            self.process.terminate()
            self.process.wait(timeout=5)


class LSPServerManager:
    """Manages LSP server lifecycle per workspace and language."""

    # Key is (workspace_root, server_type) e.g. ("/path/to/project", "python")
    _servers: dict[tuple[str, str], LSPServer] = {}
    _initialized_files: dict[tuple[str, str], set[str]] = {}
    _lock = threading.Lock()

    @classmethod
    def get_server(cls, workspace_root: Path, server_type: str) -> LSPServer:
        key = (str(workspace_root), server_type)
        with cls._lock:
            if key not in cls._servers:
                cls._servers[key] = cls._start_server(workspace_root, server_type)
                cls._initialized_files[key] = set()
            return cls._servers[key]

    @classmethod
    def _find_ty_executable(cls, workspace_root: Path) -> str:
        """Find ty executable, preferring virtualenv version."""
        # Check for ty in workspace's virtualenv
        venv_ty = workspace_root / ".venv" / "bin" / "ty"
        if venv_ty.exists():
            return str(venv_ty)

        # Fall back to system ty
        return "ty"

    @classmethod
    def _find_tsserver_executable(cls, workspace_root: Path) -> str:
        """Find typescript-language-server executable."""
        # Check for local node_modules install
        local_ts = workspace_root / "node_modules" / ".bin" / "typescript-language-server"
        if local_ts.exists():
            return str(local_ts)

        # Fall back to global install
        return "typescript-language-server"

    @classmethod
    def _start_server(cls, workspace_root: Path, server_type: str) -> LSPServer:
        if server_type == "python":
            return cls._start_python_server(workspace_root)
        elif server_type == "typescript":
            return cls._start_typescript_server(workspace_root)
        else:
            raise ValueError(f"Unknown server type: {server_type}")

    @classmethod
    def _start_python_server(cls, workspace_root: Path) -> LSPServer:
        ty_executable = cls._find_ty_executable(workspace_root)
        try:
            process = subprocess.Popen(
                [ty_executable, "server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=workspace_root,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "ty not found. Install with: uv tool install ty"
            ) from None

        server = LSPServer(process=process)

        # Initialize
        server.send_request(
            "initialize",
            {
                "processId": None,
                "rootUri": workspace_root.as_uri(),
                "capabilities": {},
            },
        )
        server.send_notification("initialized", {})

        return server

    @classmethod
    def _start_typescript_server(cls, workspace_root: Path) -> LSPServer:
        tsserver_executable = cls._find_tsserver_executable(workspace_root)
        try:
            process = subprocess.Popen(
                [tsserver_executable, "--stdio"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=workspace_root,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "typescript-language-server not found. Install with: "
                "npm install -g typescript-language-server typescript"
            ) from None

        server = LSPServer(process=process)

        # Initialize with capabilities needed for TypeScript
        server.send_request(
            "initialize",
            {
                "processId": None,
                "rootUri": workspace_root.as_uri(),
                "capabilities": {
                    "textDocument": {
                        "hover": {"contentFormat": ["markdown", "plaintext"]},
                        "definition": {"linkSupport": True},
                        "references": {},
                        "documentSymbol": {
                            "hierarchicalDocumentSymbolSupport": True,
                        },
                        "publishDiagnostics": {"relatedInformation": True},
                    },
                },
                "initializationOptions": {},
            },
        )
        server.send_notification("initialized", {})

        return server

    @classmethod
    def ensure_file_open(
        cls, server: LSPServer, workspace_root: Path, file_path: Path, server_type: str
    ) -> str:
        key = (str(workspace_root), server_type)
        uri = file_path.as_uri()

        with cls._lock:
            if uri not in cls._initialized_files.get(key, set()):
                content = file_path.read_text()
                language_id, _ = _get_language_info(file_path)
                server.send_notification(
                    "textDocument/didOpen",
                    {
                        "textDocument": {
                            "uri": uri,
                            "languageId": language_id,
                            "version": 1,
                            "text": content,
                        }
                    },
                )
                cls._initialized_files.setdefault(key, set()).add(uri)

        return uri

    @classmethod
    def shutdown_all(cls) -> None:
        with cls._lock:
            for server in cls._servers.values():
                server.shutdown()
            cls._servers.clear()
            cls._initialized_files.clear()


# Register cleanup on application exit
atexit.register(LSPServerManager.shutdown_all)


def _get_workspace_root(file_path: Path) -> Path:
    """Find git root or use file's parent directory."""
    current = file_path.parent
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return file_path.parent


def _resolve_path(file_path: str) -> Path:
    """Resolve file path to absolute path."""
    path = Path(file_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def _check_supported(file_path: Path) -> str | None:
    """Return error message if file type not supported, None otherwise."""
    if file_path.suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        return f"Unsupported file type: {file_path.suffix}. Supported: {supported}"
    return None


def _format_location(uri: str, line: int, col: int) -> str:
    """Format a location as file:line:col."""
    path = uri.replace("file://", "")
    return f"{path}:{line}:{col}"


def _format_hover_result(result: dict[str, Any] | None) -> str:
    """Format hover response into readable text."""
    if not result:
        return "No information available at this position."

    contents = result.get("contents", {})
    if isinstance(contents, str):
        return contents
    if isinstance(contents, dict):
        return contents.get("value", str(contents))
    if isinstance(contents, list):
        parts = []
        for item in contents:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get("value", str(item)))
        return "\n\n".join(parts)
    return str(contents)


def _format_locations(result: list[dict[str, Any]] | dict[str, Any] | None) -> str:
    """Format definition/references locations."""
    if not result:
        return "No locations found."

    locations = result if isinstance(result, list) else [result]
    formatted = []
    for loc in locations:
        uri = loc.get("uri", "")
        start = loc.get("range", {}).get("start", {})
        line = start.get("line", 0) + 1  # Convert 0-indexed to 1-indexed
        col = start.get("character", 0) + 1
        formatted.append(_format_location(uri, line, col))

    return "\n".join(formatted)


def _format_symbols(result: list[dict[str, Any]] | None) -> str:
    """Format document symbols into readable outline."""
    if not result:
        return "No symbols found."

    lines = []
    _format_symbol_tree(result, lines, indent=0)
    return "\n".join(lines)


def _format_symbol_tree(
    symbols: list[dict[str, Any]], lines: list[str], indent: int
) -> None:
    """Recursively format symbol tree."""
    symbol_kinds = {
        1: "File",
        2: "Module",
        3: "Namespace",
        4: "Package",
        5: "Class",
        6: "Method",
        7: "Property",
        8: "Field",
        9: "Constructor",
        10: "Enum",
        11: "Interface",
        12: "Function",
        13: "Variable",
        14: "Constant",
        15: "String",
        16: "Number",
        17: "Boolean",
        18: "Array",
    }

    for sym in symbols:
        kind_num = sym.get("kind", 0)
        kind = symbol_kinds.get(kind_num, f"Unknown({kind_num})")
        name = sym.get("name", "?")
        detail = sym.get("detail", "")

        prefix = "  " * indent
        detail_str = f" - {detail}" if detail else ""
        lines.append(f"{prefix}{kind}: {name}{detail_str}")

        children = sym.get("children", [])
        if children:
            _format_symbol_tree(children, lines, indent + 1)


def _format_diagnostics(result: list[dict[str, Any]] | None) -> str:
    """Format diagnostics into readable text."""
    if not result:
        return "No diagnostics."

    lines = []
    severity_map = {1: "Error", 2: "Warning", 3: "Info", 4: "Hint"}

    for diag in result:
        severity = severity_map.get(diag.get("severity", 1), "Unknown")
        message = diag.get("message", "")
        start = diag.get("range", {}).get("start", {})
        line = start.get("line", 0) + 1
        col = start.get("character", 0) + 1
        lines.append(f"{line}:{col} [{severity}] {message}")

    return "\n".join(lines) if lines else "No diagnostics."


# --- Individual operation handlers ---


def _op_hover(file: str, line: int, column: int) -> str:
    path = _resolve_path(file)
    if err := _check_supported(path):
        return err
    if not path.exists():
        return f"File not found: {path}"

    _, server_type = _get_language_info(path)
    workspace = _get_workspace_root(path)
    server = LSPServerManager.get_server(workspace, server_type)
    uri = LSPServerManager.ensure_file_open(server, workspace, path, server_type)

    result = server.send_request(
        "textDocument/hover",
        {
            "textDocument": {"uri": uri},
            "position": {"line": line - 1, "character": column - 1},
        },
    )
    return _format_hover_result(result.get("result"))


def _op_definition(file: str, line: int, column: int) -> str:
    path = _resolve_path(file)
    if err := _check_supported(path):
        return err
    if not path.exists():
        return f"File not found: {path}"

    _, server_type = _get_language_info(path)
    workspace = _get_workspace_root(path)
    server = LSPServerManager.get_server(workspace, server_type)
    uri = LSPServerManager.ensure_file_open(server, workspace, path, server_type)

    result = server.send_request(
        "textDocument/definition",
        {
            "textDocument": {"uri": uri},
            "position": {"line": line - 1, "character": column - 1},
        },
    )
    return _format_locations(result.get("result"))


def _op_references(file: str, line: int, column: int) -> str:
    path = _resolve_path(file)
    if err := _check_supported(path):
        return err
    if not path.exists():
        return f"File not found: {path}"

    _, server_type = _get_language_info(path)
    workspace = _get_workspace_root(path)
    server = LSPServerManager.get_server(workspace, server_type)
    uri = LSPServerManager.ensure_file_open(server, workspace, path, server_type)

    result = server.send_request(
        "textDocument/references",
        {
            "textDocument": {"uri": uri},
            "position": {"line": line - 1, "character": column - 1},
            "context": {"includeDeclaration": True},
        },
    )
    return _format_locations(result.get("result"))


def _op_symbols(file: str) -> str:
    path = _resolve_path(file)
    if err := _check_supported(path):
        return err
    if not path.exists():
        return f"File not found: {path}"

    _, server_type = _get_language_info(path)
    workspace = _get_workspace_root(path)
    server = LSPServerManager.get_server(workspace, server_type)
    uri = LSPServerManager.ensure_file_open(server, workspace, path, server_type)

    result = server.send_request(
        "textDocument/documentSymbol",
        {"textDocument": {"uri": uri}},
    )
    return _format_symbols(result.get("result"))


def _op_diagnostics(file: str) -> str:
    path = _resolve_path(file)
    if err := _check_supported(path):
        return err
    if not path.exists():
        return f"File not found: {path}"

    _, server_type = _get_language_info(path)
    workspace = _get_workspace_root(path)
    server = LSPServerManager.get_server(workspace, server_type)
    uri = LSPServerManager.ensure_file_open(server, workspace, path, server_type)

    if server_type == "python":
        # ty uses pull diagnostics
        result = server.send_request(
            "textDocument/diagnostic",
            {"textDocument": {"uri": uri}},
        )
        items = result.get("result", {}).get("items", [])
        return _format_diagnostics(items)
    else:
        # TypeScript server uses push diagnostics, but we can request them
        # by making a dummy request that triggers diagnostic calculation
        # For now, return a helpful message
        # TODO: Implement push diagnostics tracking for tsserver
        return "Diagnostics for TypeScript files coming soon. Use 'symbols' or 'hover' for now."


# --- Tool schema and input model ---


class LSPOperation(BaseModel):
    """A single LSP operation."""

    operation: Literal["hover", "definition", "references", "symbols", "diagnostics"]
    file: str
    line: int | None = None
    column: int | None = None


class LSPToolInput(BaseModel):
    """Input for the LSP tool - supports batch operations."""

    operations: list[LSPOperation]


LSPTool: ToolParam = {
    "name": ToolName.LSP,
    "description": """Code intelligence via Language Server Protocol.

Supported languages:
- Python (.py) via ty
- TypeScript/JavaScript (.ts, .tsx, .js, .jsx) via typescript-language-server

Operations:
- hover: Get type signature and documentation at position (requires file, line, column)
- definition: Jump to symbol definition (requires file, line, column)
- references: Find all references to a symbol (requires file, line, column)
- symbols: List all symbols in a file outline (requires file only)
- diagnostics: Get type errors and warnings for a file (requires file only, Python only for now)

Line and column numbers are 1-indexed. Multiple operations can be batched in a single call.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "operations": {
                "type": "array",
                "description": "List of LSP operations to perform",
                "items": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": [
                                "hover",
                                "definition",
                                "references",
                                "symbols",
                                "diagnostics",
                            ],
                            "description": "The LSP operation to perform",
                        },
                        "file": {
                            "type": "string",
                            "description": "Path to the file",
                        },
                        "line": {
                            "type": "integer",
                            "description": "Line number (1-indexed, required for hover/definition/references)",
                        },
                        "column": {
                            "type": "integer",
                            "description": "Column number (1-indexed, required for hover/definition/references)",
                        },
                    },
                    "required": ["operation", "file"],
                },
            },
        },
        "required": ["operations"],
    },
}


def lsp_operation(params: LSPToolInput) -> list[Content]:
    """Execute LSP operations and return results."""
    results: list[str] = []

    for op in params.operations:
        try:
            match op.operation:
                case "hover":
                    if op.line is None or op.column is None:
                        result = "Error: hover requires line and column"
                    else:
                        result = _op_hover(op.file, op.line, op.column)
                case "definition":
                    if op.line is None or op.column is None:
                        result = "Error: definition requires line and column"
                    else:
                        result = _op_definition(op.file, op.line, op.column)
                case "references":
                    if op.line is None or op.column is None:
                        result = "Error: references requires line and column"
                    else:
                        result = _op_references(op.file, op.line, op.column)
                case "symbols":
                    result = _op_symbols(op.file)
                case "diagnostics":
                    result = _op_diagnostics(op.file)
                case _:
                    result = f"Unknown operation: {op.operation}"

            header = f"=== {op.operation} {op.file}"
            if op.line is not None:
                header += f":{op.line}"
                if op.column is not None:
                    header += f":{op.column}"
            header += " ==="
            results.append(f"{header}\n{result}")

        except Exception as e:
            logger.exception("LSP operation failed: %s", op)
            results.append(f"=== {op.operation} {op.file} ===\nError: {e}")

    return [{"type": "text", "text": "\n\n".join(results)}]
