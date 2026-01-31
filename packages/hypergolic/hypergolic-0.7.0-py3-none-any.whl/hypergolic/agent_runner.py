"""
AgentRunner orchestrates the agentic conversation loop.

This module owns the business logic for:
- Submitting user messages and starting API streaming
- Processing API responses and tool execution
- Handling user interrupts mid-turn
- Deciding when to continue the loop vs. finish a turn

The TUI layer should only handle presentation concerns and forward
user actions to the runner.
"""

import asyncio
import logging
from enum import Enum, auto
from typing import TYPE_CHECKING, Protocol

from anthropic import AsyncAnthropic
from anthropic.types import Message, MessageParam, TextBlockParam, ToolUnionParam

from hypergolic.config import HypergolicConfig
from hypergolic.summarization import (
    SummarizationAction,
    SummarizationConfig,
    SummarizationManager,
    format_summary_as_user_message,
    generate_context_summary,
)
from hypergolic.tools.cancellation import CancellationToken

if TYPE_CHECKING:
    from hypergolic.conversation_manager import ConversationManager
    from hypergolic.session_stats import SessionStats
    from hypergolic.tui.streaming import StreamingController
    from hypergolic.tui.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


class AgentState(Enum):
    IDLE = auto()
    STREAMING = auto()
    PROCESSING_TOOLS = auto()
    INTERRUPTED = auto()
    SUMMARIZING = auto()


class AgentRunnerCallbacks(Protocol):
    """UI-agnostic callbacks for the agent loop."""

    def on_streaming_start(self) -> None:
        """Called when streaming is about to start."""
        ...

    def on_stream_text(self, text: str) -> None:
        """Called with accumulated text during streaming."""
        ...

    def on_stream_complete(self, response: Message) -> None:
        """Called when streaming finishes successfully."""
        ...

    def on_stream_error(self, error: Exception) -> None:
        """Called when streaming encounters an error."""
        ...

    def on_stream_cancelled(self) -> None:
        """Called when streaming is cancelled (not interrupted)."""
        ...

    def on_turn_complete(self) -> None:
        """Called when the entire turn (including tools) is complete."""
        ...

    def on_summarization_suggested(self) -> None:
        """Called when context size suggests summarization (soft threshold)."""
        ...

    def on_summarization_started(self) -> None:
        """Called when summarization begins."""
        ...

    def on_summarization_complete(self, formatted_summary: str) -> None:
        """Called when summarization finishes with the formatted summary message."""
        ...


