from textual.app import ComposeResult
from textual.widgets import Static

from hypergolic.tui.widgets.tool_displays.base import BaseToolDisplay


class FileExplorerDisplay(BaseToolDisplay):
    def _get_display_name(self) -> str:
        return "file_explorer"

    def compose_params(self) -> ComposeResult:
        parts = []

        if path := self.tool_input.get("path"):
            parts.append(f"Path: {path}")
        if style := self.tool_input.get("style"):
            parts.append(f"Style: {style}")
        if depth := self.tool_input.get("depth"):
            parts.append(f"Depth: {depth}")

        yield Static("; ".join(parts) if parts else "(no path)", classes="tool-params")

    def compose_result(self) -> ComposeResult:
        if self.is_error:
            yield from self._yield_error(self.tool_output)
            return

        if self.interrupted:
            yield from self._yield_inline_result("[Interrupted by user]")
            return

        output = self.tool_output.strip() if self.tool_output else ""
        if not output:
            yield from self._yield_inline_result("✓ Completed (empty)")
            return

        line_count = output.count("\n") + 1
        yield from self._yield_collapsible_output(f"Show Output ({line_count} lines)")
