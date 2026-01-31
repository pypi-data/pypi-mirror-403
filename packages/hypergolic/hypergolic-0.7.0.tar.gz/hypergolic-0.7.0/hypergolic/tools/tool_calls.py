import json
from collections.abc import Iterable
from typing import Any

from anthropic.types import MessageParam, TextBlock, ToolResultBlockParam, ToolUseBlock
from anthropic.types.tool_result_block_param import Content

from hypergolic.config import HypergolicConfig
from hypergolic.session_context import SessionContext
from hypergolic.tools.browser import (
    BrowserToolInput,
    browser_control,
)
from hypergolic.tools.cancellation import CancellationToken
from hypergolic.tools.command_line import CommandLineToolInput, issue_cmd
from hypergolic.tools.enums import ToolName
from hypergolic.tools.file_explorer import FileExplorerToolInput, file_explorer
from hypergolic.tools.file_operations import FileOperationsToolInput, file_operations
from hypergolic.tools.git import GitToolInput, git_operation
from hypergolic.tools.lsp import LSPToolInput, lsp_operation
from hypergolic.tools.merge_branch import merge_branch
from hypergolic.tools.read_file import ReadFileToolInput, read_file
from hypergolic.tools.screenshot import (
    ScreenshotToolInput,
    take_screenshot,
)
from hypergolic.tools.search_files import SearchFilesToolInput, search_files
from hypergolic.tools.window_management import (
    WindowManagementToolInput,
    window_management,
)


class ToolCallDenied(Exception):
    pass


class ToolCallCancelled(Exception):
    pass


def format_tool_input(tool_use: ToolUseBlock) -> str:
    try:
        return json.dumps(tool_use.input, indent=2)
    except (TypeError, ValueError):
        return str(tool_use.input)


def extract_tool_result_text(tool_result_message: MessageParam) -> str | None:
    content_list = tool_result_message.get("content", [])
    if not content_list:
        return None

    text_parts = []
    for content_block in content_list:
        if isinstance(content_block, dict):
            if content_block.get("type") == "tool_result":
                inner_content = content_block.get("content", [])
                if isinstance(inner_content, str):
                    text_parts.append(inner_content)
                elif isinstance(inner_content, list):
                    for item in inner_content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif isinstance(item, TextBlock):
                            text_parts.append(item.text)

    return "\n".join(text_parts) if text_parts else None


def handle_tool_call(
    client: Any,  # AsyncAnthropic, but we don't use it for most tools
    config: HypergolicConfig,
    tool_use: ToolUseBlock,
    session_context: SessionContext,
    cancellation_token: CancellationToken | None = None,
) -> MessageParam:
    """Handle a tool call synchronously. Called from asyncio.to_thread().

    Note: Code review is handled separately via the sub-agent system.
    """
    try:
        if cancellation_token and cancellation_token.is_cancelled():
            raise ToolCallCancelled("Tool call cancelled before execution")

        match tool_use.name:
            case ToolName.COMMAND_LINE:
                cmd_params = CommandLineToolInput(**tool_use.input)  # type: ignore
                content: Iterable[Content] = issue_cmd(
                    cmd_params, cancellation_token=cancellation_token
                )
            case ToolName.FILE_OPERATIONS:
                file_ops_params = FileOperationsToolInput(**tool_use.input)  # type: ignore
                content: Iterable[Content] = file_operations(
                    params=file_ops_params, session_context=session_context
                )
            case ToolName.GIT:
                git_params = GitToolInput(**tool_use.input)  # type: ignore
                content: Iterable[Content] = git_operation(
                    params=git_params, session_context=session_context
                )
            case ToolName.LSP:
                lsp_params = LSPToolInput(**tool_use.input)  # type: ignore
                content: Iterable[Content] = lsp_operation(lsp_params)
            case ToolName.SCREENSHOT:
                screenshot_params = ScreenshotToolInput(**tool_use.input)  # type: ignore
                content: Iterable[Content] = take_screenshot(screenshot_params)
            case ToolName.CODE_REVIEW:
                # Code review is now handled via sub-agent, not here
                # This case should not be reached in normal operation
                content = [{"type": "text", "text": "Code review should be handled via sub-agent system"}]
            case ToolName.MERGE_BRANCH:
                content: Iterable[Content] = merge_branch(
                    session_context=session_context
                )
            case ToolName.FILE_EXPLORER:
                file_explorer_params = FileExplorerToolInput(**tool_use.input)  # type: ignore
                content: Iterable[Content] = file_explorer(file_explorer_params)
            case ToolName.READ_FILE:
                read_file_params = ReadFileToolInput(**tool_use.input)  # type: ignore
                content: Iterable[Content] = read_file(read_file_params)
            case ToolName.SEARCH_FILES:
                search_files_params = SearchFilesToolInput(**tool_use.input)  # type: ignore
                content: Iterable[Content] = search_files(search_files_params)
            case ToolName.WINDOW_MANAGEMENT:
                window_params = WindowManagementToolInput(**tool_use.input)  # type: ignore
                content: Iterable[Content] = window_management(window_params)
            case _:
                raise Exception(f"Tool not found: {tool_use.name}")

        if cancellation_token and cancellation_token.is_cancelled():
            raise ToolCallCancelled("Tool call cancelled after execution")

    except ToolCallCancelled:
        raise
    except Exception as e:
        error_content = (
            f"Tool call {tool_use.id} ({tool_use.name}) failed. Error: {str(e)}"
        )
        content_block: ToolResultBlockParam = {
            "type": "tool_result",
            "tool_use_id": tool_use.id,
            "content": [{"type": "text", "text": error_content}],
        }
        return {"role": "user", "content": [content_block]}

    content_block: ToolResultBlockParam = {
        "type": "tool_result",
        "tool_use_id": tool_use.id,
        "content": content,
    }

    return {
        "role": "user",
        "content": [content_block],
    }


async def handle_async_tool_call(
    tool_use: ToolUseBlock,
    session_context: SessionContext,
) -> MessageParam:
    """Handle async tool calls (browser, etc.)."""
    try:
        match tool_use.name:
            case ToolName.BROWSER:
                browser_params = BrowserToolInput(**tool_use.input)  # type: ignore
                content: Iterable[Content] = await browser_control(browser_params)
            case _:
                raise Exception(f"Unknown async tool: {tool_use.name}")

    except Exception as e:
        error_content = (
            f"Tool call {tool_use.id} ({tool_use.name}) failed. Error: {str(e)}"
        )
        content_block: ToolResultBlockParam = {
            "type": "tool_result",
            "tool_use_id": tool_use.id,
            "content": [{"type": "text", "text": error_content}],
        }
        return {"role": "user", "content": [content_block]}

    content_block: ToolResultBlockParam = {
        "type": "tool_result",
        "tool_use_id": tool_use.id,
        "content": content,
    }

    return {
        "role": "user",
        "content": [content_block],
    }


def create_denied_tool_result(
    tool_use: ToolUseBlock, denial_message: str | None = None
) -> MessageParam:
    if denial_message:
        content = f"Tool call was denied by the user. Reason: {denial_message}"
    else:
        content = "Tool call was denied by the user."

    content_block: ToolResultBlockParam = {
        "type": "tool_result",
        "tool_use_id": tool_use.id,
        "content": content,
        "is_error": True,
    }

    return {
        "role": "user",
        "content": [content_block],
    }
