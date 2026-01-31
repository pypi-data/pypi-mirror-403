import json
import logging
from datetime import datetime
from typing import Any

from anthropic.types import MessageParam

from hypergolic.session_context import SessionContext
from hypergolic.session_db import save_session as save_session_to_db
from hypergolic.summarization import MessageMeta

logger = logging.getLogger(__name__)

# Content truncation settings for log files
MAX_CONTENT_LENGTH = 500  # Truncate content longer than this
TRUNCATION_SUFFIX = "...[truncated]"


class SessionHistoryManager:
    """
    Manages session history persistence.

    Stores sessions in SQLite database. Handles both initial saves and
    appending segments (used when summarization occurs mid-session).
    """

    def __init__(self, session_context: SessionContext):
        self.session_context = session_context
        self._session_id: str | None = None
        self._segments: list[dict[str, Any]] = []
        self._metadata: dict[str, Any] = {}

    @property
    def session_id(self) -> str | None:
        return self._session_id

    def save(
        self,
        messages: list[MessageParam],
        stats: dict[str, Any],
        sub_agent_traces: dict[str, dict[str, Any]] | None = None,
        usage_snapshots: list[dict[str, Any]] | None = None,
        message_metas: list[MessageMeta] | None = None,
    ) -> str | None:
        """
        Save session history to SQLite database.

        Always saves all messages (no segmentation). Message metadata tracks
        which summarization epoch each message belongs to.

        Args:
            messages: Conversation messages to save
            stats: Final session statistics
            sub_agent_traces: Optional traces from sub-agents
            usage_snapshots: List of usage snapshots, one per API response
            message_metas: Metadata for each message (summarization index, etc.)

        Returns:
            Session ID if saved, None if no messages
        """
        if not messages:
            return None

        now = datetime.now()

        # Always create/update as a single session with all messages
        self._create_or_update_session(
            messages, stats, sub_agent_traces, now, usage_snapshots, message_metas
        )

        # Save to database
        save_session_to_db(self._session_id, self._metadata, self._segments)  # type: ignore[arg-type]
        logger.info("Saved session to database: %s", self._session_id)
        return self._session_id

    def _create_or_update_session(
        self,
        messages: list[MessageParam],
        stats: dict[str, Any],
        sub_agent_traces: dict[str, dict[str, Any]] | None,
        now: datetime,
        usage_snapshots: list[dict[str, Any]] | None = None,
        message_metas: list[MessageMeta] | None = None,
    ) -> None:
        """Create or update session with all messages."""
        if not self._session_id:
            timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
            session_suffix = self.session_context.agent_branch.split("-")[-1]
            self._session_id = f"{timestamp}_{self.session_context.project_name}_{session_suffix}"

        self._metadata = {
            "timestamp": now.isoformat(),
            "project": self.session_context.project_name,
            "branch": self.session_context.agent_branch,
            "original_branch": self.session_context.original_branch,
            "base_commit": self.session_context.base_commit,
            "git_root": str(self.session_context.worktree_root),
            "remote_url": self.session_context.remote_url,
        }

        formatted_messages = format_messages_with_snapshots(
            messages, usage_snapshots, message_metas
        )

        segment: dict[str, Any] = {
            "segment_index": 0,
            "timestamp": now.isoformat(),
            "stats": stats,
            "messages": formatted_messages,
        }

        if sub_agent_traces:
            segment["sub_agent_traces"] = sub_agent_traces

        self._segments = [segment]


def save_session_history(
    session_context: SessionContext,
    messages: list[MessageParam],
    stats: dict[str, Any],
    sub_agent_traces: dict[str, dict[str, Any]] | None = None,
) -> str | None:
    """
    Legacy function for simple session saves.

    For new code that needs summarization support, use SessionHistoryManager instead.
    """
    manager = SessionHistoryManager(session_context)
    return manager.save(messages, stats, sub_agent_traces)


def format_messages_with_snapshots(
    messages: list[MessageParam],
    usage_snapshots: list[dict[str, Any]] | None = None,
    message_metas: list[MessageMeta] | None = None,
) -> list[dict[str, Any]]:
    """
    Format messages, attaching usage snapshots and metadata.

    Each assistant message corresponds to one API response, so we pair
    them with snapshots in order.
    """
    formatted = []
    snapshot_index = 0
    snapshots = usage_snapshots or []
    metas = message_metas or []

    for i, msg in enumerate(messages):
        role = msg.get("role", "unknown")
        meta = metas[i] if i < len(metas) else None

        # Attach snapshot to assistant messages (each = one API call)
        if role == "assistant" and snapshot_index < len(snapshots):
            formatted.append(format_message(msg, snapshots[snapshot_index], meta))
            snapshot_index += 1
        else:
            formatted.append(format_message(msg, None, meta))

    return formatted


