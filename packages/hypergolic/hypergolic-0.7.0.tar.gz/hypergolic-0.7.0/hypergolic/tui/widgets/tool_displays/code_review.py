from textual.app import ComposeResult
from textual.widgets import Static

from hypergolic.tui.widgets.tool_displays.base import BaseToolDisplay


class CodeReviewDisplay(BaseToolDisplay):
    def _get_display_name(self) -> str:
        return "code_review"

    def compose_params(self) -> ComposeResult:
        parts = []
        if base := self.tool_input.get("base_branch"):
            parts.append(f"Base: {base}")
        if feature := self.tool_input.get("feature_branch"):
            parts.append(f"Feature: {feature}")
        yield Static(
            "; ".join(parts) if parts else "Requesting review", classes="tool-params"
        )

    def compose_result(self) -> ComposeResult:
        if self.is_error:
            yield from self._yield_error(self.tool_output)
            return

        if self.interrupted:
            yield from self._yield_inline_result("[Interrupted by user]")
            return

        # Success case normally handled by CodeReviewSummary, but just in case:
        yield from self._yield_inline_result("✓ Review completed")
