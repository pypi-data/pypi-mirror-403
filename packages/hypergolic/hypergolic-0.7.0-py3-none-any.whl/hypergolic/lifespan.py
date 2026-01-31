"""Lifespan management for Hypergolic sessions.

Each session operates in its own git worktree to enable multiple concurrent
sessions without interference. The worktree is created on session start and
cleaned up on session end.

Note: Git worktree management is now handled per-tab in SessionTab.
This module provides the legacy context manager for backwards compatibility
and any app-wide lifecycle concerns.
"""

import logging
from contextlib import contextmanager

from hypergolic.session_context import SessionContext
from hypergolic.version_control import (
    WorktreeCleanupResult,
    cleanup_worktree,
    create_worktree,
    stash_dirty_branch,
    unstash_dirty_branch,
)

logger = logging.getLogger(__name__)


@contextmanager
def HypergolicLifespan(session_context: SessionContext, merge_on_exit: bool = False):
    """Context manager for app-wide lifecycle.

    With multi-tab support, git branch management is now done per-tab.
    This context manager now only handles the initial session's branch
    to maintain backwards compatibility with the App initialization.
    """
    start(session_context)
    try:
        yield
    finally:
        # Note: Branch cleanup is now handled by SessionTab.end_lifespan()
        # called from TUI.action_quit(). This end() call is a safety net
        # for abnormal exits.
        pass


def start(session_context: SessionContext):
    """Initialize the session's git worktree."""
    print("Starting session...")
    stash_dirty_branch(session_context)
    if not create_worktree(session_context):
        raise RuntimeError(
            f"Failed to create worktree at {session_context.worktree_root}"
        )


def end(session_context: SessionContext, merge_on_exit: bool = False):
    """Clean up a session's git worktree and branch.

    This is primarily called by SessionTab.end_lifespan() now.
    Kept for backwards compatibility.
    """
    print("Ending session...")

    result = cleanup_worktree(session_context, merge_if_changes=merge_on_exit)

    match result:
        case WorktreeCleanupResult.DELETED:
            print(f"Cleaned up empty branch: {session_context.agent_branch}")
        case WorktreeCleanupResult.MERGED:
            print(
                f"✅ Merged {session_context.agent_branch} into {session_context.original_branch}"
            )
        case WorktreeCleanupResult.PRESERVED:
            print(f"⚠️  Branch preserved with changes: {session_context.agent_branch}")
            print(f"   To merge: git merge {session_context.agent_branch}")
            print(f"   To delete: git branch -D {session_context.agent_branch}")
        case WorktreeCleanupResult.NOT_FOUND:
            pass  # Worktree was already cleaned up somehow

    unstash_dirty_branch(session_context)
