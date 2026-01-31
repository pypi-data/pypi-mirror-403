import json

from textual.app import ComposeResult
from textual.widgets import Collapsible, Static

from hypergolic.tui.widgets.tool_displays.base import BaseToolDisplay


class CommandLineDisplay(BaseToolDisplay):
    DEFAULT_CSS = """
    CommandLineDisplay .cmd-line {
        color: #22d3ee;
        padding: 0;
        height: auto;
    }

    CommandLineDisplay .cmd-line-full {
        color: #22d3ee;
        padding: 0 1;
        margin: 0;
        height: auto;
    }

    CommandLineDisplay .cmd-collapsible {
        padding: 0;
        margin: 0;
    }

    CommandLineDisplay .exit-code {
        color: #4ade80;
        padding: 0;
        height: auto;
    }

    CommandLineDisplay .exit-code-error {
        color: #f87171;
        padding: 0;
        height: auto;
    }
    """

    CMD_TRUNCATE_LENGTH = 80

    def _get_display_name(self) -> str:
        return "command_line"

    def compose_params(self) -> ComposeResult:
        cmd = self.tool_input.get("cmd", "")
        if len(cmd) > self.CMD_TRUNCATE_LENGTH:
            truncated = cmd[: self.CMD_TRUNCATE_LENGTH - 3] + "..."
            with Collapsible(
                title=f"$ {truncated}", collapsed=True, classes="cmd-collapsible"
            ):
                yield Static(f"$ {cmd}", classes="cmd-line-full", markup=False)
        else:
            yield Static(f"$ {cmd}", classes="cmd-line", markup=False)

    def compose_result(self) -> ComposeResult:
        if self.is_error:
            yield from self._yield_error(self.tool_output)
            return

        if self.interrupted:
            yield from self._yield_inline_result("[Interrupted by user]")
            return

        # Parse the JSON output to get returncode, stdout, stderr
        try:
            result = json.loads(self.tool_output)
            returncode = result.get("returncode", 0)
            stdout = result.get("stdout", "").strip()
            stderr = result.get("stderr", "").strip()
        except (json.JSONDecodeError, TypeError):
            # Fallback if output isn't JSON
            yield from self._yield_collapsible_output()
            return

        # Show exit code
        if returncode == 0:
            yield Static("Exit: 0", classes="exit-code")
        else:
            yield Static(f"Exit: {returncode}", classes="exit-code-error")

        # Combine stdout and stderr for display
        output_parts = []
        if stdout:
            output_parts.append(stdout)
        if stderr:
            output_parts.append(f"[stderr]\n{stderr}")
        combined = "\n".join(output_parts)

        if not combined:
            return

        # Short output inline, long output collapsible
        if len(combined) < 100 and "\n" not in combined:
            yield from self._yield_inline_result(combined)
        else:
            line_count = combined.count("\n") + 1
            yield from self._yield_collapsible_output(f"Show Output ({line_count} lines)")
