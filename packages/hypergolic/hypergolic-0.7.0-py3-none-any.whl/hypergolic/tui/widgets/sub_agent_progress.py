"""Widget for displaying sub-agent progress inline in conversation."""

import json
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Markdown, Static, TabbedContent, TabPane

from hypergolic.agents.roles import AgentRole
from hypergolic.agents.sub_agent import SubAgentCallbacks
from hypergolic.agents.trace import SubAgentTrace, ToolCallRecord


class ToolActivity(Static):
    """Shows a single tool call activity."""

    DEFAULT_CSS = """
    ToolActivity {
        height: auto;
        padding: 0 1;
        color: #94a3b8;
    }

    ToolActivity.active {
        color: #fbbf24;
    }

    ToolActivity.complete {
        color: #4ade80;
    }
    """

    def __init__(self, tool_name: str, details: str = ""):
        super().__init__()
        self.tool_name = tool_name
        self.details = details
        self._complete = False

    def compose(self) -> ComposeResult:
        return []

    def render(self) -> str:
        icon = "✓" if self._complete else "◆"
        detail_str = f": {self.details}" if self.details else ""
        return f"{icon} {self.tool_name}{detail_str}"

    def mark_complete(self) -> None:
        self._complete = True
        self.remove_class("active")
        self.add_class("complete")
        self.refresh()


class SubAgentDetailScreen(ModalScreen[None]):
    """Modal screen showing full sub-agent trace details."""

    BINDINGS = [
        Binding("escape", "dismiss_screen", "Close", show=True),
        Binding("q", "dismiss_screen", "Close", show=False),
    ]

    DEFAULT_CSS = """
    SubAgentDetailScreen {
        align: center middle;
    }

    SubAgentDetailScreen > Vertical {
        width: 90%;
        height: 90%;
        max-width: 140;
        background: #1e1e2e;
        border: solid #6366f1;
    }

    SubAgentDetailScreen .header {
        dock: top;
        height: 3;
        background: #1e293b;
        border-bottom: solid #334155;
        padding: 1 2;
    }

    SubAgentDetailScreen .header-title {
        width: 1fr;
        color: #818cf8;
        text-style: bold;
    }

    SubAgentDetailScreen .header-hint {
        width: auto;
        color: #64748b;
    }

    SubAgentDetailScreen .tab-content {
        padding: 1 2;
    }

    SubAgentDetailScreen .output-content {
        padding: 1;
    }

    SubAgentDetailScreen .trace-item {
        height: auto;
        margin: 0 0 1 0;
        padding: 1;
        background: #0f172a;
        border: solid #334155;
    }

    SubAgentDetailScreen .trace-tool-name {
        color: #4ade80;
        text-style: bold;
    }

    SubAgentDetailScreen .trace-tool-input {
        color: #94a3b8;
        padding: 0 0 0 2;
    }

    SubAgentDetailScreen .trace-tool-output {
        color: #e2e8f0;
        padding: 0 0 0 2;
        max-height: 10;
    }

    SubAgentDetailScreen .prompt-content {
        color: #e2e8f0;
        padding: 1;
        background: #0f172a;
        border: solid #334155;
    }

    SubAgentDetailScreen TabbedContent {
        height: 1fr;
    }

    SubAgentDetailScreen TabPane {
        padding: 1;
    }
    """

    def __init__(self, trace: SubAgentTrace, **kwargs):
        super().__init__(**kwargs)
        self.trace = trace

    def compose(self) -> ComposeResult:
        role_name = self._get_role_display_name()
        status = "✓ Complete" if self.trace.is_complete and not self.trace.is_error else ""
        if self.trace.is_error:
            status = "✗ Error"

        with Vertical():
            with Horizontal(classes="header"):
                yield Static(f"🤖 {role_name} {status}", classes="header-title")
                yield Static("[Esc] Close", classes="header-hint", markup=False)

            with TabbedContent():
                with TabPane("Output", id="output-tab"):
                    with VerticalScroll(classes="tab-content"):
                        if self.trace.final_output:
                            yield Markdown(self.trace.final_output, classes="output-content")
                        elif self.trace.is_error:
                            yield Static(f"Error: {self.trace.error}", classes="output-content")
                        else:
                            yield Static("(no output yet)", classes="output-content")

                with TabPane(f"Trace ({len(self.trace.tool_calls)})", id="trace-tab"):
                    with VerticalScroll(classes="tab-content"):
                        if self.trace.tool_calls:
                            for record in self.trace.tool_calls:
                                yield from self._compose_trace_item(record)
                        else:
                            yield Static("(no tool calls)", classes="output-content")

                with TabPane("Raw", id="raw-tab"):
                    with VerticalScroll(classes="tab-content"):
                        yield Static(
                            self._serialize_trace_to_json(),
                            classes="prompt-content",
                            markup=False,
                        )

    def _compose_trace_item(self, record: ToolCallRecord) -> ComposeResult:
        """Compose a single tool call trace item."""
        with Vertical(classes="trace-item"):
            # Tool name and timing
            duration = f" ({record.duration_ms}ms)" if record.duration_ms else ""
            yield Static(f"◆ {record.tool_name}{duration}", classes="trace-tool-name")

            # Input summary
            input_summary = self._format_tool_input(record.tool_input)
            if input_summary:
                yield Static(f"→ {input_summary}", classes="trace-tool-input")

            # Output preview
            output = record.tool_output or "(no output)"
            if len(output) > 500:
                output = output[:500] + "..."
            yield Static(output, classes="trace-tool-output", markup=False)

    def _format_tool_input(self, tool_input: dict) -> str:
        """Format tool input for display."""
        if "path" in tool_input:
            return str(tool_input["path"])
        if "paths" in tool_input:
            paths = tool_input["paths"]
            if len(paths) == 1:
                return str(paths[0])
            return f"{len(paths)} files"
        if "pattern" in tool_input:
            return f'search: "{tool_input["pattern"]}"'
        if "cmd" in tool_input:
            return f'$ {tool_input["cmd"]}'
        return ""

    def _get_role_display_name(self) -> str:
        return {
            AgentRole.OPERATOR: "Operator",
            AgentRole.CODE_REVIEWER: "Code Reviewer",
        }.get(self.trace.role, "Agent")

    def _serialize_trace_to_json(self) -> str:
        """Serialize the entire trace history to formatted JSON."""
        # Build the message history structure
        messages: list[dict[str, Any]] = []

        # Initial user prompt
        if self.trace.initial_prompt:
            messages.append({
                "role": "user",
                "content": self.trace.initial_prompt,
            })

        # Tool calls and results
        for record in self.trace.tool_calls:
            # Assistant's tool use
            messages.append({
                "role": "assistant",
                "content": [{
                    "type": "tool_use",
                    "name": record.tool_name,
                    "input": record.tool_input,
                }],
            })
            # Tool result
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "output": record.tool_output,
                }],
            })

        # Final assistant response
        if self.trace.final_output:
            messages.append({
                "role": "assistant",
                "content": self.trace.final_output,
            })

        # Build full trace object
        trace_data = {
            "role": self.trace.role.value if hasattr(self.trace.role, "value") else str(self.trace.role),
            "context": self.trace.context,
            "started_at": self.trace.started_at.isoformat() if self.trace.started_at else None,
            "completed_at": self.trace.completed_at.isoformat() if self.trace.completed_at else None,
            "duration_ms": self.trace.duration_ms,
            "is_complete": self.trace.is_complete,
            "is_error": self.trace.is_error,
            "error": self.trace.error,
            "messages": messages,
        }

        return json.dumps(trace_data, indent=2, default=str)

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)


