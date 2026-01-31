from textual.app import ComposeResult
from textual.widgets import Static

from hypergolic.tui.widgets.tool_displays.base import BaseToolDisplay


class ReadFileDisplay(BaseToolDisplay):
    def _get_display_name(self) -> str:
        return "read_file"

    def compose_params(self) -> ComposeResult:
        path = self.tool_input.get("path", "(no path)")
        yield Static(f"Path: {path}", classes="tool-params")

    def compose_result(self) -> ComposeResult:
        if self.is_error:
            yield from self._yield_error(self.tool_output)
            return

        if self.interrupted:
            yield from self._yield_inline_result("[Interrupted by user]")
            return

        output = self.tool_output.strip() if self.tool_output else ""
        if not output:
            yield from self._yield_inline_result("✓ Read (empty file)")
            return

        line_count = output.count("\n") + 1
        char_count = len(output)
        yield from self._yield_collapsible_output(
            f"Show Content ({line_count} lines, {char_count:,} chars)"
        )