class AgentRunner:
    """Orchestrates the agent conversation loop."""

    def __init__(
        self,
        client: AsyncAnthropic,
        config: HypergolicConfig,
        system_prompt: list[TextBlockParam],
        tools: list[ToolUnionParam],
        conversation: ConversationManager,
        stats: SessionStats,
        tool_executor: ToolExecutor,
        streaming: StreamingController,
        callbacks: AgentRunnerCallbacks,
    ):
        self._client = client
        self._config = config
        self._system_prompt = system_prompt
        self._tools = tools
        self._conversation = conversation
        self._stats = stats
        self._tool_executor = tool_executor
        self._streaming = streaming
        self._callbacks = callbacks

        self._state = AgentState.IDLE
        self._pending_interrupt: str | None = None
        self._current_task: asyncio.Task[None] | None = None
        self._summarization = SummarizationManager(
            SummarizationConfig(),
            auto_approve_config=config.auto_summarize,
        )
        self._pending_summarization = False
        self._last_input_tokens = 0

    @property
    def state(self) -> AgentState:
        return self._state

    @property
    def is_busy(self) -> bool:
        return self._state != AgentState.IDLE

    @property
    def conversation(self) -> ConversationManager:
        return self._conversation

    @property
    def stats(self) -> SessionStats:
        return self._stats

    @property
    def messages(self) -> list[MessageParam]:
        return self._conversation.messages

    def submit_message(self, message: str) -> None:
        """User submits a message - starts the agent loop."""
        self._conversation.add_user_message(message)
        self._start_agent_loop()

    def interrupt(self, message: str) -> None:
        """User interrupts with a new message."""
        self._pending_interrupt = message
        self._state = AgentState.INTERRUPTED
        self._streaming.cancel()
        self._tool_executor.interrupt()

    def cancel(self) -> None:
        """Cancel current operation without providing a new message."""
        self._streaming.cancel()
        self._tool_executor.interrupt()
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()

    def _start_agent_loop(self) -> None:
        """Start the async agent loop as a task."""
        self._current_task = asyncio.create_task(self._run_agent_loop())

    async def _run_agent_loop(self) -> None:
        """Main agent loop - streams responses and processes tools until done."""
        try:
            while True:
                if self._pending_interrupt:
                    self._process_interrupt()
                    continue

                response = await self._stream_response()

                if self._pending_interrupt:
                    self._process_interrupt()
                    continue

                self._conversation.add_agent_response(response)
                self._callbacks.on_stream_complete(response)

                # Check context size and handle summarization
                self._last_input_tokens = response.usage.input_tokens
                summarization_action = self._summarization.check_context_size(
                    self._last_input_tokens
                )

                if summarization_action == SummarizationAction.SUGGEST:
                    # Mark for summarization at turn end
                    self._pending_summarization = True

                # Process tools if any
                should_continue = await self._process_tools(response)

                if self._pending_interrupt:
                    self._process_interrupt()
                    continue

                if not should_continue:
                    break

            # At end of turn, handle suggested summarization
            if self._pending_summarization:
                self._pending_summarization = False
                if self._summarization.should_auto_approve:
                    # Auto-approve: perform summarization immediately
                    await self._perform_summarization()
                else:
                    # Prompt user
                    self._callbacks.on_summarization_suggested()

            self._finish_turn()

        except asyncio.CancelledError:
            if self._pending_interrupt:
                # Restart the loop to handle the interrupt
                self._process_interrupt()
                self._start_agent_loop()
            else:
                self._callbacks.on_stream_cancelled()
                self._state = AgentState.IDLE
        except Exception as e:
            logger.exception("Agent loop error: %s", e)
            self._callbacks.on_stream_error(e)
            self._state = AgentState.IDLE

    async def _stream_response(self) -> Message:
        """Execute the streaming API call."""
        from hypergolic.tui.streaming import StreamingConfig

        self._state = AgentState.STREAMING
        self._streaming.cancellation_token = CancellationToken()
        self._callbacks.on_streaming_start()

        # Get messages for API (may be subset if summarized)
        api_messages = self._conversation.prepare_for_api_call()

        config = StreamingConfig(
            messages=api_messages,
            system_prompt=self._system_prompt,
            tools=self._tools,
            model=self._config.provider.model,
            max_tokens=self._config.provider.max_tokens,
        )

        final_response: Message | None = None

        async for event_type, data in self._streaming.stream(config):
            if event_type == "text":
                self._callbacks.on_stream_text(data)
            elif event_type == "complete":
                final_response = data
            elif event_type == "cancelled":
                raise asyncio.CancelledError()
            elif event_type == "error":
                raise data

        if final_response is None:
            raise RuntimeError("Stream completed without a response")

        return final_response

    async def _process_tools(self, response: Message) -> bool:
        """Process tool calls in response. Returns True if loop should continue."""
        self._state = AgentState.PROCESSING_TOOLS
        return await self._tool_executor.process_response(response)

    def _process_interrupt(self) -> None:
        """Process a pending interrupt."""
        if not self._pending_interrupt:
            self._finish_turn()
            return

        interrupt_message = self._pending_interrupt
        self._pending_interrupt = None

        self._tool_executor.reset()
        self._conversation.handle_interrupt(interrupt_message)
        # Continue the loop - it will stream again

    def _finish_turn(self) -> None:
        """Complete the current turn.

        Note: This is called from within _run_agent_loop, so we don't cancel
        _current_task here (it will complete naturally).
        """
        self._state = AgentState.IDLE
        self._tool_executor.reset()
        self._callbacks.on_turn_complete()

    def reset(self) -> None:
        """Reset the runner state."""
        self._state = AgentState.IDLE
        self._pending_interrupt = None
        self._pending_summarization = False
        self._tool_executor.reset()
        self._summarization.reset()
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
        self._current_task = None

    async def _perform_summarization(self) -> None:
        """Perform context summarization."""
        self._state = AgentState.SUMMARIZING
        self._callbacks.on_summarization_started()

        try:
            # Generate summary from current epoch's messages
            summary = await generate_context_summary(
                client=self._client,
                messages=self._conversation.messages,
                message_metas=self._conversation.message_metas,
                current_index=self._conversation.current_summarization_index,
                model=self._config.provider.model,
            )

            # Format and add as a new message (increments epoch)
            formatted_summary = format_summary_as_user_message(summary)
            self._conversation.add_summary_message(formatted_summary)

            # Update summarization manager's epoch tracking
            self._summarization.increment_epoch()

            # Notify UI
            self._callbacks.on_summarization_complete(formatted_summary)

            logger.info(
                "Context summarized. Previous input tokens: %d, new epoch: %d",
                self._last_input_tokens,
                self._conversation.current_summarization_index,
            )
        except Exception as e:
            logger.exception("Summarization failed: %s", e)
            raise
        finally:
            self._state = AgentState.IDLE

    async def summarize_now(self) -> None:
        """Manually trigger summarization (called from UI)."""
        if self._state != AgentState.IDLE:
            logger.warning("Cannot summarize while agent is busy")
            return
        await self._perform_summarization()

    def set_auto_summarize_session(self, value: bool) -> None:
        """Set session-level auto-summarize (user selected 'Always')."""
        self._summarization.set_session_auto_approve(value)
