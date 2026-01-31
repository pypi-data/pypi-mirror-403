from typing import cast

from anthropic.types import MessageParam, ToolResultBlockParam, ToolUseBlock


def find_tool_use_ids_in_message(message: MessageParam) -> set[str]:
    tool_ids: set[str] = set()
    content = message.get("content", [])

    if not isinstance(content, list):
        return tool_ids

    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            tool_id = block.get("id")
            if tool_id:
                tool_ids.add(tool_id)
        elif isinstance(block, ToolUseBlock):
            tool_ids.add(block.id)

    return tool_ids


def find_tool_result_ids_in_message(message: MessageParam) -> set[str]:
    result_ids: set[str] = set()
    content = message.get("content", [])

    if not isinstance(content, list):
        return result_ids

    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_result":
            tool_use_id = block.get("tool_use_id")
            if tool_use_id:
                result_ids.add(tool_use_id)

    return result_ids


def find_incomplete_tool_uses(messages: list[MessageParam]) -> set[str]:
    all_tool_use_ids: set[str] = set()
    all_tool_result_ids: set[str] = set()

    for message in messages:
        role = message.get("role")
        if role == "assistant":
            all_tool_use_ids.update(find_tool_use_ids_in_message(message))
        elif role == "user":
            all_tool_result_ids.update(find_tool_result_ids_in_message(message))

    return all_tool_use_ids - all_tool_result_ids


def create_interrupt_tool_results(
    incomplete_tool_ids: set[str],
) -> list[ToolResultBlockParam]:
    return [
        {
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": "Tool execution was interrupted by user",
            "is_error": True,
        }
        for tool_id in incomplete_tool_ids
    ]


def create_interrupt_user_message(user_text: str) -> MessageParam:
    interrupt_notice = (
        "[USER INTERRUPT] The user has interrupted your previous response. "
        "Any tool calls that were in progress have been cancelled. "
        "Please acknowledge the interruption and address the user's new message:\n\n"
    )

    return {
        "role": "user",
        "content": [{"type": "text", "text": interrupt_notice + user_text}],
    }


def prepare_interrupted_history(
    messages: list[MessageParam],
    interrupt_message: str,
) -> list[MessageParam]:
    result: list[MessageParam] = list(messages)
    incomplete_ids = find_incomplete_tool_uses(result)

    if incomplete_ids:
        error_results = create_interrupt_tool_results(incomplete_ids)
        error_message = cast(MessageParam, {"role": "user", "content": error_results})
        result.append(error_message)

    result.append(create_interrupt_user_message(interrupt_message))
    return result
