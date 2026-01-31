from __future__ import annotations

import os
from typing import TYPE_CHECKING

from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from hypergolic.config import HypergolicConfig


class Provider(BaseModel):
    api_key: str
    endpoint: str
    model: str
    max_tokens: int = Field(default=8192)


def get_default_provider() -> Provider:
    return Provider(
        api_key=os.environ["HYPERGOLIC_API_KEY"],
        endpoint=os.environ["HYPERGOLIC_BASE_URL"],
        model=os.environ["HYPERGOLIC_MODEL"],
    )


def build_provider_client(config: HypergolicConfig) -> AsyncAnthropic:
    return AsyncAnthropic(
        api_key=config.provider.api_key,
        base_url=config.provider.endpoint,
    )
