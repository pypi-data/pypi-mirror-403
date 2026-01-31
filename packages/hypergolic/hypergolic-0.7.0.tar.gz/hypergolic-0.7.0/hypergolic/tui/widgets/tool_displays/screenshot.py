from textual.app import ComposeResult
from textual.widgets import Static

from hypergolic.tui.widgets.tool_displays.base import BaseToolDisplay


class ScreenshotDisplay(BaseToolDisplay):
    def _get_display_name(self) -> str:
        return "screenshot"

    def compose_params(self) -> ComposeResult:
        parts = []

        if target := self.tool_input.get("target"):
            parts.append(f"Target: {target}")
        if window_id := self.tool_input.get("window_id"):
            parts.append(f"Window ID: {window_id}")

        yield Static("; ".join(parts) if parts else "Target: fullscreen", classes="tool-params")

    def compose_result(self) -> ComposeResult:
        if self.is_error:
            yield from self._yield_error(self.tool_output)
            return

        if self.interrupted:
            yield from self._yield_inline_result("[Interrupted by user]")
            return

        # Screenshot output is typically just confirmation or base64 data
        # We don't want to show the base64 blob
        yield from self._yield_inline_result("✓ Screenshot captured")
