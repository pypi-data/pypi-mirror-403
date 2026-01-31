from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from hypergolic.session_context import SessionContext


class BranchDisplay(Static):
    def __init__(self, session_context: SessionContext, **kwargs):
        super().__init__(**kwargs)
        self.session_context = session_context

    def render(self) -> str:
        ctx = self.session_context
        return f"📁 {ctx.project_name} │ 🌿 {ctx.original_branch} → {ctx.agent_branch}"


class HypergolicHeader(Static):
    DEFAULT_CSS = """
    HypergolicHeader {
        dock: top;
        height: 2;
        background: #0f172a;
        color: #e2e8f0;
        padding: 0 1;
        border-bottom: solid #334155;
    }

    HypergolicHeader Horizontal {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    HypergolicHeader .title {
        width: auto;
        text-style: bold;
        color: #f97316;
    }

    HypergolicHeader .context {
        width: 1fr;
        text-align: center;
        color: #94a3b8;
    }
    """

    def __init__(self, session_context: SessionContext, **kwargs):
        super().__init__(**kwargs)
        self.session_context = session_context

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Static("🔥 Hypergolic", classes="title")
            yield BranchDisplay(self.session_context, classes="context")
