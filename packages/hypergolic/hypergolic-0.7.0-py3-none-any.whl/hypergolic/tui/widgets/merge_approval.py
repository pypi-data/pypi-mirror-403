from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.widgets import Input, Static

from hypergolic.session_context import SessionContext
from hypergolic.tui.widgets.diff_view import FileDiffHeader, MergeDiffView
from hypergolic.tui.widgets.tools import DenialInput, ToolApprovalResult
from hypergolic.version_control import MergeDiffData, get_merge_diff


class MergeApprovalScreen(ModalScreen[ToolApprovalResult]):
    BINDINGS = [
        Binding("y", "approve", "Approve", show=True, priority=True),
        Binding("n", "deny", "Deny", show=True, priority=True),
        Binding("d", "deny_with_reason", "Deny with reason", show=True, priority=True),
        Binding("escape", "deny", "Deny", show=False, priority=True),
        Binding("e", "expand_all", "Expand all", show=True),
        Binding("c", "collapse_all", "Collapse all", show=True),
    ]

    DEFAULT_CSS = """
    MergeApprovalScreen {
        align: center middle;
    }

    MergeApprovalScreen > Vertical {
        width: 90%;
        max-width: 140;
        height: 85%;
        background: #1e1e2e;
        border: thick #22c55e;
    }

    MergeApprovalScreen .header {
        dock: top;
        height: 3;
        background: #14532d;
        padding: 1 2;
        color: #bbf7d0;
        text-style: bold;
    }

    MergeApprovalScreen .branch-info {
        height: 2;
        padding: 0 2;
        background: #1e293b;
        border-bottom: solid #334155;
        color: #e2e8f0;
    }

    MergeApprovalScreen .diff-container {
        height: 1fr;
    }

    MergeApprovalScreen .action-bar {
        dock: bottom;
        height: auto;
        padding: 1 2;
        background: #1e293b;
        border-top: solid #334155;
    }

    MergeApprovalScreen .action-hints {
        height: 1;
        text-align: center;
        color: #94a3b8;
    }

    MergeApprovalScreen .loading {
        height: 100%;
        content-align: center middle;
        color: #64748b;
    }

    MergeApprovalScreen .error {
        height: 100%;
        content-align: center middle;
        color: #f87171;
        padding: 2;
    }
    """

    def __init__(self, session_context: SessionContext, **kwargs):
        super().__init__(**kwargs)
        self.session_context = session_context
        self.diff_data: MergeDiffData | None = None
        self._denial_mode = False
        self._loading = True
        self._error: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical():
            # Header
            yield Static("🔀 MERGE APPROVAL", classes="header")

            # Branch info
            yield Static(
                self._render_branch_info(),
                classes="branch-info",
            )

            # Diff container (will be populated on mount)
            with Vertical(classes="diff-container", id="diff-container"):
                yield Static("Loading diff...", classes="loading", id="loading")

            # Denial input (hidden by default)
            yield DenialInput(id="denial-input")

            # Action bar
            with Vertical(classes="action-bar"):
                yield Static(
                    "[Y] Approve    [N] Deny    [D] Deny with reason    [E] Expand    [C] Collapse",
                    classes="action-hints",
                    markup=False,
                )

    def _render_branch_info(self) -> Text:
        text = Text()
        text.append("Merging: ", style="#94a3b8")
        text.append(self.session_context.agent_branch, style="bold #818cf8")
        text.append(" → ", style="#64748b")
        text.append(self.session_context.original_branch, style="bold #4ade80")
        return text

    async def on_mount(self) -> None:
        self.focus()
        self.run_worker(self._load_diff, exclusive=True, thread=True)

    def _load_diff(self) -> MergeDiffData | None:
        try:
            return get_merge_diff(self.session_context)
        except Exception as e:
            self._error = str(e)
            return None

    def on_worker_state_changed(self, event) -> None:
        """Handle worker completion."""
        if event.worker.name == "_load_diff" and event.state.name == "SUCCESS":
            self.diff_data = event.worker.result
            self._loading = False
            self._update_diff_view()
        elif event.worker.name == "_load_diff" and event.state.name == "ERROR":
            self._loading = False
            self._error = str(event.worker.error)
            self._update_diff_view()

    def _update_diff_view(self) -> None:
        """Update the diff view after loading."""
        container = self.query_one("#diff-container", Vertical)

        loading = self.query_one("#loading", Static)
        loading.remove()

        if self._error:
            container.mount(
                Static(f"Error loading diff: {self._error}", classes="error")
            )
            self.focus()
        else:
            diff_view = MergeDiffView(self.diff_data)
            container.mount(diff_view)
            if not self._focus_first_file_header():
                self.focus()

    def _focus_first_file_header(self) -> bool:
        try:
            first_header = self.query_one(FileDiffHeader)
            first_header.focus()
            return True
        except NoMatches:
            return False

    def action_approve(self) -> None:
        if self._denial_mode:
            return
        self.dismiss(ToolApprovalResult(approved=True))

    def action_deny(self) -> None:
        self.dismiss(ToolApprovalResult(approved=False, denial_message=None))

    def action_deny_with_reason(self) -> None:
        self._denial_mode = True
        denial_input = self.query_one("#denial-input", DenialInput)
        denial_input.add_class("visible")
        denial_input.query_one(Input).focus()

    def action_expand_all(self) -> None:
        try:
            diff_view = self.query_one(MergeDiffView)
            diff_view.expand_all()
        except NoMatches:
            pass

    def action_collapse_all(self) -> None:
        """Collapse all file diffs."""
        try:
            diff_view = self.query_one(MergeDiffView)
            diff_view.collapse_all()
        except NoMatches:
            pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter in the denial reason input."""
        if event.input.id == "denial-reason":
            reason = event.value.strip() or None
            self.dismiss(ToolApprovalResult(approved=False, denial_message=reason))
