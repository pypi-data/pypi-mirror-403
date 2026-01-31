"""
Summarization prompt screen.

Shown when the context window reaches the threshold,
asking the user if they want to summarize the conversation.
"""

from dataclasses import dataclass
from enum import Enum, auto

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static


class SummarizationChoice(Enum):
    """User's choice for summarization."""

    SUMMARIZE_ONCE = auto()  # Summarize this time only
    ALWAYS_SUMMARIZE = auto()  # Summarize now and auto-approve for session
    SKIP = auto()  # Don't summarize


@dataclass
class SummarizationPromptResult:
    choice: SummarizationChoice

    @property
    def should_summarize(self) -> bool:
        return self.choice in (SummarizationChoice.SUMMARIZE_ONCE, SummarizationChoice.ALWAYS_SUMMARIZE)

    @property
    def auto_approve_session(self) -> bool:
        return self.choice == SummarizationChoice.ALWAYS_SUMMARIZE


class SummarizationPromptScreen(ModalScreen[SummarizationPromptResult]):
    """Modal screen prompting user about context summarization."""

    BINDINGS = [
        Binding("y", "summarize", "Summarize", show=True, priority=True),
        Binding("a", "always", "Always", show=True, priority=True),
        Binding("n", "continue", "Skip", show=True, priority=True),
        Binding("escape", "continue", "Skip", show=False, priority=True),
    ]

    DEFAULT_CSS = """
    SummarizationPromptScreen {
        align: center middle;
    }

    SummarizationPromptScreen > Vertical {
        width: 70;
        height: auto;
        background: #1e1e2e;
        border: thick #f59e0b;
        padding: 1 2;
    }

    SummarizationPromptScreen .header {
        text-align: center;
        color: #fbbf24;
        text-style: bold;
        padding-bottom: 1;
    }

    SummarizationPromptScreen .body {
        text-align: center;
        color: #e2e8f0;
        padding-bottom: 1;
    }

    SummarizationPromptScreen .details {
        text-align: center;
        color: #94a3b8;
        padding-bottom: 1;
    }

    SummarizationPromptScreen .action-hints {
        text-align: center;
        color: #94a3b8;
        padding-top: 1;
        border-top: solid #334155;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("⚠️  Context Window Growing Large", classes="header")
            yield Static(
                "The conversation is approaching context limits.",
                classes="body",
            )
            yield Static(
                "Summarizing creates a checkpoint—history is preserved in the UI\n"
                "but only the summary is sent to the LLM for efficiency.",
                classes="details",
            )
            yield Static(
                "[Y] Summarize    [A] Always (auto-summarize this session)    [N] Skip",
                classes="action-hints",
                markup=False,
            )

    def action_summarize(self) -> None:
        self.dismiss(SummarizationPromptResult(choice=SummarizationChoice.SUMMARIZE_ONCE))

    def action_always(self) -> None:
        self.dismiss(SummarizationPromptResult(choice=SummarizationChoice.ALWAYS_SUMMARIZE))

    def action_continue(self) -> None:
        self.dismiss(SummarizationPromptResult(choice=SummarizationChoice.SKIP))
