from textual.app import ComposeResult
from textual.widgets import Static

from hypergolic.tui.widgets.tool_displays.base import BaseToolDisplay


class DefaultToolDisplay(BaseToolDisplay):
    """Fallback display for tools without a custom implementation."""

    def compose_params(self) -> ComposeResult:
        if not self.tool_input:
            yield Static("(no parameters)", classes="tool-params")
            return

        parts = []
        for key, value in self.tool_input.items():
            parts.append(self._format_param(key, value))

        yield Static("; ".join(parts), classes="tool-params")

    def compose_result(self) -> ComposeResult:
        if self.is_error:
            yield from self._yield_error(self.tool_output)
            return

        if self.interrupted:
            yield from self._yield_inline_result("[Interrupted by user]")
            return

        output = self.tool_output.strip() if self.tool_output else ""

        if not output or output == "(no output)":
            yield from self._yield_inline_result("✓ Completed")
            return

        if len(output) < 100 and "\n" not in output:
            yield from self._yield_inline_result(output)
        else:
            yield from self._yield_collapsible_output()
