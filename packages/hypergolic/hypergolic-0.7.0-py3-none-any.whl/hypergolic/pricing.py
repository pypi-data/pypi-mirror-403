"""
Model pricing for cost estimation.

Pricing is per million tokens (MTok). Based on Anthropic's pricing page.
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CacheDuration(Enum):
    """Cache duration options for prompt caching."""

    FIVE_MINUTES = "5m"
    ONE_HOUR = "1h"


@dataclass(frozen=True)
class ModelPricing:
    """Pricing structure for a Claude model (USD per million tokens)."""

    input_tokens: float
    output_tokens: float
    cache_write_5m: float
    cache_write_1h: float
    cache_read: float

    def calculate_cost(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_creation_tokens: int = 0,
        cache_duration: CacheDuration = CacheDuration.FIVE_MINUTES,
    ) -> float:
        """
        Calculate the total cost in USD for token usage.

        Args:
            input_tokens: Non-cached input tokens
            output_tokens: Output tokens generated
            cache_read_tokens: Tokens read from cache (cache hits)
            cache_creation_tokens: Tokens written to cache
            cache_duration: Cache duration tier for write pricing

        Returns:
            Total cost in USD
        """
        cache_write_rate = (
            self.cache_write_5m
            if cache_duration == CacheDuration.FIVE_MINUTES
            else self.cache_write_1h
        )

        # Convert to millions and multiply by rate
        cost = (
            (input_tokens / 1_000_000) * self.input_tokens
            + (output_tokens / 1_000_000) * self.output_tokens
            + (cache_read_tokens / 1_000_000) * self.cache_read
            + (cache_creation_tokens / 1_000_000) * cache_write_rate
        )

        return cost


# Model pricing constants (USD per million tokens)
# Source: https://docs.anthropic.com/en/docs/about-claude/pricing
# Last verified: 2025-01-27

CLAUDE_OPUS_4 = ModelPricing(
    input_tokens=15.0,
    output_tokens=75.0,
    cache_write_5m=18.75,
    cache_write_1h=30.0,
    cache_read=1.50,
)

CLAUDE_OPUS_4_5 = ModelPricing(
    input_tokens=15.0,
    output_tokens=75.0,
    cache_write_5m=18.75,
    cache_write_1h=30.0,
    cache_read=1.50,
)

CLAUDE_SONNET_4 = ModelPricing(
    input_tokens=3.0,
    output_tokens=15.0,
    cache_write_5m=3.75,
    cache_write_1h=6.0,
    cache_read=0.30,
)

CLAUDE_SONNET_4_5 = ModelPricing(
    input_tokens=3.0,
    output_tokens=15.0,
    cache_write_5m=3.75,
    cache_write_1h=6.0,
    cache_read=0.30,
)

CLAUDE_HAIKU_3_5 = ModelPricing(
    input_tokens=0.80,
    output_tokens=4.0,
    cache_write_5m=1.0,
    cache_write_1h=1.6,
    cache_read=0.08,
)

# Model family to pricing mapping (matched by substring)
_MODEL_FAMILIES: list[tuple[str, ModelPricing]] = [
    # Order matters: more specific patterns first
    ("opus-4-5", CLAUDE_OPUS_4_5),
    ("opus-4.5", CLAUDE_OPUS_4_5),
    ("opus-4", CLAUDE_OPUS_4),
    ("sonnet-4-5", CLAUDE_SONNET_4_5),
    ("sonnet-4.5", CLAUDE_SONNET_4_5),
    ("sonnet-4", CLAUDE_SONNET_4),
    ("haiku-3-5", CLAUDE_HAIKU_3_5),
    ("haiku-3.5", CLAUDE_HAIKU_3_5),
    ("haiku", CLAUDE_HAIKU_3_5),
]

# Default pricing (Opus 4.5)
DEFAULT_PRICING = CLAUDE_OPUS_4_5


def get_pricing(model_name: str | None = None) -> ModelPricing:
    """
    Get pricing for a model by name.

    Matches model names by looking for known family substrings.
    E.g., "claude-opus-4-5-20250520" matches "opus-4-5" -> CLAUDE_OPUS_4_5

    Args:
        model_name: Model identifier. If None, returns default pricing.

    Returns:
        ModelPricing for the requested model, or default if not found.
    """
    if model_name is None:
        return DEFAULT_PRICING

    model_lower = model_name.lower()

    # Match against known model families (order matters for specificity)
    for pattern, pricing in _MODEL_FAMILIES:
        if pattern in model_lower:
            return pricing

    logger.warning(f"Unknown model '{model_name}', using default (Opus 4.5) pricing")
    return DEFAULT_PRICING
