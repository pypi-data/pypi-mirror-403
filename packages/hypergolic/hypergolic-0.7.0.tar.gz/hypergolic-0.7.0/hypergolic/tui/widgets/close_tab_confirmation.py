from dataclasses import dataclass
from enum import Enum

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static


class CloseTabAction(Enum):
    CANCEL = "cancel"
    CLOSE_PRESERVE = "close_preserve"
    CLOSE_DELETE = "close_delete"


@dataclass
class CloseTabConfirmationResult:
    action: CloseTabAction


class CloseTabConfirmationScreen(ModalScreen[CloseTabConfirmationResult]):
    """Confirmation screen for closing a tab with unmerged changes."""

    BINDINGS = [
        Binding("y", "close_preserve", "Yes (preserve branch)", show=True, priority=True),
        Binding("n", "cancel", "No", show=True, priority=True),
        Binding("d", "close_delete", "Close & delete branch", show=True, priority=True),
        Binding("escape", "cancel", "Cancel", show=False, priority=True),
    ]

    DEFAULT_CSS = """
    CloseTabConfirmationScreen {
        align: center middle;
    }

    CloseTabConfirmationScreen > Vertical {
        width: 70;
        height: auto;
        background: #1e1e2e;
        border: thick #f59e0b;
        padding: 1 2;
    }

    CloseTabConfirmationScreen .header {
        text-align: center;
        color: #fbbf24;
        text-style: bold;
        padding-bottom: 1;
    }

    CloseTabConfirmationScreen .body {
        text-align: center;
        color: #e2e8f0;
        padding-bottom: 1;
    }

    CloseTabConfirmationScreen .branch-info {
        text-align: center;
        color: #94a3b8;
        padding-bottom: 1;
    }

    CloseTabConfirmationScreen .action-hints {
        text-align: center;
        color: #94a3b8;
        padding-top: 1;
        border-top: solid #334155;
    }

    CloseTabConfirmationScreen .warning {
        text-align: center;
        color: #f87171;
        padding-bottom: 1;
    }
    """

    def __init__(
        self,
        branch_name: str,
        has_uncommitted: bool = False,
        has_committed: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.branch_name = branch_name
        self.has_uncommitted = has_uncommitted
        self.has_committed = has_committed

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("⚠️  Unmerged Changes", classes="header")

            # Build description based on what kind of changes exist
            if self.has_uncommitted and self.has_committed:
                body_text = "This tab has uncommitted changes and unmerged commits."
            elif self.has_uncommitted:
                body_text = "This tab has uncommitted changes."
            else:
                body_text = "This tab has unmerged commits."

            yield Static(f"{body_text} Close anyway?", classes="body")
            yield Static(f"Branch: {self.branch_name}", classes="branch-info")

            if self.has_uncommitted:
                yield Static(
                    "⚠️  [D] will discard uncommitted changes!",
                    classes="warning",
                )

            yield Static(
                "[Y] Yes (preserve branch)    [N] No    [D] Close & delete branch",
                classes="action-hints",
                markup=False,
            )

    def action_close_preserve(self) -> None:
        self.dismiss(CloseTabConfirmationResult(action=CloseTabAction.CLOSE_PRESERVE))

    def action_close_delete(self) -> None:
        self.dismiss(CloseTabConfirmationResult(action=CloseTabAction.CLOSE_DELETE))

    def action_cancel(self) -> None:
        self.dismiss(CloseTabConfirmationResult(action=CloseTabAction.CANCEL))