class SubAgentProgress(Vertical, can_focus=True):
    """Shows progress of a sub-agent task inline in the conversation.

    During execution: shows live progress with tool activity and thinking preview.
    After completion: collapses to a summary that can be expanded to show full trace.
    """

    BINDINGS = [
        Binding("enter", "expand", "View details", show=False),
        Binding("space", "expand", "View details", show=False),
    ]

    DEFAULT_CSS = """
    SubAgentProgress {
        height: auto;
        margin: 1 0;
        padding: 0;
        background: #1a1a2e;
        border: solid #6366f1;
    }

    SubAgentProgress:focus {
        border: solid #a5b4fc;
    }

    SubAgentProgress .progress-header {
        height: auto;
        padding: 1 2;
        background: #1e293b;
        border-bottom: solid #334155;
    }

    SubAgentProgress .progress-title {
        color: #818cf8;
        text-style: bold;
    }

    SubAgentProgress .progress-subtitle {
        color: #64748b;
    }

    SubAgentProgress .activity-section {
        height: auto;
        max-height: 12;
        padding: 1 2;
    }

    SubAgentProgress .activity-placeholder {
        color: #64748b;
        text-style: italic;
    }

    SubAgentProgress .activity-placeholder.hidden {
        display: none;
    }

    SubAgentProgress .thinking-section {
        height: auto;
        max-height: 8;
        padding: 1 2;
        border-top: solid #334155;
    }

    SubAgentProgress .thinking-label {
        color: #fbbf24;
        text-style: italic;
    }

    SubAgentProgress .thinking-text {
        color: #e2e8f0;
        padding: 0 1;
    }

    SubAgentProgress.complete {
        border: solid #22c55e;
    }

    SubAgentProgress.complete:hover {
        border: solid #4ade80;
    }

    SubAgentProgress.error {
        border: solid #ef4444;
    }

    SubAgentProgress.error:hover {
        border: solid #f87171;
    }

    /* Status-specific styling for reviews */
    SubAgentProgress.status-approved {
        border: solid #22c55e;
    }

    SubAgentProgress.status-approved:hover {
        border: solid #4ade80;
    }

    SubAgentProgress.status-denied {
        border: solid #ef4444;
    }

    SubAgentProgress.status-denied:hover {
        border: solid #f87171;
    }

    SubAgentProgress.status-suppressed {
        border: solid #64748b;
    }

    SubAgentProgress.status-suppressed:hover {
        border: solid #94a3b8;
    }

    /* Summary mode styles (after completion) */
    SubAgentProgress.summary-mode .activity-section {
        display: none;
    }

    SubAgentProgress.summary-mode .thinking-section {
        display: none;
    }

    SubAgentProgress .summary-section {
        display: none;
        height: auto;
        max-height: 12;
        padding: 1 2;
    }

    SubAgentProgress.summary-mode .summary-section {
        display: block;
    }

    SubAgentProgress .summary-text {
        color: #e2e8f0;
        height: auto;
        max-height: 8;
    }

    SubAgentProgress .summary-stats {
        color: #94a3b8;
        height: 1;
    }

    SubAgentProgress .expand-hint {
        color: #64748b;
        text-align: right;
        height: 1;
    }

    SubAgentProgress:focus .expand-hint {
        color: #94a3b8;
    }
    """

    current_text = reactive("")

    def __init__(self, trace: SubAgentTrace):
        super().__init__()
        self.trace = trace
        self._activities: list[ToolActivity] = []
        self._thinking_widget: Static | None = None
        self._activity_container: VerticalScroll | None = None
        self._activity_placeholder: Static | None = None
        self._title_widget: Static | None = None
        self._summary_text: Static | None = None
        self._summary_stats: Static | None = None

    def compose(self) -> ComposeResult:
        role_name = self._get_role_display_name()

        with Vertical(classes="progress-header"):
            self._title_widget = Static(
                f"🤖 {role_name} in Progress", classes="progress-title"
            )
            yield self._title_widget
            if self.trace.context:
                yield Static(self.trace.context, classes="progress-subtitle")

        with VerticalScroll(classes="activity-section") as container:
            self._activity_container = container
            self._activity_placeholder = Static(
                "Analyzing changes...", classes="activity-placeholder"
            )
            yield self._activity_placeholder

        with Vertical(classes="thinking-section"):
            yield Static("💭 Thinking...", classes="thinking-label")
            self._thinking_widget = Static("", classes="thinking-text")
            yield self._thinking_widget

        # Summary section (hidden until complete)
        with Vertical(classes="summary-section"):
            self._summary_text = Static("", classes="summary-text")
            yield self._summary_text
            self._summary_stats = Static("", classes="summary-stats")
            yield self._summary_stats
            yield Static("[Enter/Space to view details]", classes="expand-hint")

    def _get_role_display_name(self) -> str:
        return {
            AgentRole.OPERATOR: "Operator",
            AgentRole.CODE_REVIEWER: "Code Reviewer",
        }.get(self.trace.role, "Agent")

    def add_tool_activity(self, tool_name: str, details: str = "") -> ToolActivity:
        """Add a new tool activity indicator."""
        # Hide placeholder on first tool activity
        if self._activity_placeholder and not self._activities:
            self._activity_placeholder.add_class("hidden")

        activity = ToolActivity(tool_name, details)
        activity.add_class("active")
        self._activities.append(activity)
        if self._activity_container:
            self._activity_container.mount(activity)
            self._activity_container.scroll_end(animate=False)
        return activity

    def complete_current_tool(self) -> None:
        """Mark the current tool activity as complete."""
        if self._activities:
            self._activities[-1].mark_complete()

    def update_thinking(self, text: str) -> None:
        """Update the thinking/streaming text preview."""
        self.current_text = text
        if self._thinking_widget:
            # Show last 200 chars as preview
            preview = text[-200:] if len(text) > 200 else text
            if len(text) > 200:
                preview = "..." + preview
            self._thinking_widget.update(preview)

    def mark_complete(self) -> None:
        """Mark the sub-agent as complete and switch to summary mode."""
        self.add_class("complete")
        self._apply_status_class()
        self._switch_to_summary_mode()

    def _apply_status_class(self) -> None:
        """Apply status-specific CSS class based on output content."""
        status = self._detect_status(self.trace.final_output)
        if status:
            self.add_class(f"status-{status}")

    def _detect_status(self, output: str) -> str | None:
        """Detect review status from output text."""
        if not output:
            return None
        first_line = output.strip().split("\n")[0].upper()
        if "APPROVED" in first_line:
            return "approved"
        elif "DENIED" in first_line:
            return "denied"
        elif "SUPPRESSED" in first_line:
            return "suppressed"
        return None

    def mark_error(self, error: str) -> None:
        """Mark the sub-agent as errored and switch to summary mode."""
        self.add_class("error")
        self._switch_to_summary_mode()

    def _truncate_to_lines(self, text: str, max_lines: int = 8) -> str:
        """Truncate text to at most max_lines, adding ellipsis if needed."""
        if not text:
            return ""
        lines = text.strip().split("\n")
        if len(lines) <= max_lines:
            return text.strip()
        truncated = "\n".join(lines[:max_lines])
        return truncated + "\n..."

    def _switch_to_summary_mode(self) -> None:
        """Transform from progress view to summary view."""
        self.add_class("summary-mode")

        role_name = self._get_role_display_name()
        if self.trace.is_error:
            status = "✗ Error"
        else:
            status = "✓ Complete"

        if self._title_widget:
            self._title_widget.update(f"🤖 {role_name} {status}")

        # Update summary text
        if self._summary_text:
            if self.trace.is_error:
                self._summary_text.update(f"Error: {self.trace.error}")
            else:
                # Show preview of final output (limited to ~8 lines)
                preview = self._truncate_to_lines(self.trace.final_output or "", max_lines=8)
                self._summary_text.update(preview)

        # Update stats
        if self._summary_stats:
            tool_count = len(self.trace.tool_calls)
            duration = ""
            if self.trace.duration_ms:
                seconds = self.trace.duration_ms / 1000
                duration = f" │ {seconds:.1f}s"
            self._summary_stats.update(f"{tool_count} tool calls{duration}")

    def action_expand(self) -> None:
        """Open the detail screen to view full trace."""
        self.app.push_screen(SubAgentDetailScreen(self.trace))

    def on_click(self) -> None:
        """Handle click to expand details."""
        if self.trace.is_complete:
            self.action_expand()


