from textual.app import ComposeResult
from textual.widgets import Static

from hypergolic.tui.widgets.tool_displays.base import BaseToolDisplay


class BrowserDisplay(BaseToolDisplay):
    DEFAULT_CSS = """
    BrowserDisplay .browser-op {
        color: #a78bfa;
        padding: 0;
        height: auto;
    }

    BrowserDisplay .browser-target {
        color: #22d3ee;
        padding: 0;
        height: auto;
    }
    """

    def _get_display_name(self) -> str:
        return "browser"

    def compose_params(self) -> ComposeResult:
        operation = self.tool_input.get("operation", "unknown")
        yield Static(f"🌐 {operation}", classes="browser-op")

        # Show relevant details based on operation
        url = self.tool_input.get("url")
        selector = self.tool_input.get("selector")
        text = self.tool_input.get("text")

        if url:
            display_url = url if len(url) <= 60 else url[:57] + "..."
            yield Static(f"→ {display_url}", classes="browser-target", markup=False)
        elif selector:
            display_selector = selector if len(selector) <= 60 else selector[:57] + "..."
            yield Static(f"→ {display_selector}", classes="browser-target", markup=False)
            if text:
                display_text = text if len(text) <= 40 else text[:37] + "..."
                yield Static(f'  "{display_text}"', classes="browser-target", markup=False)

    def compose_result(self) -> ComposeResult:
        if self.is_error:
            yield from self._yield_error(self.tool_output)
            return

        if self.interrupted:
            yield from self._yield_inline_result("[Interrupted by user]")
            return

        # Check if this is a screenshot (no text output)
        if not self.tool_output or self.tool_output == "(image)":
            yield from self._yield_inline_result("📸 Screenshot captured")
            return

        # Short output inline, long output collapsible
        if len(self.tool_output) < 100 and "\n" not in self.tool_output:
            yield from self._yield_inline_result(self.tool_output)
        else:
            line_count = self.tool_output.count("\n") + 1
            yield from self._yield_collapsible_output(f"Show Output ({line_count} lines)")
