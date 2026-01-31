"""Sub-agent runner for orchestrating child agent tasks."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Protocol

from anthropic import AsyncAnthropic
from anthropic.types import Message, MessageParam, TextBlockParam, ToolUnionParam

from hypergolic.agents.roles import AgentRole
from hypergolic.tools.cancellation import CancellationToken

logger = logging.getLogger(__name__)


class SubAgentCallbacks(Protocol):
    """Callbacks for sub-agent progress updates."""

    def on_sub_agent_start(self, role: AgentRole) -> None:
        """Called when sub-agent starts."""
        ...

    def on_sub_agent_text(self, text: str) -> None:
        """Called with accumulated text during streaming."""
        ...

    def on_sub_agent_tool_start(self, tool_name: str, tool_input: dict) -> None:
        """Called when sub-agent starts a tool call."""
        ...

    def on_sub_agent_tool_complete(self, tool_name: str, result: str) -> None:
        """Called when sub-agent completes a tool call."""
        ...

    def on_sub_agent_complete(self, final_text: str) -> None:
        """Called when sub-agent completes successfully."""
        ...

    def on_sub_agent_error(self, error: Exception) -> None:
        """Called when sub-agent encounters an error."""
        ...


class SubAgentToolHandler(Protocol):
    """Protocol for handling sub-agent tool calls."""

    async def handle_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool and return the result as a string."""
        ...


@dataclass
class SubAgentRunner:
    """Runs a sub-agent loop with progress callbacks."""

    client: AsyncAnthropic
    role: AgentRole
    system_prompt: list[TextBlockParam]
    tools: list[ToolUnionParam]
    model: str
    max_tokens: int
    callbacks: SubAgentCallbacks
    tool_handler: SubAgentToolHandler

    cancellation_token: CancellationToken = field(default_factory=CancellationToken)
    _messages: list[MessageParam] = field(default_factory=list)

    async def run(self, initial_prompt: str) -> str:
        """Run the sub-agent loop and return the final text response."""
        self.callbacks.on_sub_agent_start(self.role)

        self._messages = [{"role": "user", "content": initial_prompt}]
        final_text = ""

        try:
            while True:
                if self.cancellation_token.is_cancelled():
                    raise asyncio.CancelledError()

                response = await self._stream_response()

                if self.cancellation_token.is_cancelled():
                    raise asyncio.CancelledError()

                # Extract and accumulate text
                text_content = self._extract_text(response)
                if text_content:
                    final_text = text_content

                # Add assistant response to messages
                self._messages.append({"role": "assistant", "content": response.content})

                # Process tools if any
                has_tools = await self._process_tools(response)

                if not has_tools or response.stop_reason != "tool_use":
                    break

            self.callbacks.on_sub_agent_complete(final_text)
            logger.debug("Sub-agent %s completed successfully", self.role.name)
            return final_text

        except asyncio.CancelledError:
            logger.info("Sub-agent cancelled")
            raise
        except Exception as e:
            logger.exception("Sub-agent error: %s", e)
            self.callbacks.on_sub_agent_error(e)
            raise

    async def _stream_response(self) -> Message:
        """Stream a response from the API."""
        accumulated_text = ""

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            tools=self.tools,
            messages=self._messages,
        ) as stream:
            async for event in stream:
                if self.cancellation_token.is_cancelled():
                    return await stream.get_final_message()

                if event.type == "text":
                    accumulated_text = event.snapshot  # type: ignore[attr-defined]
                    self.callbacks.on_sub_agent_text(accumulated_text)

            return await stream.get_final_message()

    async def _process_tools(self, response: Message) -> bool:
        """Process tool calls in response. Returns True if tools were processed."""
        tool_uses = [block for block in response.content if block.type == "tool_use"]

        if not tool_uses:
            return False

        tool_results = []
        for tool_use in tool_uses:
            if self.cancellation_token.is_cancelled():
                break

            tool_input = tool_use.input if isinstance(tool_use.input, dict) else {}
            self.callbacks.on_sub_agent_tool_start(tool_use.name, tool_input)

            result = await self.tool_handler.handle_tool(tool_use.name, tool_input)

            self.callbacks.on_sub_agent_tool_complete(tool_use.name, result)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result,
            })

        if tool_results:
            self._messages.append({"role": "user", "content": tool_results})

        return True

    def _extract_text(self, response: Message) -> str:
        """Extract text content from response."""
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""

    def cancel(self) -> None:
        """Cancel the sub-agent."""
        self.cancellation_token.cancel()
