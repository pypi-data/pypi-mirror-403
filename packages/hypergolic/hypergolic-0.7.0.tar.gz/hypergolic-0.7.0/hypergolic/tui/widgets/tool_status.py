from rich.markup import escape
from textual.widgets import Static


class ToolExecutingStatus(Static):
    DEFAULT_CSS = """
    ToolExecutingStatus {
        background: #1e2a3a;
        border: solid #22d3ee;
        padding: 0 1;
        margin: 1 0;
        height: auto;
        color: #e2e8f0;
    }
    """

    def __init__(self, tool_name: str, details: str = "", **kwargs):
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.details = details

    def render(self) -> str:
        if self.details:
            return f"⚡ Executing: {escape(self.tool_name)} - {escape(self.details)}"
        return f"⚡ Executing: {escape(self.tool_name)}"


class ToolDeniedStatus(Static):
    DEFAULT_CSS = """
    ToolDeniedStatus {
        background: #2d1f1f;
        border: solid #f87171;
        padding: 0 1;
        margin: 1 0;
        height: auto;
        color: #fca5a5;
    }
    """

    def __init__(self, tool_name: str, denial_message: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.denial_message = denial_message

    def render(self) -> str:
        if self.denial_message:
            return f"❌ Tool denied: {escape(self.tool_name)} - {escape(self.denial_message)}"
        return f"❌ Tool denied: {escape(self.tool_name)}"
