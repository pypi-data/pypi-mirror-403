"""
TUI-specific observer for updating the sidebar with session stats.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from hypergolic.session_stats import StatsObserver

if TYPE_CHECKING:
    from hypergolic.tui.widgets.sidebar import SessionSidebar


class SidebarStatsObserver(StatsObserver):
    """
    Updates the TUI sidebar when stats change.

    This observer bridges SessionStats to the Textual sidebar widget,
    keeping stats logic decoupled from the main TUI class.
    """

    def __init__(self, query_sidebar: Callable[[], SessionSidebar]):
        """
        Args:
            query_sidebar: Callable that returns the SessionSidebar widget,
                          or raises NoMatches if not found.
        """
        self._query_sidebar = query_sidebar

    def on_tokens_updated(
        self,
        context_tokens: int,
        output_tokens: int,
        cache_read_tokens: int,
        cache_creation_tokens: int,
        cost_usd: float,
    ) -> None:
        from textual.css.query import NoMatches

        try:
            sidebar = self._query_sidebar()
            sidebar.context_tokens = context_tokens
            sidebar.output_tokens = output_tokens
            sidebar.cache_read_tokens = cache_read_tokens
            sidebar.cache_creation_tokens = cache_creation_tokens
            sidebar.cost_usd = cost_usd
        except NoMatches:
            pass

    def on_stats_updated(
        self, message_count: int, tool_count: int, summarization_count: int
    ) -> None:
        from textual.css.query import NoMatches

        try:
            sidebar = self._query_sidebar()
            sidebar.message_count = message_count
            sidebar.tool_count = tool_count
            sidebar.summarization_count = summarization_count
        except NoMatches:
            pass
