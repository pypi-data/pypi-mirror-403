from textual.app import ComposeResult
from textual.widgets import Static

from hypergolic.tui.widgets.tool_displays.base import BaseToolDisplay


class GitDisplay(BaseToolDisplay):
    def _get_display_name(self) -> str:
        return "git"

    def compose_params(self) -> ComposeResult:
        parts = []

        if op := self.tool_input.get("operation"):
            parts.append(f"Operation: {op}")
        if msg := self.tool_input.get("message"):
            display_msg = msg if len(msg) <= 50 else msg[:47] + "..."
            parts.append(f'Message: "{display_msg}"')

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

        # For simple operations, show inline result
        if op in ("add", "commit", "add_commit"):
            # Check for success indicators
            if "committed" in output.lower() or op == "add":
                first_line = output.split("\n")[0] if output else ""
                if len(first_line) < 80:
                    yield from self._yield_inline_result(f"✓ {first_line}")
                else:
                    yield from self._yield_collapsible_output("Show Output")
            else:
                # Might be hook failure or other issue
                yield from self._yield_collapsible_output("Show Output", collapsed=False)
        elif op == "status":
            line_count = output.count("\n") + 1
            yield from self._yield_collapsible_output(f"Show Status ({line_count} lines)")
        else:
            yield from self._yield_collapsible_output()
