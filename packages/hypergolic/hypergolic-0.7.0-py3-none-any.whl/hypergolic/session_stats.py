"""
Session statistics tracking.

Tracks token usage, message counts, and tool invocations for an agent session.
This is a domain object independent of any UI layer.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from hypergolic.pricing import ModelPricing


class StatsObserver(Protocol):
    """Protocol for observing stats changes (e.g., for UI updates)."""

    def on_tokens_updated(
        self,
        context_tokens: int,
        output_tokens: int,
        cache_read_tokens: int,
        cache_creation_tokens: int,
        cost_usd: float,
    ) -> None: ...

    def on_stats_updated(
        self, message_count: int, tool_count: int, summarization_count: int
    ) -> None: ...


class UsageLike(Protocol):
    """Protocol for objects with token usage attributes (e.g., API responses)."""

    input_tokens: int
    output_tokens: int


@dataclass
class UsageSnapshot:
    """A snapshot of usage at a point in time (after each API response)."""

    context_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    cost_usd: float

    def to_dict(self) -> dict:
        return {
            "context_tokens": self.context_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "cost_usd": self.cost_usd,
        }


@dataclass
class SessionStats:
    """Tracks statistics for an agent session."""

    # Context window usage (latest request only - shows how full the context is)
    context_tokens: int = 0

    # Cumulative token counts (for cost calculation)
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0

    message_count: int = 0
    tool_count: int = 0
    summarization_count: int = 0

    observer: StatsObserver | None = field(default=None, repr=False)

    # Pricing configuration
    _pricing: ModelPricing | None = field(default=None, repr=False)

    # Usage snapshots taken after each API response
    _usage_snapshots: list[UsageSnapshot] = field(default_factory=list, repr=False)

    @property
    def pricing(self) -> ModelPricing:
        if self._pricing is None:
            from hypergolic.pricing import DEFAULT_PRICING

            self._pricing = DEFAULT_PRICING
        return self._pricing

    @pricing.setter
    def pricing(self, value: ModelPricing) -> None:
        self._pricing = value

    @property
    def cost_usd(self) -> float:
        """Calculate total session cost in USD."""
        return self.pricing.calculate_cost(
            input_tokens=0,  # Input tokens aren't cumulative, don't include
            output_tokens=self.output_tokens,
            cache_read_tokens=self.cache_read_tokens,
            cache_creation_tokens=self.cache_creation_tokens,
        )

    def add_usage(self, usage: UsageLike | None) -> None:
        if usage is None:
            return

        # Context tokens = input_tokens + cache_read (total context window size)
        # input_tokens is non-cached input, cache_read is cached input
        input_tokens = getattr(usage, "input_tokens", 0) or 0
        cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
        self.context_tokens = input_tokens + cache_read

        # These are cumulative
        self.output_tokens += getattr(usage, "output_tokens", 0) or 0
        self.cache_read_tokens += getattr(usage, "cache_read_input_tokens", 0) or 0
        self.cache_creation_tokens += (
            getattr(usage, "cache_creation_input_tokens", 0) or 0
        )

        # Record a snapshot after each API response
        self._usage_snapshots.append(
            UsageSnapshot(
                context_tokens=self.context_tokens,
                output_tokens=self.output_tokens,
                cache_read_tokens=self.cache_read_tokens,
                cache_creation_tokens=self.cache_creation_tokens,
                cost_usd=self.cost_usd,
            )
        )

        self._notify_tokens()

    def get_latest_snapshot(self) -> UsageSnapshot | None:
        """Get the most recent usage snapshot, or None if no API calls yet."""
        return self._usage_snapshots[-1] if self._usage_snapshots else None

    def get_all_snapshots(self) -> list[UsageSnapshot]:
        """Get all usage snapshots for analysis."""
        return list(self._usage_snapshots)

    def increment_message_count(self, count: int = 1) -> None:
        self.message_count += count
        self._notify_stats()

    def increment_tool_count(self, count: int = 1) -> None:
        self.tool_count += count
        self._notify_stats()

    def increment_summarization_count(self) -> None:
        self.summarization_count += 1
        self._notify_stats()

    def reset(self) -> None:
        self.context_tokens = 0
        self.output_tokens = 0
        self.cache_read_tokens = 0
        self.cache_creation_tokens = 0
        self.message_count = 0
        self.tool_count = 0
        self.summarization_count = 0
        self._usage_snapshots.clear()

        self._notify_tokens()
        self._notify_stats()

    def _notify_tokens(self) -> None:
        if self.observer:
            self.observer.on_tokens_updated(
                self.context_tokens,
                self.output_tokens,
                self.cache_read_tokens,
                self.cache_creation_tokens,
                self.cost_usd,
            )

    def _notify_stats(self) -> None:
        if self.observer:
            self.observer.on_stats_updated(
                self.message_count, self.tool_count, self.summarization_count
            )

    def to_dict(self) -> dict:
        return {
            "context_tokens": self.context_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "cost_usd": self.cost_usd,
            "message_count": self.message_count,
            "tool_count": self.tool_count,
            "summarization_count": self.summarization_count,
        }
