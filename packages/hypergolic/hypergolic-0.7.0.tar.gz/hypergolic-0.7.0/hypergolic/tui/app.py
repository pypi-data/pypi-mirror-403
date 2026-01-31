from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam, TextBlockParam
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, TabbedContent, TabPane, Tabs

from hypergolic.config import HypergolicConfig
from hypergolic.conversation_manager import ConversationManager
from hypergolic.session_context import SessionContext
from hypergolic.session_stats import SessionStats
from hypergolic.tui.session_tab import SessionTab, create_session_tab
from hypergolic.tui.widgets.clear_confirmation import (
    ClearAction,
    ClearConfirmationResult,
    ClearConfirmationScreen,
)
from hypergolic.tui.widgets.close_tab_confirmation import (
    CloseTabAction,
    CloseTabConfirmationResult,
    CloseTabConfirmationScreen,
)
from hypergolic.tui.widgets.conversation import AgentMessage
from hypergolic.tui.widgets.file_browser import FileBrowserFileSelected
from hypergolic.tui.widgets.header import HypergolicHeader
from hypergolic.tui.widgets.prompt_input import PromptInput
from hypergolic.version_control import (
    WorktreeCleanupResult,
    commit_all_changes,
    discard_uncommitted_changes,
    force_delete_agent_branch,
    has_committed_changes,
    has_uncommitted_changes,
    is_branch_merged,
    remove_worktree,
    unstash_dirty_branch,
)

if TYPE_CHECKING:
    from hypergolic.app import App as HypergolicApp

logger = logging.getLogger(__name__)


