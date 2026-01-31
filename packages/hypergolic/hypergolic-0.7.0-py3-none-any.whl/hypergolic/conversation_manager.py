"""
Conversation history management.

Manages the message history for an agent conversation, including
user messages, agent responses, and tool results. This is a domain
object independent of any UI layer.

Key design: Messages are never deleted. Summarization creates a checkpoint
and only messages from the current epoch (+ the summary) are sent to the LLM.
"""

import copy

from anthropic.types import Message, MessageParam

from hypergolic.agents import prepare_interrupted_history
from hypergolic.prompts.resolvers import (
    truncate_prior_tool_results,
    update_message_cache_headers,
)
from hypergolic.session_stats import SessionStats
from hypergolic.summarization import MessageMeta


class ConversationManager:
    """Manages conversation message history and coordinates with stats tracking."""

    def __init__(self, stats: SessionStats):
        self.stats = stats
        self.messages: list[MessageParam] = []
        self.message_metas: list[MessageMeta] = []
        self._current_summarization_index: int = 0
        self._last_summary_idx: int | None = None  # Index of most recent summary message

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def current_summarization_index(self) -> int:
        return self._current_summarization_index

    @property
    def has_summary(self) -> bool:
        return self._last_summary_idx is not None

    def add_user_message(self, text: str) -> MessageParam:
        message: MessageParam = {
            "role": "user",
            "content": [{"type": "text", "text": text}],
        }
        meta = MessageMeta(summarization_index=self._current_summarization_index)
        self.messages.append(message)
        self.message_metas.append(meta)
        self.stats.increment_message_count()
        return message

    def add_agent_response(self, response: Message) -> MessageParam:
        self.stats.add_usage(response.usage)
        self.stats.increment_message_count()

        message: MessageParam = {
            "role": response.role,
            "content": response.content,
        }
        meta = MessageMeta(summarization_index=self._current_summarization_index)
        self.messages.append(message)
        self.message_metas.append(meta)
        return message

    def add_tool_result(self, result: MessageParam) -> None:
        meta = MessageMeta(summarization_index=self._current_summarization_index)
        self.messages.append(result)
        self.message_metas.append(meta)

    def add_summary_message(self, summary_text: str) -> MessageParam:
        """
        Add a summarization checkpoint message.

        This increments the summarization epoch. Future messages will
        belong to the new epoch, and API calls will only include the
        summary + messages from the new epoch.
        """
        # Increment epoch BEFORE adding the summary message
        # The summary belongs to the NEW epoch
        self._current_summarization_index += 1

        message: MessageParam = {
            "role": "user",
            "content": [{"type": "text", "text": summary_text}],
        }
        meta = MessageMeta(
            summarization_index=self._current_summarization_index,
            is_summary=True,
        )
        self.messages.append(message)
        self.message_metas.append(meta)
        self._last_summary_idx = len(self.messages) - 1
        self.stats.increment_summarization_count()
        return message

    def handle_interrupt(self, interrupt_message: str) -> None:
        # Get messages for API call (summary + current epoch)
        api_messages = self.get_messages_for_api()
        interrupted = prepare_interrupted_history(api_messages, interrupt_message)

        # prepare_interrupted_history can add 1-2 messages:
        # 1. Optional: error results for incomplete tool calls
        # 2. Always: the user interrupt message
        # We need to append all new messages to our history
        new_message_count = len(interrupted) - len(api_messages)
        for new_msg in interrupted[-new_message_count:]:
            meta = MessageMeta(summarization_index=self._current_summarization_index)
            self.messages.append(new_msg)
            self.message_metas.append(meta)

        # Only count the actual user interrupt message
        self.stats.increment_message_count()

    def clear(self) -> None:
        """Clear all messages and reset state."""
        self.messages.clear()
        self.message_metas.clear()
        self._current_summarization_index = 0
        self._last_summary_idx = None
        self.stats.reset()

    def get_messages_for_api(self) -> list[MessageParam]:
        """
        Get messages to send to the LLM.

        If there's been a summarization, returns only:
        - The most recent summary message
        - All messages from the current epoch (after the summary)

        Otherwise returns all messages.
        """
        self._validate_sync()

        if self._last_summary_idx is None:
            # No summarization yet - return all messages
            return self.messages.copy()

        # Return summary + all messages after it
        return self.messages[self._last_summary_idx:].copy()

    def _validate_sync(self) -> None:
        """Validate that messages and metas are in sync."""
        assert len(self.messages) == len(self.message_metas), (
            f"Messages ({len(self.messages)}) and metas ({len(self.message_metas)}) out of sync"
        )

    def prepare_for_api_call(self) -> list[MessageParam]:
        """
        Get messages for API call with optimizations applied.

        Returns the subset of messages that should be sent to the LLM,
        with large tool results from prior turns truncated and cache
        headers updated.

        Uses deep copy to avoid mutating the original messages, which
        are needed for UI display and session history.
        """
        api_messages = self.get_messages_for_api()
        # Deep copy to avoid mutating originals (needed for UI display)
        api_messages = copy.deepcopy(api_messages)
        truncate_prior_tool_results(api_messages)
        update_message_cache_headers(api_messages)
        return api_messages
