import json
from dataclasses import dataclass
from typing import Any

from anthropic.types import ToolUseBlock
from rich.markup import escape
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Input, Static


@dataclass
class ToolApprovalResult:
    approved: bool
    denial_message: str | None = None
    allow_session: bool = False  # If True, auto-approve this command for the session
    allow_forever: bool = False  # If True, persist approval to ~/.hypergolic/tool_approvals.json


class ParameterDetailScreen(ModalScreen[None]):
    BINDINGS = [
        Binding("escape", "dismiss", "Back", show=True),
    ]

    DEFAULT_CSS = """
    ParameterDetailScreen {
        align: center middle;
    }

    ParameterDetailScreen > Vertical {
        width: 90%;
        height: 90%;
        background: #1e1e2e;
        border: solid #6366f1;
    }

    ParameterDetailScreen .header {
        dock: top;
        height: 3;
        background: #1e293b;
        border-bottom: solid #334155;
        padding: 1 2;
    }

    ParameterDetailScreen .header-title {
        width: 1fr;
        color: #818cf8;
        text-style: bold;
    }

    ParameterDetailScreen .header-hint {
        width: auto;
        color: #64748b;
    }

    ParameterDetailScreen .content {
        padding: 1 2;
        color: #e2e8f0;
    }
    """

    def __init__(self, tool_name: str, params: dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.params = params

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(classes="header"):
                yield Static(
                    f"📋 Parameters — {escape(self.tool_name)}", classes="header-title"
                )
                yield Static("[Esc] Back", classes="header-hint", markup=False)
            with VerticalScroll():
                formatted = (
                    json.dumps(self.params, indent=2)
                    if self.params
                    else "(no parameters)"
                )
                yield Static(formatted, classes="content", markup=False)

    async def action_dismiss(self, result: None = None) -> None:
        self.dismiss(None)


class ParameterBox(Vertical, can_focus=True):
    BINDINGS = [
        Binding("space", "expand", "Expand", show=False),
    ]

    DEFAULT_CSS = """
    ParameterBox {
        height: auto;
        min-height: 5;
        max-height: 16;
        border: solid #475569;
        background: #0f172a;
        padding: 1;
        margin: 1 0;
    }

    ParameterBox:focus {
        border: solid #6366f1;
    }

    ParameterBox:hover {
        border: solid #818cf8;
    }

    ParameterBox .param-content {
        color: #e2e8f0;
    }

    ParameterBox .expand-hint {
        dock: bottom;
        text-align: right;
        color: #64748b;
        padding-top: 1;
    }
    """

    def __init__(self, tool_name: str, params: dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.params = params

    def compose(self) -> ComposeResult:
        if self.params:
            formatted = json.dumps(self.params, indent=2)
            lines = formatted.split("\n")
            if len(lines) > 10:
                preview = "\n".join(lines[:10]) + "\n..."
            else:
                preview = formatted
        else:
            preview = "(no parameters)"

        yield Static(preview, classes="param-content", markup=False)
        yield Static("Space or click to expand", classes="expand-hint")

    def action_expand(self) -> None:
        self.app.push_screen(ParameterDetailScreen(self.tool_name, self.params))

    def on_click(self) -> None:
        self.action_expand()


class DenialInput(Horizontal):
    DEFAULT_CSS = """
    DenialInput {
        height: auto;
        padding: 1 0;
        display: none;
    }

    DenialInput.visible {
        display: block;
    }

    DenialInput .label {
        width: auto;
        color: #94a3b8;
        padding-right: 1;
    }

    DenialInput Input {
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("Reason:", classes="label")
        yield Input(placeholder="Optional denial reason...", id="denial-reason")


class ToolApprovalScreen(ModalScreen[ToolApprovalResult]):
    """Keybindings: Y/Enter to approve, S for session, F for forever, N/Esc to deny, D to deny with reason."""

    BINDINGS = [
        Binding("y", "approve", "Approve", show=True, priority=True),
        Binding("enter", "approve", "Approve", show=False, priority=True),
        Binding("s", "allow_session", "Allow (session)", show=True, priority=True),
        Binding("f", "allow_forever", "Allow (forever)", show=True, priority=True),
        Binding("n", "deny", "Deny", show=True, priority=True),
        Binding("d", "deny_with_reason", "Deny with reason", show=True, priority=True),
        Binding("escape", "deny", "Deny", show=False, priority=True),
    ]

    DEFAULT_CSS = """
    ToolApprovalScreen {
        align: center middle;
    }

    ToolApprovalScreen > Vertical {
        width: 80%;
        max-width: 100;
        height: auto;
        max-height: 80%;
        background: #1e1e2e;
        border: thick #f59e0b;
    }

    ToolApprovalScreen .header {
        dock: top;
        height: 3;
        background: #78350f;
        padding: 1 2;
        color: #fef3c7;
        text-style: bold;
    }

    ToolApprovalScreen .body {
        padding: 1 2;
        height: auto;
    }

    ToolApprovalScreen .section-label {
        color: #94a3b8;
        padding: 0 0 1 0;
        text-style: bold;
    }

    ToolApprovalScreen .action-bar {
        dock: bottom;
        height: auto;
        padding: 1 2;
        background: #1e293b;
        border-top: solid #334155;
    }

    ToolApprovalScreen .action-hints {
        height: 1;
        text-align: center;
        color: #94a3b8;
    }

    ToolApprovalScreen .key {
        color: #fbbf24;
        text-style: bold;
    }
    """

    def __init__(self, tool_use: ToolUseBlock, **kwargs):
        super().__init__(**kwargs)
        self.tool_use = tool_use
        self._denial_mode = False

    def compose(self) -> ComposeResult:
        params = self.tool_use.input if isinstance(self.tool_use.input, dict) else {}

        with Vertical():
            yield Static(
                f"⚠️  APPROVAL REQUIRED — {escape(self.tool_use.name)}", classes="header"
            )
            with Vertical(classes="body"):
                yield Static("Parameters", classes="section-label")
                yield ParameterBox(self.tool_use.name, params, id="param-box")
                yield DenialInput(id="denial-input")
            with Vertical(classes="action-bar"):
                yield Static(
                    "[Y] Approve  [S] Session  [F] Forever  [N] Deny  [D] Deny with reason",
                    classes="action-hints",
                    markup=False,
                )

    def on_mount(self) -> None:
        self.query_one("#param-box", ParameterBox).focus()

    def action_approve(self) -> None:
        if self._denial_mode:
            # Submit the denial input when Enter is pressed in denial mode
            denial_input = self.query_one("#denial-input", DenialInput)
            input_widget = denial_input.query_one(Input)
            reason = input_widget.value.strip() or None
            self.dismiss(ToolApprovalResult(approved=False, denial_message=reason))
            return
        self.dismiss(ToolApprovalResult(approved=True))

    def action_allow_session(self) -> None:
        """Approve and remember this command for the session."""
        self.dismiss(ToolApprovalResult(approved=True, allow_session=True))

    def action_allow_forever(self) -> None:
        """Approve and persist this command to ~/.hypergolic/tool_approvals.json."""
        self.dismiss(ToolApprovalResult(approved=True, allow_forever=True))

    def action_deny(self) -> None:
        self.dismiss(ToolApprovalResult(approved=False, denial_message=None))

    def action_deny_with_reason(self) -> None:
        self._denial_mode = True
        denial_input = self.query_one("#denial-input", DenialInput)
        denial_input.add_class("visible")
        denial_input.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "denial-reason":
            reason = event.value.strip() or None
            self.dismiss(ToolApprovalResult(approved=False, denial_message=reason))
