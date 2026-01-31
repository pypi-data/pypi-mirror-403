"""Consolidated tool approval management.

This module provides a single ApprovalManager class that handles all approval logic:
1. Config-based auto-approval (tools in auto_approved_tools set)
2. Conditional approval (e.g., browser localhost vs external URLs)
3. Session approval (user selected "Always allow" for this session)
4. Forever approval (persisted to disk, approved across sessions)

The approval check order ensures that conditional checks (like browser localhost)
are always evaluated, even for session/forever approved commands.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from anthropic.types import ToolUseBlock

from hypergolic.config import HypergolicConfig
from hypergolic.tools.browser import get_current_page_url, is_localhost_url
from hypergolic.tools.enums import ToolName

logger = logging.getLogger(__name__)

HYPERGOLIC_DIR = Path.home() / ".hypergolic"
TOOL_APPROVALS_FILE = HYPERGOLIC_DIR / "tool_approvals.json"


def _browser_requires_approval(
    config: HypergolicConfig, tool_input: dict[str, Any]
) -> bool:
    """Check if browser operation requires approval (external URLs only)."""
    if config.browser_auto_approve:
        return False

    operation = tool_input.get("operation")
    url = tool_input.get("url")

    # Launch and close are always auto-approved
    if operation in ("launch", "close"):
        return False

    # Navigate checks the target URL
    if operation == "navigate":
        return not is_localhost_url(url)

    # For other operations, check what page we're currently on
    current_url = get_current_page_url()
    return not is_localhost_url(current_url)


# Tools with conditional approval logic that must always be checked
CONDITIONAL_APPROVAL_CHECKERS: dict[str, Any] = {
    ToolName.BROWSER.value: _browser_requires_approval,
}


def _get_approval_key(tool_name: str, tool_input: dict[str, Any]) -> str | None:
    """Get the key used to identify this tool call for session/forever approval.

    For command_line tools, this is the exact command string.
    Returns None if this tool type doesn't support session/forever approval.

    Currently only command_line supports session/forever approval. Tools with
    conditional approval logic (like browser) intentionally don't support this
    because each invocation may require different approval based on context
    (e.g., localhost vs external URLs need fresh evaluation each time).
    """
    if tool_name == ToolName.COMMAND_LINE.value or tool_name == ToolName.COMMAND_LINE:
        return tool_input.get("cmd")
    return None


@dataclass
class ApprovalManager:
    """Manages all tool approval logic in a single place.

    This consolidates:
    - Config-based auto-approval
    - Conditional approval (browser localhost, etc.)
    - Session approval (in-memory, cleared on exit)
    - Forever approval (persisted to disk)
    """

    config: HypergolicConfig
    project_id: str

    # Session-approved commands (in-memory only)
    _session_approved: set[str] = field(default_factory=set)

    # Cache for forever approvals to avoid repeated disk reads
    _forever_approved_cache: set[str] | None = field(default=None, init=False)

    def requires_approval(self, tool_use: ToolUseBlock) -> bool:
        """Check if a tool call requires user approval.

        This is the main entry point for approval checks. It evaluates all
        approval layers in the correct order.

        Returns True if user approval is needed, False if auto-approved.
        """
        if not self.config.require_tool_approval:
            return False

        tool_name = tool_use.name
        tool_input = tool_use.input if isinstance(tool_use.input, dict) else {}

        # Check conditional approval first (e.g., browser localhost)
        # This must happen before session/forever checks to ensure
        # browser localhost logic is always evaluated
        if tool_name in CONDITIONAL_APPROVAL_CHECKERS:
            checker = CONDITIONAL_APPROVAL_CHECKERS[tool_name]
            if not checker(self.config, tool_input):
                # Conditional check says no approval needed
                return False
            # Conditional check says approval needed - continue to other checks

        # Check config-based auto-approval
        auto_approved_names = {t.value for t in self.config.auto_approved_tools}
        if tool_name in auto_approved_names:
            return False

        # Check session/forever approval for eligible tools
        approval_key = _get_approval_key(tool_name, tool_input)
        if approval_key:
            if self._is_session_approved(approval_key):
                return False
            if self._is_forever_approved(approval_key):
                return False

        return True

    def is_auto_approved(self, tool_use: ToolUseBlock) -> bool:
        """Check if a tool was auto-approved (session or forever).

        This is used after execution to add notes to tool results indicating
        that the command was auto-approved.
        """
        tool_name = tool_use.name
        tool_input = tool_use.input if isinstance(tool_use.input, dict) else {}
        approval_key = _get_approval_key(tool_name, tool_input)

        if not approval_key:
            return False

        return (
            self._is_session_approved(approval_key)
            or self._is_forever_approved(approval_key)
        )

    def add_session_approval(self, tool_use: ToolUseBlock) -> None:
        """Add a tool call to the session-approved set."""
        tool_name = tool_use.name
        tool_input = tool_use.input if isinstance(tool_use.input, dict) else {}
        approval_key = _get_approval_key(tool_name, tool_input)

        if approval_key:
            self._session_approved.add(approval_key)
            logger.info("Added session approval for: %s", approval_key)

    def add_forever_approval(self, tool_use: ToolUseBlock) -> None:
        """Add a tool call to the forever-approved set (persisted to disk)."""
        tool_name = tool_use.name
        tool_input = tool_use.input if isinstance(tool_use.input, dict) else {}
        approval_key = _get_approval_key(tool_name, tool_input)

        if approval_key:
            self._add_forever_approval_to_disk(approval_key)
            # Also add to session set to avoid repeated disk checks
            self._session_approved.add(approval_key)
            # Invalidate cache
            self._forever_approved_cache = None

    def _is_session_approved(self, key: str) -> bool:
        """Check if a key is in the session-approved set."""
        return key in self._session_approved

    def _is_forever_approved(self, key: str) -> bool:
        """Check if a key is in the forever-approved set."""
        if self._forever_approved_cache is None:
            self._forever_approved_cache = self._load_forever_approvals()
        return key in self._forever_approved_cache

    def _load_forever_approvals(self) -> set[str]:
        """Load forever approvals from disk for this project."""
        if not TOOL_APPROVALS_FILE.exists():
            return set()

        try:
            with open(TOOL_APPROVALS_FILE) as f:
                data = json.load(f)
            commands = data.get("projects", {}).get(self.project_id, [])
            return set(commands)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load tool approvals: %s", e)
            return set()

    def _add_forever_approval_to_disk(self, key: str) -> None:
        """Add a key to the forever-approved file."""
        HYPERGOLIC_DIR.mkdir(parents=True, exist_ok=True)

        # Load existing data
        data: dict[str, Any] = {"projects": {}}
        if TOOL_APPROVALS_FILE.exists():
            try:
                with open(TOOL_APPROVALS_FILE) as f:
                    data = json.load(f)
                if "projects" not in data:
                    data["projects"] = {}
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load tool approvals for update: %s", e)

        # Add the new approval
        project_commands = data["projects"].get(self.project_id, [])
        if key not in project_commands:
            project_commands.append(key)
            data["projects"][self.project_id] = project_commands

            try:
                with open(TOOL_APPROVALS_FILE, "w") as f:
                    json.dump(data, f, indent=2)
                logger.info(
                    "Added forever approval for '%s' in project '%s'",
                    key,
                    self.project_id,
                )
            except OSError as e:
                logger.error("Failed to save tool approvals: %s", e)

    def get_approval_key(self, tool_use: ToolUseBlock) -> str | None:
        """Get the approval key for a tool use, if applicable."""
        tool_name = tool_use.name
        tool_input = tool_use.input if isinstance(tool_use.input, dict) else {}
        return _get_approval_key(tool_name, tool_input)
