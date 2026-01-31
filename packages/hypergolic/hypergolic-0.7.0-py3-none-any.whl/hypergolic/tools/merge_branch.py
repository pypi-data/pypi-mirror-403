from anthropic.types import ToolParam
from anthropic.types.tool_result_block_param import Content

from hypergolic.session_context import SessionContext
from hypergolic.tools.enums import ToolName
from hypergolic.version_control import (
    branch_has_changes,
    merge_agent_branch,
)

MergeBranchTool: ToolParam = {
    "name": ToolName.MERGE_BRANCH,
    "description": "Merge the current agent session branch into the original branch. Use this after a successful code review to apply your changes. This will merge the agent branch and clean it up.",
    "input_schema": {
        "type": "object",
        "properties": {},
    },
}


def merge_branch(session_context: SessionContext) -> list[Content]:
    if not branch_has_changes(session_context):
        return [
            {
                "type": "text",
                "text": "No changes to merge. The agent branch has no commits beyond the base.",
            }
        ]

    merge_result = merge_agent_branch(session_context)

    if merge_result.success:
        return [
            {
                "type": "text",
                "text": f"✅ Successfully merged {session_context.agent_branch} into {session_context.original_branch}.",
            }
        ]
    else:
        return [
            {
                "type": "text",
                "text": f"❌ Failed to merge {session_context.agent_branch} into {session_context.original_branch}. {merge_result.error_message or 'Unknown error'}. The branch has been preserved for manual resolution.",
            }
        ]