def format_message(
    message: MessageParam,
    usage_snapshot: dict[str, Any] | None = None,
    meta: MessageMeta | None = None,
) -> dict[str, Any]:
    role = message.get("role", "unknown")
    content = message.get("content", [])

    formatted: dict[str, Any] = {"role": role}

    if usage_snapshot:
        formatted["usage_snapshot"] = usage_snapshot

    if meta:
        formatted["meta"] = meta.to_dict()

    if isinstance(content, str):
        content_length = len(content)
        formatted["content_length"] = content_length
        formatted["content"] = truncate_text(content)
        return formatted

    formatted["content"] = []
    total_length = 0
    for block in content:
        formatted_block, block_length = format_content_block(block)
        formatted["content"].append(formatted_block)
        total_length += block_length
    formatted["content_length"] = total_length

    return formatted


def truncate_text(text: str) -> str:
    """Truncate text if it exceeds MAX_CONTENT_LENGTH."""
    if len(text) <= MAX_CONTENT_LENGTH:
        return text
    return text[:MAX_CONTENT_LENGTH] + TRUNCATION_SUFFIX


def format_content_block(block: Any) -> tuple[dict[str, Any], int]:
    """Format a content block, returning (formatted_block, content_length)."""
    if isinstance(block, dict):
        return format_dict_block(block)

    block_type = getattr(block, "type", None)

    if block_type == "text":
        text = block.text
        return {
            "type": "text",
            "text": truncate_text(text),
            "content_length": len(text),
        }, len(text)

    if block_type == "tool_use":
        input_str = json.dumps(block.input) if block.input else ""
        return {
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": block.input,
        }, len(input_str)

    if block_type == "tool_result":
        return format_tool_result_block(block)

    raw = str(block)
    return {"type": block_type or "unknown", "raw": truncate_text(raw)}, len(raw)


def format_dict_block(block: dict) -> tuple[dict[str, Any], int]:
    """Format a dict content block, returning (formatted_block, content_length)."""
    block_type = block.get("type")

    if block_type == "text":
        text = block.get("text", "")
        return {
            "type": "text",
            "text": truncate_text(text),
            "content_length": len(text),
        }, len(text)

    if block_type == "tool_use":
        input_data = block.get("input")
        input_str = json.dumps(input_data) if input_data else ""
        return {
            "type": "tool_use",
            "id": block.get("id"),
            "name": block.get("name"),
            "input": input_data,
        }, len(input_str)

    if block_type == "tool_result":
        return format_tool_result_dict_block(block)

    # Unknown block type - return as-is with estimated length
    block_str = json.dumps(block)
    return block, len(block_str)


def format_tool_result_dict_block(block: dict) -> tuple[dict[str, Any], int]:
    """Format a tool_result dict block with truncation."""
    content = block.get("content")
    content_length = 0
    truncated_content = content

    if isinstance(content, str):
        content_length = len(content)
        truncated_content = truncate_text(content)
    elif isinstance(content, list):
        truncated_content = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text", "")
                content_length += len(text)
                truncated_content.append({
                    "type": "text",
                    "text": truncate_text(text),
                    "content_length": len(text),
                })
            else:
                item_str = str(item)
                content_length += len(item_str)
                truncated_content.append(item)

    return {
        "type": "tool_result",
        "tool_use_id": block.get("tool_use_id"),
        "content": truncated_content,
        "content_length": content_length,
        "is_error": block.get("is_error", False),
    }, content_length


def format_tool_result_block(block: Any) -> tuple[dict[str, Any], int]:
    """Format a tool_result block with truncation, returning (formatted, length)."""
    content = getattr(block, "content", None)
    content_length = 0
    formatted_content: Any = content

    if isinstance(content, str):
        content_length = len(content)
        formatted_content = truncate_text(content)
    elif isinstance(content, list):
        formatted_content = []
        for item in content:
            if hasattr(item, "type") and item.type == "text":
                text = item.text
                content_length += len(text)
                formatted_content.append({
                    "type": "text",
                    "text": truncate_text(text),
                    "content_length": len(text),
                })
            else:
                item_str = str(item)
                content_length += len(item_str)
                formatted_content.append(item_str)

    return {
        "type": "tool_result",
        "tool_use_id": block.tool_use_id,
        "content": formatted_content,
        "content_length": content_length,
        "is_error": getattr(block, "is_error", False),
    }, content_length
