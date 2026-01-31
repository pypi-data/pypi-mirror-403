"""
Session tab - encapsulates all per-session state and UI.

Each tab represents an independent Hypergolic session with its own:
- Git branch
- Conversation history
- Stats tracking
- Agent runner
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from anthropic import AsyncAnthropic
from anthropic.types import TextBlockParam
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget

from hypergolic.agent_runner import AgentRunner
from hypergolic.config import HypergolicConfig
from hypergolic.conversation_manager import ConversationManager
from hypergolic.pricing import get_pricing
from hypergolic.prompts.resolvers import build_operator_system_prompt
from hypergolic.providers import build_provider_client
from hypergolic.session_context import SessionContext, build_session_context
from hypergolic.session_history import SessionHistoryManager
from hypergolic.session_stats import SessionStats
from hypergolic.tools.approval_manager import ApprovalManager
from hypergolic.tools.tool_list import get_tools
from hypergolic.tui.callbacks import TUICallbacks
from hypergolic.tui.sidebar_observer import SidebarStatsObserver
from hypergolic.tui.streaming import StreamingController
from hypergolic.tui.tool_executor import ToolExecutor
from hypergolic.tui.tool_ui_handler import ToolUIHandler
from hypergolic.tui.widgets.conversation import AgentMessage, ConversationView
from hypergolic.tui.widgets.file_browser import FileBrowser
from hypergolic.tui.widgets.prompt_input import PromptInput
from hypergolic.tui.widgets.sidebar import SessionSidebar
from hypergolic.version_control import (
    WorktreeCleanupResult,
    cleanup_worktree,
    create_worktree,
    stash_dirty_branch,
    unstash_dirty_branch,
)

if TYPE_CHECKING:
    from hypergolic.tui.app import TUI

logger = logging.getLogger(__name__)


class SessionTab(Widget):
    """A complete session view that can be used as a tab pane content."""

    DEFAULT_CSS = """
    SessionTab {
        width: 1fr;
        height: 1fr;
        layout: vertical;
    }

    SessionTab #session-main-content {
        height: 1fr;
    }

    SessionTab #session-input-area {
        dock: bottom;
        height: auto;
        max-height: 10;
        padding: 0 1;
        background: #1e293b;
        border-top: solid #334155;
    }

    SessionTab #session-prompt-input {
        margin: 1 0;
        height: auto;
        min-height: 3;
        max-height: 8;
        background: #0f172a;
        border: tall #475569;
    }

    SessionTab #session-prompt-input:focus {
        border: tall #6366f1;
    }
    """

    def __init__(
        self,
        tui: TUI,
        session_context: SessionContext,
        config: HypergolicConfig,
        client: AsyncAnthropic,
        system_prompt: list[TextBlockParam],
        stats: SessionStats,
        conversation: ConversationManager,
        tab_id: str,
        lifespan_already_started: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._tui = tui
        self.session_context = session_context
        self.config = config
        self.client = client
        self.system_prompt = system_prompt
        self.stats = stats
        self.conversation = conversation
        self.tab_id = tab_id

        self._current_agent_message: AgentMessage | None = None
        self._is_active = False
        # For the first tab, lifespan is started by HypergolicLifespan in entrypoint
        self._lifespan_started = lifespan_already_started
        # Used during quit flow to track tabs that have been handled
        self._quit_handled = False

        # Set up callbacks that bridge events to UI
        self._callbacks = TUICallbacks(tui=tui, session_tab=self)
        self.stats.observer = SidebarStatsObserver(
            query_sidebar=lambda: self.query_one(
                f"#sidebar-{self.tab_id}", SessionSidebar
            )
        )

        # Create approval manager
        project_id = session_context.remote_url or session_context.project_name
        self._approval_manager = ApprovalManager(
            config=self.config,
            project_id=project_id,
        )

        self._tool_handler = ToolUIHandler(
            ui_callbacks=self._callbacks,
            client=self.client,
            config=self.config,
            session_context=session_context,
            approval_manager=self._approval_manager,
            stats_increment_tool=self.stats.increment_tool_count,
        )

        self._tool_executor = ToolExecutor(
            approval_manager=self._approval_manager, callbacks=self._tool_handler
        )

        # Create the runner
        self._streaming = StreamingController(client=self.client)
        self._runner = AgentRunner(
            client=self.client,
            config=self.config,
            system_prompt=self.system_prompt,
            tools=get_tools(),
            conversation=self.conversation,
            stats=self.stats,
            tool_executor=self._tool_executor,
            streaming=self._streaming,
            callbacks=self._callbacks,
        )

        # Session history manager
        self._history_manager = SessionHistoryManager(session_context)

    @property
    def runner(self) -> AgentRunner:
        return self._runner

    @property
    def is_busy(self) -> bool:
        return self._runner.is_busy

    @property
    def tab_name(self) -> str:
        """Generate tab name: project_session-id."""
        # Extract session ID from branch name (e.g., "agent/session-abc123" -> "abc123")
        branch = self.session_context.agent_branch
        session_id = branch.split("-")[-1] if "-" in branch else branch
        return f"{self.session_context.project_name}_{session_id}"

    def compose(self) -> ComposeResult:
        with Horizontal(id="session-main-content"):
            yield FileBrowser(
                self.session_context.worktree_root,
                expand_to=self.session_context.file_browser_root,
                project_name=self.session_context.project_name,
                id=f"file-browser-{self.tab_id}",
            )
            yield ConversationView(id=f"conversation-{self.tab_id}")
            yield SessionSidebar(
                self.session_context, id=f"sidebar-{self.tab_id}"
            )
        yield Vertical(
            PromptInput(
                id=f"prompt-input-{self.tab_id}",
                tab_behavior="focus",
                placeholder="Enter your message... (Shift+Enter for newline)",
            ),
            id="session-input-area",
        )

    def on_mount(self) -> None:
        # Start lifespan when first mounted (for new tabs created after initial)
        if not self._lifespan_started:
            self._start_lifespan()
        # Focus input after mount
        self.call_after_refresh(self.focus_input)

    def _start_lifespan(self) -> None:
        """Initialize the git worktree for this session."""
        logger.info(
            "Starting session lifespan for %s at %s",
            self.session_context.agent_branch,
            self.session_context.worktree_root,
        )
        stash_dirty_branch(self.session_context)
        if not create_worktree(self.session_context):
            logger.error(
                "Failed to create worktree at %s", self.session_context.worktree_root
            )
            raise RuntimeError(
                f"Failed to create worktree at {self.session_context.worktree_root}"
            )
        self._lifespan_started = True

    def end_lifespan(self, merge_on_exit: bool = False) -> WorktreeCleanupResult:
        """Clean up the git worktree for this session."""
        if not self._lifespan_started:
            return WorktreeCleanupResult.NOT_FOUND

        logger.info(
            "Ending session lifespan for %s", self.session_context.agent_branch
        )

        result = cleanup_worktree(self.session_context, merge_if_changes=merge_on_exit)
        unstash_dirty_branch(self.session_context)

        self._lifespan_started = False
        return result

    def activate(self) -> None:
        """Called when this tab becomes active.

        With worktrees, each session has its own directory so no checkout needed.
        """
        self._is_active = True
        self.focus_input()

    def deactivate(self) -> None:
        """Called when switching away from this tab."""
        self._is_active = False

    def focus_input(self) -> None:
        """Focus the prompt input for this session."""
        try:
            self.query_one(f"#prompt-input-{self.tab_id}", PromptInput).focus()
        except Exception:
            pass  # Tab may not be fully mounted yet

    # AgentMessageManager protocol implementation

    def get_current_message(self) -> AgentMessage | None:
        return self._current_agent_message

    def set_current_message(self, msg: AgentMessage | None) -> None:
        self._current_agent_message = msg

    def cleanup_message(self, mark_interrupted: bool = False) -> None:
        if self._current_agent_message:
            has_content = bool(self._current_agent_message.content_text.strip())
            if has_content:
                if mark_interrupted:
                    self._current_agent_message.mark_interrupted()
            else:
                self._current_agent_message.remove()
        self._current_agent_message = None

    def reset_tool_handler(self) -> None:
        """Reset the tool handler state."""
        self._tool_handler.reset()

    # Message handling

    def handle_user_message(self, message: str) -> None:
        """Handle a user message submission."""
        conversation_view = self.query_one(
            f"#conversation-{self.tab_id}", ConversationView
        )
        conversation_view.add_user_message(message)
        self._runner.submit_message(message)

    def request_interrupt(self, message: str) -> None:
        """Handle an interrupt request."""
        self.cleanup_message(mark_interrupted=True)

        conversation_view = self.query_one(
            f"#conversation-{self.tab_id}", ConversationView
        )
        conversation_view.add_user_message(f"[Interrupt] {message}", is_interrupt=True)

        if self._tool_handler.cancellation_token:
            self._tool_handler.cancellation_token.cancel()

        self._runner.interrupt(message)

    def cancel(self) -> None:
        """Cancel current operation."""
        if self._tool_handler.cancellation_token:
            self._tool_handler.cancellation_token.cancel()
        self._runner.cancel()

    # Summarization

    def show_summarization_prompt(self) -> None:
        """Show prompt asking user if they want to summarize."""
        from hypergolic.tui.widgets.summarization_prompt import (
            SummarizationPromptResult,
            SummarizationPromptScreen,
        )

        async def do_summarize() -> None:
            prompt_input = self.query_one(
                f"#prompt-input-{self.tab_id}", PromptInput
            )
            prompt_input.disabled = True
            try:
                await self._runner.summarize_now()
            finally:
                prompt_input.disabled = False
                self.focus_input()

        def handle_result(result: SummarizationPromptResult | None) -> None:
            if result and result.should_summarize:
                # Set session auto-approve if user selected "Always"
                if result.auto_approve_session:
                    self._runner.set_auto_summarize_session(True)
                asyncio.create_task(do_summarize())
            else:
                self.focus_input()

        self._tui.push_screen(SummarizationPromptScreen(), handle_result)

    def handle_summarization_complete(self, formatted_summary: str) -> None:
        """Handle completion of summarization.

        The summary message has already been added to conversation.messages.
        This just updates the UI to show the summary as a collapsible message.
        """
        conversation_view = self.query_one(
            f"#conversation-{self.tab_id}", ConversationView
        )
        # Add the summary message to the UI (doesn't clear existing messages)
        conversation_view.add_summary_message(formatted_summary)

    # Clear conversation

    def clear_conversation(self) -> None:
        """Fully clear the conversation - wipes all history."""
        conversation_view = self.query_one(
            f"#conversation-{self.tab_id}", ConversationView
        )
        conversation_view.clear()
        self.conversation.clear()
        self.focus_input()

    async def summarize_and_clear(self) -> None:
        """Create a summarization checkpoint (history preserved)."""
        # Use the same summarization flow as threshold-triggered summarization
        await self._runner.summarize_now()
        self.focus_input()

    # Sidebar/file browser toggles

    def toggle_sidebar(self) -> None:
        sidebar = self.query_one(f"#sidebar-{self.tab_id}", SessionSidebar)
        sidebar.toggle()

    def toggle_file_browser(self) -> None:
        file_browser = self.query_one(f"#file-browser-{self.tab_id}", FileBrowser)
        file_browser.toggle()

    # Session persistence

    def save_history(self) -> None:
        """Save session history to disk."""
        try:
            filepath = self._history_manager.save(
                messages=self.conversation.messages,
                stats=self.stats.to_dict(),
                sub_agent_traces=self._tool_handler.get_sub_agent_traces() or None,
                usage_snapshots=[s.to_dict() for s in self.stats.get_all_snapshots()],
                message_metas=self.conversation.message_metas,
            )
            if filepath:
                logger.info("Session history saved to %s", filepath)
        except Exception as e:
            logger.warning("Failed to save session history: %s", e)


def create_session_tab(tui: TUI, tab_id: str, original_branch: str) -> SessionTab:
    """Factory function to create a new SessionTab with fresh session context.

    Args:
        tui: The TUI instance
        tab_id: Unique identifier for this tab
        original_branch: The original branch to base this session on (e.g., 'main')
    """
    session_context = build_session_context(original_branch=original_branch)
    config = HypergolicConfig()
    client: AsyncAnthropic = build_provider_client(config)
    system_prompt = build_operator_system_prompt(session_context)
    stats = SessionStats()
    stats.pricing = get_pricing(config.provider.model)
    conversation = ConversationManager(stats)

    return SessionTab(
        tui=tui,
        session_context=session_context,
        config=config,
        client=client,
        system_prompt=system_prompt,
        stats=stats,
        conversation=conversation,
        tab_id=tab_id,
    )