class TUI(App):
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("ctrl+l", "clear_conversation", "Clear", show=True),
        Binding("ctrl+b", "toggle_sidebar", "Sidebar", show=True),
        Binding("ctrl+e", "toggle_file_browser", "Files", show=True),
        Binding("ctrl+w", "close_tab", "Close", show=True),
        Binding("escape", "cancel", "Cancel", show=False),
        # Tab management
        Binding("ctrl+t", "new_tab", "New Tab", show=True),
        Binding("cmd+1", "goto_tab_1", "Tab 1", show=False),
        Binding("cmd+2", "goto_tab_2", "Tab 2", show=False),
        Binding("cmd+3", "goto_tab_3", "Tab 3", show=False),
        Binding("cmd+4", "goto_tab_4", "Tab 4", show=False),
        Binding("cmd+5", "goto_tab_5", "Tab 5", show=False),
        Binding("cmd+6", "goto_tab_6", "Tab 6", show=False),
        Binding("cmd+7", "goto_tab_7", "Tab 7", show=False),
        Binding("cmd+8", "goto_tab_8", "Tab 8", show=False),
        Binding("cmd+9", "goto_tab_9", "Tab 9", show=False),
        Binding("cmd+left_square_bracket", "prev_tab", "Prev Tab", show=False),
        Binding("cmd+right_square_bracket", "next_tab", "Next Tab", show=False),
    ]

    def __init__(
        self,
        app: HypergolicApp,
        session_context: SessionContext,
        config: HypergolicConfig,
        client: AsyncAnthropic,
        system_prompt: list[TextBlockParam],
        stats: SessionStats,
        conversation: ConversationManager,
    ):
        super().__init__()
        self._app = app
        self._initial_session_context = session_context
        self._initial_config = config
        self._initial_client = client
        self._initial_system_prompt = system_prompt
        self._initial_stats = stats
        self._initial_conversation = conversation

        # Track all session tabs
        self._tabs: dict[str, SessionTab] = {}
        self._active_tab_id: str | None = None
        self._tab_counter = 0

    @property
    def active_tab(self) -> SessionTab | None:
        """Get the currently active session tab."""
        if self._active_tab_id and self._active_tab_id in self._tabs:
            return self._tabs[self._active_tab_id]
        return None

    @property
    def messages(self) -> list[MessageParam]:
        tab = self.active_tab
        return tab.conversation.messages if tab else []

    @property
    def is_busy(self) -> bool:
        tab = self.active_tab
        return tab.is_busy if tab else False

    def compose(self) -> ComposeResult:
        yield HypergolicHeader(self._initial_session_context)
        with TabbedContent(id="session-tabs"):
            # First tab created with initial session
            # Note: lifespan_already_started=True because HypergolicLifespan
            # in entrypoint already created and checked out the branch
            tab_id = self._generate_tab_id()
            first_tab = SessionTab(
                tui=self,
                session_context=self._initial_session_context,
                config=self._initial_config,
                client=self._initial_client,
                system_prompt=self._initial_system_prompt,
                stats=self._initial_stats,
                conversation=self._initial_conversation,
                tab_id=tab_id,
                lifespan_already_started=True,
            )
            self._tabs[tab_id] = first_tab
            self._active_tab_id = tab_id
            # Store runner for external access
            self._app.runner = first_tab.runner
            with TabPane(first_tab.tab_name, id=f"pane-{tab_id}"):
                yield first_tab
        yield Footer()

    def _generate_tab_id(self) -> str:
        """Generate a unique tab ID."""
        self._tab_counter += 1
        return f"tab-{self._tab_counter}"

    def on_mount(self) -> None:
        # Focus the first tab's input
        if self.active_tab:
            self.active_tab.focus_input()
        # Hide tabs bar when only one tab
        self._update_tabs_visibility()

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        """Handle tab switch events."""
        # Extract tab_id from pane id ("pane-tab-1" -> "tab-1")
        pane_id = str(event.pane.id) if event.pane.id else ""
        if pane_id.startswith("pane-"):
            tab_id = pane_id[5:]  # Remove "pane-" prefix

            # Deactivate old tab
            if self._active_tab_id and self._active_tab_id in self._tabs:
                self._tabs[self._active_tab_id].deactivate()

            # Activate new tab
            self._active_tab_id = tab_id
            if tab_id in self._tabs:
                new_tab = self._tabs[tab_id]
                new_tab.activate()
                # Update the app's runner reference
                self._app.runner = new_tab.runner
                # Update header to show current session
                self._update_header(new_tab.session_context)

    def _update_header(self, session_context: SessionContext) -> None:
        """Update the header to reflect the current session."""
        try:
            header = self.query_one(HypergolicHeader)
            header.session_context = session_context
            # Update the branch display
            from hypergolic.tui.widgets.header import BranchDisplay
            branch_display = header.query_one(BranchDisplay)
            branch_display.session_context = session_context
            branch_display.refresh()
        except Exception:
            pass  # Header may not be ready

    # AgentMessageManager protocol - delegates to active tab

    def get_current_message(self) -> AgentMessage | None:
        tab = self.active_tab
        return tab.get_current_message() if tab else None

    def set_current_message(self, msg: AgentMessage | None) -> None:
        tab = self.active_tab
        if tab:
            tab.set_current_message(msg)

    def cleanup_message(self, mark_interrupted: bool = False) -> None:
        tab = self.active_tab
        if tab:
            tab.cleanup_message(mark_interrupted)

    # Input handling - route to correct tab based on event source

    def on_prompt_input_submitted(self, event: PromptInput.Submitted) -> None:
        """Handle prompt submission from any tab."""
        # Find which tab this input belongs to
        prompt_input = event.text_area
        prompt_id = str(prompt_input.id) if prompt_input.id else ""

        # Extract tab_id from prompt input id ("prompt-input-tab-1" -> "tab-1")
        tab_id = None
        if prompt_id.startswith("prompt-input-"):
            tab_id = prompt_id[len("prompt-input-"):]

        tab = self._tabs.get(tab_id) if tab_id else self.active_tab
        if not tab:
            return

        message = prompt_input.text.strip()
        if message:
            prompt_input.clear()
            if tab.is_busy:
                tab.request_interrupt(message)
            else:
                tab.handle_user_message(message)

    def _focus_input(self) -> None:
        tab = self.active_tab
        if tab:
            tab.focus_input()

    # Tab management actions

    def action_new_tab(self) -> None:
        """Create a new session tab."""
        tab_id = self._generate_tab_id()
        # All tabs branch from the same original branch (e.g., 'main')
        original_branch = self._initial_session_context.original_branch
        new_tab = create_session_tab(self, tab_id, original_branch)
        self._tabs[tab_id] = new_tab

        # Add the new tab pane
        tabbed_content = self.query_one("#session-tabs", TabbedContent)
        new_pane = TabPane(new_tab.tab_name, id=f"pane-{tab_id}")
        tabbed_content.add_pane(new_pane)

        # Mount the SessionTab widget inside the pane
        new_pane.mount(new_tab)

        # Switch to the new tab
        tabbed_content.active = f"pane-{tab_id}"

        # Show tabs bar now that we have multiple tabs
        self._update_tabs_visibility()

    def _check_tab_for_unmerged_changes(
        self, tab: SessionTab
    ) -> tuple[bool, bool]:
        """Check if a tab has uncommitted or unmerged committed changes.

        Returns (has_uncommitted, has_unmerged_committed) tuple.
        """
        uncommitted = has_uncommitted_changes(tab.session_context)
        # Only consider committed changes "unmerged" if they're not already in the original branch
        committed = has_committed_changes(tab.session_context) and not is_branch_merged(
            tab.session_context
        )
        return uncommitted, committed

    async def action_close_tab(self) -> None:
        """Close the current tab."""
        if len(self._tabs) <= 1:
            # Don't close the last tab - quit instead
            await self.action_quit()
            return

        tab = self.active_tab
        if not tab:
            return

        # Check for uncommitted and unmerged committed changes
        uncommitted, committed = self._check_tab_for_unmerged_changes(tab)

        if uncommitted or committed:
            self.push_screen(
                CloseTabConfirmationScreen(
                    tab.session_context.agent_branch,
                    has_uncommitted=uncommitted,
                    has_committed=committed,
                ),
                self._handle_close_tab_confirmation,
            )
        else:
            self._do_close_tab(tab, delete_branch=False)

    def _handle_close_tab_confirmation(
        self, result: CloseTabConfirmationResult | None
    ) -> None:
        """Handle the result of the close tab confirmation dialog."""
        tab = self.active_tab
        if not tab:
            return

        if result is None or result.action == CloseTabAction.CANCEL:
            tab.focus_input()
            return

        delete_branch = result.action == CloseTabAction.CLOSE_DELETE
        self._do_close_tab(tab, delete_branch=delete_branch)

    def _cleanup_tab(self, tab: SessionTab, delete_branch: bool = False) -> None:
        """Clean up tab resources (save history, handle worktree/branch).

        This is the core cleanup logic shared by close_tab and quit flows.
        Does NOT remove the tab from UI - caller handles that if needed.
        """
        tab.save_history()

        if delete_branch:
            # Force delete the branch - discard any uncommitted changes first
            if has_uncommitted_changes(tab.session_context):
                discard_uncommitted_changes(tab.session_context)
            # Remove worktree first, then delete branch
            remove_worktree(tab.session_context)
            force_delete_agent_branch(tab.session_context)
            unstash_dirty_branch(tab.session_context)
            tab._lifespan_started = False
            self._log_worktree_cleanup(
                tab.session_context.agent_branch, WorktreeCleanupResult.DELETED
            )
        else:
            # Preserve branch - commit uncommitted changes first to save work
            if has_uncommitted_changes(tab.session_context):
                commit_all_changes(
                    tab.session_context,
                    "WIP: Auto-saved uncommitted changes on tab close",
                )
            # Normal cleanup - preserves branch if it has changes
            result = tab.end_lifespan()
            self._log_worktree_cleanup(tab.session_context.agent_branch, result)

    def _do_close_tab(self, tab: SessionTab, delete_branch: bool = False) -> None:
        """Actually close the tab and clean up resources."""
        tab_id = tab.tab_id

        self._cleanup_tab(tab, delete_branch)

        # Remove from tracking
        del self._tabs[tab_id]

        # Remove the pane
        tabbed_content = self.query_one("#session-tabs", TabbedContent)
        tabbed_content.remove_pane(f"pane-{tab_id}")

        # Hide tabs bar if back to single tab
        self._update_tabs_visibility()

    def _update_tabs_visibility(self) -> None:
        """Show/hide the tabs bar based on tab count."""
        try:
            tabbed_content = self.query_one("#session-tabs", TabbedContent)
            tabs = tabbed_content.query_one(Tabs)
            tabs.display = len(self._tabs) > 1
        except Exception:
            pass  # Widget may not be ready

    def _log_worktree_cleanup(self, branch: str, result: WorktreeCleanupResult) -> None:
        """Log worktree cleanup result."""
        match result:
            case WorktreeCleanupResult.DELETED:
                logger.info("Cleaned up empty branch: %s", branch)
            case WorktreeCleanupResult.MERGED:
                logger.info("Merged branch: %s", branch)
            case WorktreeCleanupResult.PRESERVED:
                self.notify(
                    f"Branch preserved: {branch}",
                    title="Branch has changes",
                    severity="warning",
                )
            case WorktreeCleanupResult.NOT_FOUND:
                pass

    def _goto_tab(self, index: int) -> None:
        """Switch to tab at given 0-based index."""
        tab_ids = list(self._tabs.keys())
        if 0 <= index < len(tab_ids):
            tab_id = tab_ids[index]
            tabbed_content = self.query_one("#session-tabs", TabbedContent)
            tabbed_content.active = f"pane-{tab_id}"

    def action_goto_tab_1(self) -> None:
        self._goto_tab(0)

    def action_goto_tab_2(self) -> None:
        self._goto_tab(1)

    def action_goto_tab_3(self) -> None:
        self._goto_tab(2)

    def action_goto_tab_4(self) -> None:
        self._goto_tab(3)

    def action_goto_tab_5(self) -> None:
        self._goto_tab(4)

    def action_goto_tab_6(self) -> None:
        self._goto_tab(5)

    def action_goto_tab_7(self) -> None:
        self._goto_tab(6)

    def action_goto_tab_8(self) -> None:
        self._goto_tab(7)

    def action_goto_tab_9(self) -> None:
        self._goto_tab(8)

    def action_prev_tab(self) -> None:
        """Switch to the previous tab, wrapping around."""
        tab_ids = list(self._tabs.keys())
        if len(tab_ids) <= 1:
            return
        current_index = (
            tab_ids.index(self._active_tab_id)
            if self._active_tab_id in tab_ids
            else 0
        )
        new_index = (current_index - 1) % len(tab_ids)
        self._goto_tab(new_index)

    def action_next_tab(self) -> None:
        """Switch to the next tab, wrapping around."""
        tab_ids = list(self._tabs.keys())
        if len(tab_ids) <= 1:
            return
        current_index = (
            tab_ids.index(self._active_tab_id)
            if self._active_tab_id in tab_ids
            else 0
        )
        new_index = (current_index + 1) % len(tab_ids)
        self._goto_tab(new_index)

    # Session actions - delegate to active tab

    def action_clear_conversation(self) -> None:
        tab = self.active_tab
        if not tab:
            return

        has_messages = len(tab.conversation.messages) > 0
        self.push_screen(
            ClearConfirmationScreen(has_messages=has_messages),
            self._handle_clear_confirmation,
        )

    def _handle_clear_confirmation(
        self, result: ClearConfirmationResult | None
    ) -> None:
        tab = self.active_tab
        if not tab:
            return

        if result is None or result.action == ClearAction.CANCEL:
            tab.focus_input()
            return

        if result.action == ClearAction.CLEAR:
            tab.clear_conversation()
        elif result.action == ClearAction.SUMMARIZE:
            asyncio.create_task(tab.summarize_and_clear())

    def action_toggle_sidebar(self) -> None:
        tab = self.active_tab
        if tab:
            tab.toggle_sidebar()

    def action_toggle_file_browser(self) -> None:
        tab = self.active_tab
        if tab:
            tab.toggle_file_browser()

    def on_file_browser_file_selected(self, event: FileBrowserFileSelected) -> None:
        """Handle file selection from the file browser."""
        tab = self.active_tab
        if tab:
            path = event.path
            relative_path = path.relative_to(tab.session_context.worktree_root)
            self.notify(f"Selected: {relative_path}", title="File")
            tab.focus_input()

    def action_cancel(self) -> None:
        tab = self.active_tab
        if tab:
            tab.cancel()

        for worker in self.workers:
            if worker.is_running:
                worker.cancel()

    async def action_quit(self) -> None:
        """Quit the application, cleaning up all tabs."""
        # Check all tabs for unmerged work (skip any already handled in this quit flow)
        tabs_with_changes: list[tuple[SessionTab, bool, bool]] = []
        for tab in self._tabs.values():
            if tab._quit_handled:
                continue
            uncommitted, committed = self._check_tab_for_unmerged_changes(tab)
            if uncommitted or committed:
                tabs_with_changes.append((tab, uncommitted, committed))

        if tabs_with_changes:
            # Show confirmation for the first tab with changes
            # After handling, action_quit will be called again to check remaining
            tab, uncommitted, committed = tabs_with_changes[0]
            # Switch to the tab so user can see what they're deciding about
            tab_id = tab.tab_id
            tabbed_content = self.query_one("#session-tabs", TabbedContent)
            tabbed_content.active = f"pane-{tab_id}"
            self.push_screen(
                CloseTabConfirmationScreen(
                    tab.session_context.agent_branch,
                    has_uncommitted=uncommitted,
                    has_committed=committed,
                ),
                self._handle_quit_tab_confirmation,
            )
            return

        # No tabs with unmerged changes, safe to quit
        self._do_quit()

    def _handle_quit_tab_confirmation(
        self, result: CloseTabConfirmationResult | None
    ) -> None:
        """Handle confirmation result when quitting with unmerged changes."""
        tab = self.active_tab
        if not tab:
            return

        if result is None or result.action == CloseTabAction.CANCEL:
            # Reset _quit_handled on all tabs since quit was cancelled
            for t in self._tabs.values():
                t._quit_handled = False
            tab.focus_input()
            return

        # Clean up this tab based on user choice
        delete_branch = result.action == CloseTabAction.CLOSE_DELETE
        self._cleanup_tab(tab, delete_branch)

        # Mark this tab as handled so we don't check it again
        tab._quit_handled = True

        # Continue quitting - check remaining tabs
        self.call_later(self.action_quit)

    def _do_quit(self) -> None:
        """Actually quit the application after all confirmations."""
        for tab in self._tabs.values():
            # Skip tabs already handled during quit confirmation
            if tab._quit_handled:
                continue
            self._cleanup_tab(tab, delete_branch=False)
        self.exit()