class SubAgentProgressCallbacks(SubAgentCallbacks):
    """Bridges sub-agent events to the progress widget and accumulates trace data."""

    def __init__(self, widget: SubAgentProgress):
        self._widget = widget
        self._current_activity: ToolActivity | None = None

    @property
    def trace(self) -> SubAgentTrace:
        """Access the accumulated trace data."""
        return self._widget.trace

    def on_sub_agent_start(self, role: AgentRole) -> None:
        pass  # Widget already shows the role

    def on_sub_agent_text(self, text: str) -> None:
        self._widget.update_thinking(text)

    def on_sub_agent_tool_start(self, tool_name: str, tool_input: dict) -> None:
        # Record in trace
        self._widget.trace.add_tool_call(tool_name, tool_input)

        # Update widget
        details = self._get_tool_details(tool_name, tool_input)
        self._current_activity = self._widget.add_tool_activity(tool_name, details)

    def on_sub_agent_tool_complete(self, tool_name: str, result: str) -> None:
        # Record in trace
        self._widget.trace.complete_tool_call(result)

        # Update widget
        self._widget.complete_current_tool()
        self._current_activity = None

    def on_sub_agent_complete(self, final_text: str) -> None:
        # Record in trace
        self._widget.trace.mark_complete(final_text)

        # Update widget
        self._widget.mark_complete()

    def on_sub_agent_error(self, error: Exception) -> None:
        # Record in trace
        self._widget.trace.mark_error(str(error))

        # Update widget
        self._widget.mark_error(str(error))

    def _get_tool_details(self, tool_name: str, tool_input: dict) -> str:
        """Extract display-friendly details from tool input."""
        if "path" in tool_input:
            return str(tool_input["path"])
        if "paths" in tool_input:
            paths = tool_input["paths"]
            if len(paths) == 1:
                return str(paths[0])
            return f"{len(paths)} files"
        if "pattern" in tool_input:
            return f'"{tool_input["pattern"]}"'
        return ""
