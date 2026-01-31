from textual.app import ComposeResult
from textual.widgets import Static

from hypergolic.tui.widgets.tool_displays.base import BaseToolDisplay


class MergeBranchDisplay(BaseToolDisplay):
    def _get_display_name(self) -> str:
        return "merge_branch"

    def compose_params(self) -> ComposeResult:
        # merge_branch takes no parameters
        yield Static("Merging agent branch into original branch", classes="tool-params")

    def compose_result(self) -> ComposeResult:
        if self.is_error:
            yield from self._yield_error(self.tool_output)
            return

        if self.interrupted:
            yield from self._yield_inline_result("[Interrupted by user]")
            return

        output = self.tool_output.strip() if self.tool_output else ""

        if output:
            # Show merge result inline if short
            if len(output) < 100 and "\n" not in output:
                yield from self._yield_inline_result(f"✓ {output}")
            else:
                yield from self._yield_collapsible_output("Show Details")
        else:
            yield from self._yield_inline_result("✓ Merged successfully")
