import asyncio
from collections.abc import Awaitable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Protocol

from anthropic.types import Message, MessageParam, ToolUseBlock

from hypergolic.tools.approval_manager import ApprovalManager
from hypergolic.tools.enums import ToolName
from hypergolic.tui.widgets.tool_approval import ToolApprovalResult


class ExecutorState(Enum):
    IDLE = auto()
    PROCESSING = auto()
    AWAITING_APPROVAL = auto()
    EXECUTING = auto()
    INTERRUPTED = auto()


@dataclass
class ToolContext:
    tool_use: ToolUseBlock
    tool_name: str = field(init=False)
    tool_input: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        self.tool_name = self.tool_use.name
        self.tool_input = (
            self.tool_use.input if isinstance(self.tool_use.input, dict) else {}
        )

    @property
    def tool_id(self) -> str:
        return self.tool_use.id

    def get_display_details(self) -> str:
        match self.tool_name:
            case ToolName.FILE_EXPLORER | ToolName.READ_FILE:
                return str(self.tool_input.get("path", ""))
            case ToolName.GIT | ToolName.FILE_OPERATIONS:
                return str(self.tool_input.get("operation", ""))
            case ToolName.SEARCH_FILES:
                return str(self.tool_input.get("pattern", ""))
            case ToolName.BROWSER:
                op = self.tool_input.get("operation", "")
                url = self.tool_input.get("url", "")
                return f"{op} {url}".strip() if url else op
            case _:
                return ""


class ToolExecutorCallbacks(Protocol):
    def on_tool_requires_approval(
        self,
        context: ToolContext,
    ) -> Awaitable[ToolApprovalResult | None]: ...

    def on_tool_executing(self, context: ToolContext) -> None: ...

    def execute_tool(self, context: ToolContext) -> Awaitable[MessageParam]: ...

    def on_tool_completed(self, context: ToolContext, result: MessageParam) -> None: ...

    def on_tool_error(self, context: ToolContext, error: Exception) -> None: ...

    def on_tool_denied(self, context: ToolContext, message: str | None) -> None: ...

    def on_tool_interrupted(self, context: ToolContext) -> None: ...


@dataclass
class ToolExecutor:
    callbacks: ToolExecutorCallbacks
    approval_manager: ApprovalManager

    _state: ExecutorState = field(default=ExecutorState.IDLE, init=False)
    _current_context: ToolContext | None = field(default=None, init=False)

    @property
    def state(self) -> ExecutorState:
        return self._state

    @property
    def current_tool(self) -> ToolContext | None:
        return self._current_context

    @property
    def is_busy(self) -> bool:
        return self._state not in (ExecutorState.IDLE, ExecutorState.INTERRUPTED)

    async def process_response(self, response: Message) -> bool:
        """Process all tool calls in response. Returns True if agent loop should continue."""
        self._state = ExecutorState.PROCESSING

        tool_uses = [block for block in response.content if block.type == "tool_use"]

        if not tool_uses:
            self._state = ExecutorState.IDLE
            return False

        for tool_use in tool_uses:
            if self._state == ExecutorState.INTERRUPTED:
                return False

            await self._handle_tool(tool_use)

        self._state = ExecutorState.IDLE
        return response.stop_reason == "tool_use"

    def interrupt(self) -> None:
        self._state = ExecutorState.INTERRUPTED
        if self._current_context:
            self.callbacks.on_tool_interrupted(self._current_context)
        self._current_context = None

    def reset(self) -> None:
        self._state = ExecutorState.IDLE
        self._current_context = None

    async def _handle_tool(self, tool_use: ToolUseBlock) -> None:
        context = ToolContext(tool_use)
        self._current_context = context

        needs_approval = self.approval_manager.requires_approval(tool_use)

        if needs_approval:
            self._state = ExecutorState.AWAITING_APPROVAL
            result = await self.callbacks.on_tool_requires_approval(context)
            if result is None or not result.approved:
                denial_message = result.denial_message if result else None
                self.callbacks.on_tool_denied(context, denial_message)
                self._current_context = None
                return

        await self._execute_tool(context)
        self._current_context = None

    async def _execute_tool(self, context: ToolContext) -> None:
        self._state = ExecutorState.EXECUTING
        self.callbacks.on_tool_executing(context)

        try:
            result = await self.callbacks.execute_tool(context)
            if self._state != ExecutorState.INTERRUPTED:
                self.callbacks.on_tool_completed(context, result)
        except asyncio.CancelledError:
            self.callbacks.on_tool_interrupted(context)
            raise
        except Exception as e:
            self.callbacks.on_tool_error(context, e)
