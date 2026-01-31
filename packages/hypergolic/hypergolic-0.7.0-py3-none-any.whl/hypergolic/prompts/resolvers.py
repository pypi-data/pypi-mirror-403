from pathlib import Path
from typing import Any, cast

from anthropic.types import CacheControlEphemeralParam, MessageParam, TextBlockParam

from hypergolic.config import PROJECT_PROMPT_FILENAME, USER_PROMPT_PATH
from hypergolic.session_context import SessionContext

BUILTIN_PROMPTS_DIR = Path(__file__).parent

EPHEMERAL_CACHE: CacheControlEphemeralParam = {"type": "ephemeral"}

# Threshold for truncating tool results from prior turns (in bytes)
# Results larger than this will be replaced with a placeholder
TOOL_RESULT_TRUNCATION_THRESHOLD = 1000


def _read_optional_prompt(path: Path) -> str | None:
    if path.is_file():
        return path.read_text().strip() or None
    return None


def build_operator_system_prompt(
    session_context: SessionContext,
) -> list[TextBlockParam]:
    blocks: list[TextBlockParam] = []

    base_prompt = (BUILTIN_PROMPTS_DIR / "system_prompt.md").read_text().strip()
    blocks.append({"type": "text", "text": base_prompt})

    user_content = _read_optional_prompt(USER_PROMPT_PATH)
    user_section = f"<!-- USER PROMPT -->\n{user_content or 'None'}"
    blocks.append({"type": "text", "text": user_section})

    project_path = session_context.worktree_root / PROJECT_PROMPT_FILENAME
    project_content = _read_optional_prompt(project_path)
    project_section = f"<!-- PROJECT PROMPT -->\n{project_content or 'None'}"
    blocks.append({"type": "text", "text": project_section})

    session_section = f"<!--SESSION CONTEXT -->\n{session_context.model_dump()}"
    blocks.append({"type": "text", "text": session_section})

    return blocks


def build_code_reviewer_system_prompt(
    session_context: SessionContext | None = None,
) -> list[TextBlockParam]:
    prompt = (
        (BUILTIN_PROMPTS_DIR / "code_reviewer_system_prompt.md").read_text().strip()
    )
    blocks: list[TextBlockParam] = [{"type": "text", "text": prompt}]

    if session_context:
        context_section = f"""<!-- SESSION CONTEXT -->
Worktree root: {session_context.worktree_root}
Project root: {session_context.project_root}
Agent branch: {session_context.agent_branch}
Original branch: {session_context.original_branch}"""
        blocks.append({"type": "text", "text": context_section, "cache_control": EPHEMERAL_CACHE})
    else:
        # Add cache control to the last block
        blocks[0]["cache_control"] = EPHEMERAL_CACHE

    return blocks


def update_message_cache_headers(messages: list[MessageParam]) -> None:
    """Rolling cache breakpoint: only the last message gets cache_control."""
    for message in messages:
        content = message["content"]
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    item_dict = cast(dict[str, Any], item)
                    if "cache_control" in item_dict:
                        del item_dict["cache_control"]

    if messages:
        last_content = messages[-1]["content"]
        if isinstance(last_content, list) and len(last_content) > 0:
            last_item = last_content[-1]
            if isinstance(last_item, dict):
                item_dict = cast(dict[str, Any], last_item)
                item_dict["cache_control"] = EPHEMERAL_CACHE


def truncate_prior_tool_results(
    messages: list[MessageParam],
    threshold: int = TOOL_RESULT_TRUNCATION_THRESHOLD,
) -> None:
    """
    Truncate large tool results from prior turns to reduce token usage.

    Tool results are only needed for the LLM to make decisions in the turn
    they're returned. In subsequent turns, a placeholder is sufficient -
    the LLM can re-call the tool if it needs the full content again.

    This modifies messages in-place. Only the last user message (current turn)
    is preserved intact.

    Args:
        messages: List of messages to process (modified in-place)
        threshold: Results larger than this (in bytes) will be truncated
    """
    if len(messages) < 2:
        return

    # Find the last user message index (current turn - don't truncate)
    last_user_idx = None
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            last_user_idx = i
            break

    # Process all user messages except the last one
    for i, message in enumerate(messages):
        if message.get("role") != "user":
            continue
        if i == last_user_idx:
            continue

        content = message.get("content")
        if not isinstance(content, list):
            continue

        # Process each content block
        new_content = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                truncated = _maybe_truncate_tool_result(block, threshold)
                new_content.append(truncated)
            else:
                new_content.append(block)

        message["content"] = new_content


def _maybe_truncate_tool_result(block: dict[str, Any], threshold: int) -> dict[str, Any]:
    """
    Truncate a tool_result block if it exceeds the threshold.

    Preserves: tool_use_id, type, is_error
    Replaces: content with a placeholder indicating size
    """
    inner_content = block.get("content")
    content_size = _estimate_content_size(inner_content)

    if content_size <= threshold:
        return block

    # Don't truncate error results - they're usually small and important
    if block.get("is_error"):
        return block

    # Create truncated version
    size_kb = content_size / 1024
    placeholder = f"[Tool result truncated - {size_kb:.1f}KB. Re-call tool if needed.]"

    return {
        "type": "tool_result",
        "tool_use_id": block.get("tool_use_id"),
        "content": placeholder,
    }


def _estimate_content_size(content: Any) -> int:
    """Estimate the size of tool result content in bytes."""
    if content is None:
        return 0
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        total = 0
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    total += len(item.get("text", ""))
                elif item.get("type") == "image":
                    # Base64 images - estimate from source data
                    source = item.get("source", {})
                    data = source.get("data", "")
                    total += len(data)
            elif isinstance(item, str):
                total += len(item)
        return total
    return len(str(content))
