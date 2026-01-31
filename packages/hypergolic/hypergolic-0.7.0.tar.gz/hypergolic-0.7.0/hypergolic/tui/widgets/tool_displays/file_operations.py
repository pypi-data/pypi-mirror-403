from textual.app import ComposeResult
from textual.widgets import Static

from hypergolic.tui.widgets.tool_displays.base import BaseToolDisplay


class FileOperationsDisplay(BaseToolDisplay):
    def _get_display_name(self) -> str:
        return "file_operations"

    def compose_params(self) -> ComposeResult:
        parts = []

        if op := self.tool_input.get("operation"):
            parts.append(f"Operation: {op}")
        if target := self.tool_input.get("target"):
            parts.append(f"Target: {target}")
        if path := self.tool_input.get("path"):
            parts.append(f"Path: {path}")
        if new_path := self.tool_input.get("new_path"):
            parts.append(f"New Path: {new_path}")

        yield Static("; ".join(parts) if parts else "(no params)", classes="tool-params")

    def compose_result(self) -> ComposeResult:
        if self.is_error:
            yield from self._yield_error(self.tool_output)
            return

        if self.interrupted:
            yield from self._yield_inline_result("[Interrupted by user]")
            return

        output = self.tool_output.strip() if self.tool_output else ""

        # File operations usually have short success messages
        if output:
            yield from self._yield_inline_result(f"✓ {output}")
        else:
            yield from self._yield_inline_result("✓ Completed")
