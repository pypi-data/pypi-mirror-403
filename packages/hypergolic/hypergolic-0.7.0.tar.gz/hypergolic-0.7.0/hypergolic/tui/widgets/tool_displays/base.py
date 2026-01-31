import json
from abc import abstractmethod
from datetime import datetime
from typing import Any

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Collapsible, Static

from hypergolic.tui.widgets.token_usage import TokenUsage


class BaseToolDisplay(Vertical):
    DEFAULT_CSS = """
    BaseToolDisplay {
        background: #1a2332;
        border: solid #4ade80;
        padding: 0 1;
        margin: 1 0;
        height: auto;
    }

    BaseToolDisplay.error {
        border: solid #f87171;
    }

    BaseToolDisplay.interrupted {
        border: solid #fbbf24;
    }

    BaseToolDisplay .tool-header {
        color: #4ade80;
        text-style: bold;
        height: 1;
        padding: 0;
    }

    BaseToolDisplay.error .tool-header {
        color: #f87171;
    }

    BaseToolDisplay.interrupted .tool-header {
        color: #fbbf24;
    }

    BaseToolDisplay .tool-params {
        color: #94a3b8;
        padding: 0;
        height: auto;
    }

    BaseToolDisplay .tool-result-inline {
        color: #e2e8f0;
        padding: 0;
        height: auto;
    }

    BaseToolDisplay .tool-error {
        color: #f87171;
        padding: 0;
        height: auto;
    }

    BaseToolDisplay Collapsible {
        padding: 0;
        margin: 0;
    }

    BaseToolDisplay .tool-output {
        color: #e2e8f0;
        padding: 0 1;
        margin: 0;
        max-height: 15;
        overflow-y: auto;
    }
    """

    def __init__(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: str,
        timestamp: datetime | None = None,
        is_error: bool = False,
        interrupted: bool = False,
        token_usage: TokenUsage | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.tool_input = tool_input
        self.tool_output = tool_output
        self.timestamp = timestamp or datetime.now()
        self.is_error = is_error
        self.interrupted = interrupted
        self.token_usage = token_usage

    def compose(self) -> ComposeResult:
        if self.is_error:
            self.add_class("error")
        if self.interrupted:
            self.add_class("interrupted")

        yield self._compose_header()
        yield from self.compose_params()
        yield from self.compose_result()

    def _compose_header(self) -> Static:
        time_str = self.timestamp.strftime("%I:%M:%S %p")
        icon = self._get_icon()
        display_name = self._get_display_name()

        usage_str = ""
        if self.token_usage:
            formatted = self.token_usage.format_header()
            if formatted:
                usage_str = f" │ {formatted}"

        return Static(
            f"{icon} Tool: [bold]{escape(display_name)}[/bold] │ {time_str}{usage_str}",
            classes="tool-header",
        )

    def _get_icon(self) -> str:
        if self.is_error:
            return "❌"
        if self.interrupted:
            return "⚠️"
        return "✓"

    def _get_display_name(self) -> str:
        return self.tool_name

    @abstractmethod
    def compose_params(self) -> ComposeResult:
        """Render the input parameters in a tool-specific way."""
        ...

    @abstractmethod
    def compose_result(self) -> ComposeResult:
        """Render the result/output in a tool-specific way."""
        ...

    def _yield_collapsible_output(
        self, title: str = "Show Output", collapsed: bool = True
    ) -> ComposeResult:
        output = self.tool_output.strip() if self.tool_output else "(no output)"
        with Collapsible(title=title, collapsed=collapsed):
            yield Static(output, classes="tool-output", markup=False)

    def _yield_inline_result(self, text: str) -> ComposeResult:
        yield Static(text, classes="tool-result-inline", markup=False)

    def _yield_error(self, text: str) -> ComposeResult:
        yield Static(f"Error: {text}", classes="tool-error", markup=False)

    def _format_param(self, key: str, value: Any, max_len: int = 60) -> str:
        if isinstance(value, str):
            display = value if len(value) <= max_len else value[: max_len - 3] + "..."
        elif isinstance(value, dict | list):
            display = json.dumps(value)
            if len(display) > max_len:
                display = display[: max_len - 3] + "..."
        else:
            display = str(value)
        return f"{key}: {display}"
