from textual.app import ComposeResult
from textual.widgets import Static

from hypergolic.tui.widgets.tool_displays.base import BaseToolDisplay


class WindowManagementDisplay(BaseToolDisplay):
    def _get_display_name(self) -> str:
        return "window_management"

    def compose_params(self) -> ComposeResult:
        parts = []

        if op := self.tool_input.get("operation"):
            parts.append(f"Operation: {op}")
        if app := self.tool_input.get("app_name"):
            parts.append(f"App: {app}")
        if window_id := self.tool_input.get("window_id"):
            parts.append(f"Window ID: {window_id}")

        yield Static("; ".join(parts) if parts else "(no operation)", classes="tool-params")

    def compose_result(self) -> ComposeResult:
        if self.is_error:
            yield from self._yield_error(self.tool_output)
            return

        if self.interrupted:
            yield from self._yield_inline_result("[Interrupted by user]")
            return

        output = self.tool_output.strip() if self.tool_output else ""
        op = self.tool_input.get("operation", "")

        if not output:
            yield from self._yield_inline_result("✓ Completed")
            return

        if op == "list":
            # Count windows from output
            lines = output.split("\n")
            # First line usually says "Found X window(s):"
            if lines and "window" in lines[0].lower():
                yield from self._yield_inline_result(lines[0])
                if len(lines) > 1:
                    yield from self._yield_collapsible_output("Show Windows")
            else:
                yield from self._yield_collapsible_output("Show Windows")
        elif op == "focus":
            yield from self._yield_inline_result(f"✓ {output}")
        elif op == "get_info":
            yield from self._yield_collapsible_output("Show Info")
        else:
            yield from self._yield_collapsible_output()
