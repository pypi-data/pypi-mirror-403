from textual.app import ComposeResult
from textual.widgets import Static

from hypergolic.tui.widgets.tool_displays.base import BaseToolDisplay


class SearchFilesDisplay(BaseToolDisplay):
    def _get_display_name(self) -> str:
        return "search_files"

    def compose_params(self) -> ComposeResult:
        parts = []

        if pattern := self.tool_input.get("pattern"):
            parts.append(f'Pattern: "{pattern}"')
        if path := self.tool_input.get("path"):
            parts.append(f"Path: {path}")
        if glob := self.tool_input.get("include_glob"):
            parts.append(f"Glob: {glob}")

        yield Static("; ".join(parts) if parts else "(no pattern)", classes="tool-params")

    def compose_result(self) -> ComposeResult:
        if self.is_error:
            yield from self._yield_error(self.tool_output)
            return

        if self.interrupted:
            yield from self._yield_inline_result("[Interrupted by user]")
            return

        output = self.tool_output.strip() if self.tool_output else ""

        if not output:
            yield from self._yield_inline_result("No matches found")
            return

        # Count matches (lines in output)
        match_count = output.count("\n") + 1 if output else 0
        yield from self._yield_collapsible_output(f"Show Matches ({match_count} lines)")
