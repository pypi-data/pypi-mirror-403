from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam, TextBlockParam, ToolUnionParam

from hypergolic.tools.cancellation import CancellationToken


class StreamState(Enum):
    IDLE = auto()
    STREAMING = auto()
    CANCELLED = auto()
    COMPLETED = auto()
    ERROR = auto()


@dataclass
class StreamingConfig:
    messages: list[MessageParam]
    system_prompt: list[TextBlockParam]
    tools: list[ToolUnionParam]
    model: str
    max_tokens: int


@dataclass
class StreamingController:
    client: AsyncAnthropic
    cancellation_token: CancellationToken | None = None
    _state: StreamState = field(default=StreamState.IDLE, init=False)

    @property
    def state(self) -> StreamState:
        return self._state

    @property
    def is_active(self) -> bool:
        return self._state == StreamState.STREAMING

    def cancel(self) -> None:
        if self.cancellation_token:
            self.cancellation_token.cancel()

    def reset(self) -> None:
        self._state = StreamState.IDLE
        self.cancellation_token = None

    async def stream(self, config: StreamingConfig) -> AsyncIterator[tuple[str, Any]]:
        """Yields (event_type, data) tuples: "text", "complete", "cancelled", or "error"."""
        self._state = StreamState.STREAMING

        try:
            async with self.client.messages.stream(
                max_tokens=config.max_tokens,
                messages=config.messages,
                model=config.model,
                tools=config.tools,
                system=config.system_prompt,
            ) as stream:
                async for event in stream:
                    if (
                        self.cancellation_token
                        and self.cancellation_token.is_cancelled()
                    ):
                        self._state = StreamState.CANCELLED
                        yield ("cancelled", await stream.get_final_message())
                        return

                    if event.type == "text":
                        yield ("text", event.snapshot)  # type: ignore[attr-defined]

                response = await stream.get_final_message()
                self._state = StreamState.COMPLETED
                yield ("complete", response)

        except Exception as e:
            self._state = StreamState.ERROR
            yield ("error", e)
