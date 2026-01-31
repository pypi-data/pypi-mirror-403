from datetime import datetime

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Collapsible, Markdown, Static

from hypergolic.tui.widgets.token_usage import TokenUsage


class SummaryMessage(Vertical):
    """A collapsible summary checkpoint message.

    Shows "Conversation summarized (click to expand)" when collapsed,
    and the full summary content when expanded.
    """

    DEFAULT_CSS = """
    SummaryMessage {
        background: #1e2d3d;
        border: solid #0ea5e9;
        padding: 0 1;
        margin: 1 0;
        height: auto;
    }

    SummaryMessage Collapsible {
        border: none;
        padding: 0;
    }

    SummaryMessage CollapsibleTitle {
        color: #38bdf8;
        text-style: bold;
        padding: 0;
    }

    SummaryMessage .content {
        padding: 0 1;
        color: #e2e8f0;
    }
    """

    def __init__(self, content: str, timestamp: datetime | None = None):
        super().__init__()
        self.content = content
        self.timestamp = timestamp or datetime.now()

    def compose(self) -> ComposeResult:
        time_str = self.timestamp.strftime("%I:%M:%S %p")
        title = f"📋 Conversation summarized │ {time_str} (click to expand)"
        with Collapsible(title=title, collapsed=True):
            yield Markdown(self.content, classes="content")


class MessageHeader(Static):
    interrupted = reactive(False)

    def __init__(
        self,
        role: str,
        timestamp: datetime | None = None,
        interrupted: bool = False,
        token_usage: TokenUsage | None = None,
    ):
        super().__init__()
        self.role = role
        self.timestamp = timestamp or datetime.now()
        self.interrupted = interrupted
        self.token_usage = token_usage

    def render(self) -> str:
        time_str = self.timestamp.strftime("%I:%M:%S %p")
        usage_str = ""
        if self.token_usage:
            formatted = self.token_usage.format_header()
            if formatted:
                usage_str = f" │ {formatted}"

        if self.role == "user":
            return f"👤 You │ {time_str}"
        else:
            suffix = " [interrupted]" if self.interrupted else ""
            return f"🤖 Agent │ {time_str}{usage_str}{suffix}"

    def set_token_usage(self, usage: TokenUsage) -> None:
        self.token_usage = usage
        self.refresh()


class UserMessage(Vertical):
    DEFAULT_CSS = """
    UserMessage {
        background: #1e3a5f;
        border: solid #3b82f6;
        padding: 0 1;
        margin: 1 0;
        height: auto;
    }

    UserMessage.interrupt {
        border: solid #fbbf24;
        background: #2d2a1f;
    }

    UserMessage MessageHeader {
        color: #60a5fa;
        text-style: bold;
        height: 1;
        padding: 0;
    }

    UserMessage.interrupt MessageHeader {
        color: #fbbf24;
    }

    UserMessage .content {
        padding: 0 1;
        color: #e2e8f0;
    }
    """

    def __init__(
        self,
        content: str,
        timestamp: datetime | None = None,
        is_interrupt: bool = False,
    ):
        super().__init__()
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.is_interrupt = is_interrupt

    def compose(self) -> ComposeResult:
        if self.is_interrupt:
            self.add_class("interrupt")
        yield MessageHeader("user", self.timestamp)
        yield Static(self.content, classes="content")


class AgentMessage(Vertical):
    DEFAULT_CSS = """
    AgentMessage {
        background: #1a1a2e;
        border: solid #6366f1;
        padding: 0 1;
        margin: 1 0;
        height: auto;
    }

    AgentMessage.interrupted {
        border: solid #fbbf24;
    }

    AgentMessage MessageHeader {
        color: #a5b4fc;
        text-style: bold;
        height: 1;
        padding: 0;
    }

    AgentMessage.interrupted MessageHeader {
        color: #fbbf24;
    }

    AgentMessage .content {
        padding: 0 1;
        color: #e2e8f0;
    }
    """

    content_text = reactive("", recompose=False)

    def __init__(
        self,
        content: str = "",
        timestamp: datetime | None = None,
        token_usage: TokenUsage | None = None,
    ):
        super().__init__()
        self.content_text = content
        self.timestamp = timestamp or datetime.now()
        self.token_usage = token_usage
        self._markdown_widget: Markdown | None = None
        self._header: MessageHeader | None = None
        self._interrupted = False

    def compose(self) -> ComposeResult:
        self._header = MessageHeader(
            "agent", self.timestamp, self._interrupted, self.token_usage
        )
        yield self._header
        self._markdown_widget = Markdown(self.content_text, classes="content")
        yield self._markdown_widget

    def update_content(self, text: str) -> None:
        self.content_text = text
        if self._markdown_widget:
            self._markdown_widget.update(text)

    def set_token_usage(self, usage: TokenUsage) -> None:
        self.token_usage = usage
        if self._header:
            self._header.set_token_usage(usage)

    def mark_interrupted(self) -> None:
        """Mark this message as interrupted."""
        self._interrupted = True
        self.add_class("interrupted")

        # Update the header to show interrupted state
        if self._header:
            self._header.interrupted = True

        # Update the content to show it was interrupted
        if self._markdown_widget:
            current = self.content_text
            if current and not current.endswith("\n\n*[interrupted]*"):
                self._markdown_widget.update(current + "\n\n*[interrupted]*")


class ConversationView(ScrollableContainer):
    DEFAULT_CSS = """
    ConversationView {
        height: 1fr;
        padding: 0 1;
        scrollbar-gutter: stable;
    }
    """

    def add_user_message(self, content: str, is_interrupt: bool = False) -> UserMessage:
        message = UserMessage(content, is_interrupt=is_interrupt)
        self.mount(message)
        self.scroll_end(animate=False)
        return message

    def add_agent_message(self, content: str = "") -> AgentMessage:
        message = AgentMessage(content)
        self.mount(message)
        self.scroll_end(animate=False)
        return message

    def add_summary_message(self, content: str) -> SummaryMessage:
        message = SummaryMessage(content)
        self.mount(message)
        self.scroll_end(animate=False)
        return message

    def clear(self) -> None:
        for child in list(self.children):
            child.remove()
