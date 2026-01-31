"""Session info sidebar widget."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Static

from hypergolic.session_context import SessionContext


class SidebarSection(Static):
    """A section header in the sidebar."""

    DEFAULT_CSS = """
    SidebarSection {
        color: #94a3b8;
        text-style: bold;
        padding: 1 0 0 0;
        border-bottom: solid #334155;
    }
    """


class SidebarItem(Static):
    """A key-value item in the sidebar."""

    DEFAULT_CSS = """
    SidebarItem {
        padding: 0 1;
        height: auto;
    }

    SidebarItem .label {
        color: #64748b;
    }

    SidebarItem .value {
        color: #e2e8f0;
    }
    """

    def __init__(self, label: str, value: str = "", **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self._value = value

    def render(self) -> str:
        return f"[#64748b]{self.label}:[/#64748b] {self._value}"

    def update_value(self, value: str) -> None:
        """Update the displayed value."""
        self._value = value
        self.refresh()


class SessionSidebar(Vertical):
    """Sidebar showing session context and statistics."""

    # Sidebar width - truncation lengths below are derived from this
    SIDEBAR_WIDTH = 28

    DEFAULT_CSS = """
    SessionSidebar {
        dock: right;
        width: 28;
        background: #0f172a;
        border-left: solid #334155;
        padding: 0 1;
    }

    SessionSidebar.hidden {
        display: none;
    }

    SessionSidebar .sidebar-title {
        text-style: bold;
        color: #818cf8;
        text-align: center;
        padding: 1 0;
        border-bottom: double #4f46e5;
    }
    """

    # Reactive token counts
    context_tokens = reactive(0)
    output_tokens = reactive(0)
    cache_read_tokens = reactive(0)
    cache_creation_tokens = reactive(0)
    cost_usd = reactive(0.0)
    message_count = reactive(0)
    tool_count = reactive(0)
    summarization_count = reactive(0)

    def __init__(self, session_context: SessionContext, **kwargs):
        super().__init__(**kwargs)
        self.session_context = session_context

    def compose(self) -> ComposeResult:
        yield Static("📊 Session Info", classes="sidebar-title")

        # Context section
        yield SidebarSection("Context")
        yield SidebarItem("Project", self.session_context.project_name, id="project")
        yield SidebarItem(
            "Base", self.session_context.original_branch, id="base-branch"
        )
        yield SidebarItem(
            "Agent",
            self._truncate_branch(self.session_context.agent_branch),
            id="agent-branch",
        )

        # Tokens section
        yield SidebarSection("Tokens")
        yield SidebarItem("Context", "0", id="context-tokens")
        yield SidebarItem("Output", "0", id="output-tokens")
        yield SidebarItem("Cache Read", "0", id="cache-read")
        yield SidebarItem("Cache Write", "0", id="cache-write")

        # Cost section
        yield SidebarSection("Cost")
        yield SidebarItem("Session", "$0.00", id="session-cost")
        yield SidebarItem("Cache Rate", "-", id="cache-hit-rate")

        # Stats section
        yield SidebarSection("Statistics")
        yield SidebarItem("Messages", "0", id="message-count")
        yield SidebarItem("Tool Calls", "0", id="tool-count")
        yield SidebarItem("Summaries", "0", id="summarization-count")

    def _truncate_branch(self, branch: str, max_len: int = 20) -> str:
        """Truncate branch name to fit sidebar.

        Default max_len is derived from SIDEBAR_WIDTH minus padding/label space.
        """
        if len(branch) <= max_len:
            return branch
        # Keep prefix and suffix
        return branch[:8] + "..." + branch[-9:]

    def _truncate_path(self, path: str, max_len: int = 22) -> str:
        """Truncate path to fit sidebar, keeping the end.

        Default max_len is derived from SIDEBAR_WIDTH minus padding/label space.
        """
        if len(path) <= max_len:
            return path
        return "..." + path[-(max_len - 3) :]

    def watch_context_tokens(self, value: int) -> None:
        """Update context window usage display."""
        self._update_item("context-tokens", f"{value:,}")
        self._update_cache_efficiency()

    def watch_output_tokens(self, value: int) -> None:
        """Update output tokens display."""
        self._update_item("output-tokens", f"{value:,}")

    def watch_cache_read_tokens(self, value: int) -> None:
        """Update cache read tokens display."""
        self._update_item("cache-read", f"{value:,}")
        self._update_cache_efficiency()

    def watch_cache_creation_tokens(self, value: int) -> None:
        """Update cache creation tokens display."""
        self._update_item("cache-write", f"{value:,}")
        self._update_cache_efficiency()

    def watch_cost_usd(self, value: float) -> None:
        """Update session cost display."""
        self._update_item("session-cost", f"${value:.2f}")

    def watch_message_count(self, value: int) -> None:
        """Update message count display."""
        self._update_item("message-count", str(value))

    def watch_tool_count(self, value: int) -> None:
        """Update tool count display."""
        self._update_item("tool-count", str(value))

    def watch_summarization_count(self, value: int) -> None:
        """Update summarization count display."""
        self._update_item("summarization-count", str(value))

    def _update_cache_efficiency(self) -> None:
        """Update cache efficiency metrics.

        Cache Hit Rate: What percentage of cacheable input tokens were served from cache.
        Formula: cache_read / (cache_read + cache_creation)
        """
        cache_read = self.cache_read_tokens
        cache_write = self.cache_creation_tokens

        # Calculate hit rate: cache_read / total_cacheable_tokens
        total_cacheable = cache_read + cache_write
        if total_cacheable > 0:
            hit_rate = cache_read / total_cacheable
            self._update_item("cache-hit-rate", f"{hit_rate:.0%}")
        else:
            self._update_item("cache-hit-rate", "-")

    def _update_item(self, item_id: str, value: str) -> None:
        """Update a sidebar item by ID."""
        try:
            item = self.query_one(f"#{item_id}", SidebarItem)
            item.update_value(value)
        except NoMatches:
            pass  # Widget might not be mounted yet

    def toggle(self) -> None:
        """Toggle sidebar visibility."""
        self.toggle_class("hidden")
