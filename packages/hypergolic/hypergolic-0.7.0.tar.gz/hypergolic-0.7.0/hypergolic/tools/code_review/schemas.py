from anthropic.types import ToolParam
from pydantic import BaseModel

from hypergolic.tools.enums import ToolName

CodeReviewTool: ToolParam = {
    "name": ToolName.CODE_REVIEW,
    "description": "Request a code review for a given branch",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "A summary of the changes performed, including context, goals, and reasoning behind the changes",
            },
            "feature_branch": {
                "type": "string",
                "description": "The branch the agent implemented code on. Eg `agent-2025-12-01-08-33PM__new-auth-system`",
            },
            "base_branch": {
                "type": "string",
                "description": "The original branch to compare against. Eg `main`",
            },
        },
    },
}


class CodeReviewToolInput(BaseModel):
    base_branch: str
    feature_branch: str
    summary: str = ""
