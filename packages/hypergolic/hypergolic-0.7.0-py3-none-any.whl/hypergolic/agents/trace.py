"""Sub-agent trace data structures for capturing execution history."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from hypergolic.agents.roles import AgentRole


def _serialize_datetime(dt: datetime | None) -> str | None:
    """Serialize datetime to ISO format string."""
    return dt.isoformat() if dt else None


@dataclass
class ToolCallRecord:
    """Record of a single tool call made by a sub-agent."""

    tool_name: str
    tool_input: dict[str, Any]
    tool_output: str
    started_at: datetime
    completed_at: datetime | None = None

    @property
    def duration_ms(self) -> int | None:
        """Duration of the tool call in milliseconds."""
        if self.completed_at is None:
            return None
        delta = self.completed_at - self.started_at
        return int(delta.total_seconds() * 1000)

    def serialize(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "tool_output": self.tool_output,
            "started_at": _serialize_datetime(self.started_at),
            "completed_at": _serialize_datetime(self.completed_at),
            "duration_ms": self.duration_ms,
        }


@dataclass
class SubAgentTrace:
    """Complete trace of a sub-agent execution.

    Captures all tool calls, text output, and metadata for a sub-agent run.
    This allows the UI to show what happened during sub-agent execution
    even after the task completes.
    """

    role: AgentRole
    context: str  # e.g., "main → feature-branch" for code review
    initial_prompt: str  # The prompt that started the sub-agent
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None

    # Accumulated data
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    final_output: str = ""
    error: str | None = None

    @property
    def is_complete(self) -> bool:
        return self.completed_at is not None

    @property
    def is_error(self) -> bool:
        return self.error is not None

    @property
    def duration_ms(self) -> int | None:
        """Total duration of the sub-agent run in milliseconds."""
        if self.completed_at is None:
            return None
        delta = self.completed_at - self.started_at
        return int(delta.total_seconds() * 1000)

    def add_tool_call(self, tool_name: str, tool_input: dict[str, Any]) -> ToolCallRecord:
        """Start tracking a new tool call."""
        record = ToolCallRecord(
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output="",
            started_at=datetime.now(),
        )
        self.tool_calls.append(record)
        return record

    def complete_tool_call(self, result: str) -> None:
        """Complete the most recent tool call with its result."""
        if self.tool_calls:
            self.tool_calls[-1].tool_output = result
            self.tool_calls[-1].completed_at = datetime.now()

    def mark_complete(self, final_output: str) -> None:
        """Mark the sub-agent as successfully completed."""
        self.final_output = final_output
        self.completed_at = datetime.now()

    def mark_error(self, error: str) -> None:
        """Mark the sub-agent as failed with an error."""
        self.error = error
        self.completed_at = datetime.now()

    def serialize(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict with full message history."""
        # Build message history structure
        messages: list[dict[str, Any]] = []

        # Initial user prompt
        if self.initial_prompt:
            messages.append({
                "role": "user",
                "content": self.initial_prompt,
            })

        # Tool calls and results
        for record in self.tool_calls:
            # Assistant's tool use
            messages.append({
                "role": "assistant",
                "content": [{
                    "type": "tool_use",
                    "name": record.tool_name,
                    "input": record.tool_input,
                }],
            })
            # Tool result
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "output": record.tool_output,
                }],
            })

        # Final assistant response
        if self.final_output:
            messages.append({
                "role": "assistant",
                "content": self.final_output,
            })

        return {
            "role": self.role.value if hasattr(self.role, "value") else str(self.role),
            "context": self.context,
            "started_at": _serialize_datetime(self.started_at),
            "completed_at": _serialize_datetime(self.completed_at),
            "duration_ms": self.duration_ms,
            "is_complete": self.is_complete,
            "is_error": self.is_error,
            "error": self.error,
            "tool_calls": [tc.serialize() for tc in self.tool_calls],
            "messages": messages,
        }
