"""
Context window summarization management.

Handles automatic summarization when the context window grows too large,
preventing API errors and maintaining conversation quality.

Key design principles:
- Summarization is a checkpoint, not a replacement
- All messages are preserved in memory and saved to the database
- Only summary + messages since summary are sent to the LLM
- Multiple summarizations chain: new summary includes prior summary content
"""

import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam, TextBlock

from hypergolic.prompts.paths import SUMMARIZE_CONTEXT_PROMPT_PATH

logger = logging.getLogger(__name__)


class SummarizationAction(Enum):
    """Action to take based on context size."""

    NONE = auto()
    SUGGEST = auto()  # Threshold hit - prompt user (or auto-approve)


@dataclass
class SummarizationConfig:
    """Configuration for context summarization thresholds."""

    # Threshold: suggest/trigger summarization
    # Lower than before since we're being more proactive
    threshold: int = 80_000


@dataclass
class MessageMeta:
    """Metadata for tracking message state in summarization."""

    summarization_index: int = 0  # Which epoch this message belongs to
    is_summary: bool = False  # Is this a summarization checkpoint message

    def to_dict(self) -> dict[str, Any]:
        return {
            "summarization_index": self.summarization_index,
            "is_summary": self.is_summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MessageMeta:
        return cls(
            summarization_index=data.get("summarization_index", 0),
            is_summary=data.get("is_summary", False),
        )


@dataclass
class SummarizationState:
    """Tracks the current summarization state for a conversation."""

    current_index: int = 0  # Current summarization epoch
    auto_approve_session: bool = False  # User selected "Always" for this session

    def increment(self) -> None:
        """Move to next summarization epoch."""
        self.current_index += 1


class SummarizationManager:
    """Manages context window summarization decisions."""

    def __init__(
        self,
        config: SummarizationConfig | None = None,
        auto_approve_config: bool = False,
    ):
        self.config = config or SummarizationConfig()
        self.state = SummarizationState()
        # Config-level auto-approve (from env var)
        self._auto_approve_config = auto_approve_config

    @property
    def should_auto_approve(self) -> bool:
        """Check if summarization should auto-approve."""
        return self._auto_approve_config or self.state.auto_approve_session

    @property
    def current_index(self) -> int:
        """Current summarization epoch."""
        return self.state.current_index

    def set_session_auto_approve(self, value: bool) -> None:
        """Set session-level auto-approve (user selected 'Always')."""
        self.state.auto_approve_session = value

    def check_context_size(self, input_tokens: int) -> SummarizationAction:
        """
        Check if summarization is needed based on input token count.

        Args:
            input_tokens: The input_tokens from the most recent API response

        Returns:
            SummarizationAction indicating what action to take
        """
        if input_tokens >= self.config.threshold:
            logger.info(
                "Context size %d exceeds threshold %d, suggesting summarization",
                input_tokens,
                self.config.threshold,
            )
            return SummarizationAction.SUGGEST

        return SummarizationAction.NONE

    def increment_epoch(self) -> None:
        """Increment the summarization epoch after a summary is created."""
        self.state.increment()

    def reset(self) -> None:
        """Reset state for a new session."""
        self.state = SummarizationState()


async def generate_context_summary(
    client: AsyncAnthropic,
    messages: list[MessageParam],
    message_metas: list[MessageMeta],
    current_index: int,
    model: str,
) -> str:
    """
    Generate a summary of the conversation for context window management.

    Only summarizes messages from the current epoch (since last summary).
    If there's a prior summary, it's included in the content to summarize.

    Args:
        client: The Anthropic client
        messages: All conversation messages
        message_metas: Metadata for each message
        current_index: Current summarization epoch
        model: The model to use for summarization

    Returns:
        A structured summary string
    """
    # Get messages from current epoch only
    messages_to_summarize = [
        msg
        for msg, meta in zip(messages, message_metas, strict=True)
        if meta.summarization_index == current_index
    ]

    if not messages_to_summarize:
        return "No messages to summarize."

    logger.info(
        "Generating context summary for %d messages (epoch %d) using model %s",
        len(messages_to_summarize),
        current_index,
        model,
    )

    system_prompt = SUMMARIZE_CONTEXT_PROMPT_PATH.read_text().strip()

    # Convert messages to a transcript string
    transcript = format_messages_as_transcript(messages_to_summarize)

    if not transcript.strip():
        logger.warning("No content found in messages to summarize")
        return "No content to summarize."

    # Wrap transcript in a single user message to prevent the model
    # from continuing the conversation instead of summarizing it
    summary_request: list[MessageParam] = [
        {"role": "user", "content": f"Please summarize this conversation:\n\n{transcript}"}
    ]

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=4096,  # Allow longer summaries for context preservation
            system=system_prompt,
            messages=summary_request,
        )
    except Exception as e:
        logger.exception("Failed to generate context summary: %s", e)
        raise

    logger.info(
        "Summary generated: stop_reason=%s, usage=%s",
        response.stop_reason,
        response.usage,
    )

    text_parts = [
        block.text for block in response.content if isinstance(block, TextBlock)
    ]

    if text_parts:
        return "\n\n".join(text_parts)

    logger.warning("Summary generation returned no text content")
    return "Summary generation failed - no content returned."


def format_messages_as_transcript(messages: list[MessageParam]) -> str:
    """
    Convert messages to a transcript string suitable for summarization.

    Extracts text content and provides summaries of tool calls/results.
    """
    lines: list[str] = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        text = _extract_text_from_content(content)

        if not text.strip():
            continue

        prefix = "USER" if role == "user" else "ASSISTANT"
        lines.append(f"{prefix}: {text}")

    return "\n\n".join(lines)


def _extract_text_from_content(content: Any) -> str:
    """Extract text content from a message content field."""
    if isinstance(content, str):
        return content

    text_parts = []
    for block in content:
        if isinstance(block, dict):
            block_type = block.get("type")
            if block_type == "text":
                text_parts.append(block.get("text", ""))
            elif block_type == "tool_use":
                tool_name = block.get("name", "unknown")
                text_parts.append(f"[Called tool: {tool_name}]")
            elif block_type == "tool_result":
                result_content = block.get("content", "")
                if isinstance(result_content, str):
                    # Truncate long tool results
                    if len(result_content) > 500:
                        result_content = result_content[:500] + "...[truncated]"
                    text_parts.append(f"[Tool result: {result_content}]")
        elif hasattr(block, "type"):
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                text_parts.append(f"[Called tool: {block.name}]")

    return "\n".join(text_parts)


def format_summary_as_user_message(summary: str) -> str:
    """Format the summary as a user message for the continued conversation."""
    return f"""# Context Summary (Checkpoint)

This is a summarization checkpoint. The full conversation history is preserved in the UI
but only this summary and subsequent messages are sent to the LLM for token efficiency.

If this summary is insufficient for the current task, feel free to explore—use `git diff`,
`git log`, file reads, etc. to recover any needed context. Prefer to work with available
information rather than re-exploring unless necessary.

---

{summary}

---

*The conversation continues from here.*"""
