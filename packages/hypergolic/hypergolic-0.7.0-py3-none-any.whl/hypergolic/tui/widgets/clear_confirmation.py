from dataclasses import dataclass
from enum import Enum

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static


class ClearAction(Enum):
    CANCEL = "cancel"
    CLEAR = "clear"  # Full wipe - destroys message history
    SUMMARIZE = "summarize"  # Creates checkpoint, preserves history


@dataclass
class ClearConfirmationResult:
    action: ClearAction


class ClearConfirmationScreen(ModalScreen[ClearConfirmationResult]):
    BINDINGS = [
        Binding("s", "summarize", "Summarize", show=True, priority=True),
        Binding("c", "clear", "Clear All", show=True, priority=True),
        Binding("n", "cancel", "Cancel", show=True, priority=True),
        Binding("escape", "cancel", "Cancel", show=False, priority=True),
    ]

    DEFAULT_CSS = """
    ClearConfirmationScreen {
        align: center middle;
    }

    ClearConfirmationScreen > Vertical {
        width: 65;
        height: auto;
        background: #1e1e2e;
        border: thick #6366f1;
        padding: 1 2;
    }

    ClearConfirmationScreen .header {
        text-align: center;
        color: #a5b4fc;
        text-style: bold;
        padding-bottom: 1;
    }

    ClearConfirmationScreen .body {
        text-align: center;
        color: #e2e8f0;
        padding-bottom: 1;
    }

    ClearConfirmationScreen .details {
        text-align: left;
        color: #94a3b8;
        padding: 0 2 1 2;
    }

    ClearConfirmationScreen .action-hints {
        text-align: center;
        color: #94a3b8;
        padding-top: 1;
        border-top: solid #334155;
    }
    """

    def __init__(self, has_messages: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.has_messages = has_messages

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("🗑️  Clear Conversation", classes="header")
            yield Static(
                "How would you like to handle the conversation?",
                classes="body",
            )
            if self.has_messages:
                yield Static(
                    "• Summarize: Creates a checkpoint, history preserved\n"
                    "• Clear All: Wipes session, loses message history",
                    classes="details",
                )
                yield Static(
                    "[S] Summarize    [C] Clear All    [N] Cancel",
                    classes="action-hints",
                    markup=False,
                )
            else:
                yield Static(
                    "[C] Clear    [N] Cancel",
                    classes="action-hints",
                    markup=False,
                )

    def action_clear(self) -> None:
        self.dismiss(ClearConfirmationResult(action=ClearAction.CLEAR))

    def action_summarize(self) -> None:
        if self.has_messages:
            self.dismiss(ClearConfirmationResult(action=ClearAction.SUMMARIZE))
        else:
            self.dismiss(ClearConfirmationResult(action=ClearAction.CLEAR))

    def action_cancel(self) -> None:
        self.dismiss(ClearConfirmationResult(action=ClearAction.CANCEL))
