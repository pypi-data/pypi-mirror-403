"""
TUI callback implementations.

This module bridges agent/tool events to TUI presentation, implementing
the callback protocols that AgentRunner and ToolExecutor depend on.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Protocol

from anthropic.types import Message, MessageParam
from textual.css.query import NoMatches

from hypergolic.tools.enums import ToolName
from hypergolic.tui.tool_executor import ToolContext
from hypergolic.tui.widgets.merge_approval import MergeApprovalScreen
from hypergolic.tui.widgets.token_usage import TokenUsage
from hypergolic.tui.widgets.tool_approval import ToolApprovalResult, ToolApprovalScreen

if TYPE_CHECKING:
    from hypergolic.tui.app import TUI
    from hypergolic.tui.session_tab import SessionTab
    from hypergolic.tui.widgets.conversation import AgentMessage, ConversationView


class AgentMessageManager(Protocol):
    """Protocol for managing the current agent message in the UI."""

    def get_current_message(self) -> AgentMessage | None: ...
    def set_current_message(self, msg: AgentMessage | None) -> None: ...
    def cleanup_message(self, mark_interrupted: bool = False) -> None: ...
    def reset_tool_handler(self) -> None: ...


class TUICallbacks:
    """
    Bridges agent/tool events to TUI presentation.

    Implements both AgentRunnerCallbacks and ToolUICallbacks protocols
    through duck typing, keeping the TUI class focused on composition
    and Textual-specific concerns.
    """

    def __init__(
        self,
        tui: TUI,
        session_tab: SessionTab,
    ):
        self._tui = tui
        self._session_tab = session_tab

    # --- AgentRunnerCallbacks implementation ---

    def on_streaming_start(self) -> None:
        """Called when streaming is about to start."""
        conversation_view = self.get_conversation_view()
        if conversation_view:
            agent_message = conversation_view.add_agent_message("")
            self._session_tab.set_current_message(agent_message)

    def on_stream_text(self, text: str) -> None:
        """Called with accumulated text during streaming."""
        current_msg = self._session_tab.get_current_message()
        if current_msg:
            current_msg.update_content(text)
            conversation_view = self.get_conversation_view()
            if conversation_view:
                conversation_view.scroll_end(animate=False)

    def on_stream_complete(self, response: Message) -> None:
        """Called when streaming finishes successfully."""
        current_msg = self._session_tab.get_current_message()
        if current_msg and response.usage:
            usage = TokenUsage.from_api_usage(response.usage)
            current_msg.set_token_usage(usage)
        self._session_tab.cleanup_message()

    def on_stream_error(self, error: Exception) -> None:
        """Called when streaming encounters an error."""
        self._session_tab.cleanup_message(mark_interrupted=True)
        conversation_view = self.get_conversation_view()
        if conversation_view:
            conversation_view.add_agent_message(
                f"❌ An error occurred while getting a response. Please try again: {error}."
            )
        self._session_tab.reset_tool_handler()
        self.focus_input()

    def on_stream_cancelled(self) -> None:
        """Called when streaming is cancelled (not interrupted)."""
        self._session_tab.cleanup_message(mark_interrupted=True)
        conversation_view = self.get_conversation_view()
        if conversation_view:
            conversation_view.add_agent_message("⚠️ Response cancelled.")
        self._session_tab.reset_tool_handler()
        self.focus_input()

    def on_turn_complete(self) -> None:
        """Called when the entire turn (including tools) is complete."""
        self._session_tab.reset_tool_handler()
        self.focus_input()

    def on_summarization_suggested(self) -> None:
        """Called when context size suggests summarization."""
        self._session_tab.show_summarization_prompt()

    def on_summarization_started(self) -> None:
        """Called when summarization begins."""
        conversation_view = self.get_conversation_view()
        if conversation_view:
            agent_message = conversation_view.add_agent_message(
                "📝 Context window growing large, summarizing conversation..."
            )
            self._session_tab.set_current_message(agent_message)

    def on_summarization_complete(self, formatted_summary: str) -> None:
        """Called when summarization finishes."""
        self._session_tab.cleanup_message()
        self._session_tab.handle_summarization_complete(formatted_summary)

    # --- ToolUICallbacks implementation ---

    def get_conversation_view(self) -> ConversationView | None:
        """Get the conversation view for this callback's session tab.

        Returns None if the view doesn't exist yet (e.g., during early
        initialization or error handling before UI is fully mounted).
        """
        from hypergolic.tui.widgets.conversation import ConversationView

        try:
            return self._session_tab.query_one(
                f"#conversation-{self._session_tab.tab_id}", ConversationView
            )
        except NoMatches:
            return None

    async def request_tool_approval(
        self, context: ToolContext
    ) -> ToolApprovalResult | None:
        """Show approval screen and wait for user decision."""
        future: asyncio.Future[ToolApprovalResult | None] = asyncio.Future()

        def on_result(result: ToolApprovalResult | None) -> None:
            if not future.done():
                future.set_result(result)

        session_context = self._session_tab.session_context

        if context.tool_name == ToolName.MERGE_BRANCH:
            screen = MergeApprovalScreen(session_context)
        else:
            screen = ToolApprovalScreen(context.tool_use)

        self._tui.push_screen(screen, on_result)
        return await future

    def focus_input(self) -> None:
        self._session_tab.focus_input()

    def add_tool_result(self, result: MessageParam) -> None:
        self._session_tab.conversation.add_tool_result(result)
