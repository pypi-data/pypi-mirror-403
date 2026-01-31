from rich.syntax import Syntax
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Static

from hypergolic.version_control import FileDiff, FileStatus, MergeDiffData


class DiffSummaryBar(Static):
    DEFAULT_CSS = """
    DiffSummaryBar {
        height: 3;
        padding: 1 2;
        background: #1e293b;
        border-bottom: solid #334155;
    }

    DiffSummaryBar .summary-text {
        color: #e2e8f0;
    }
    """

    def __init__(self, diff_data: MergeDiffData, **kwargs):
        super().__init__(**kwargs)
        self.diff_data = diff_data

    def render(self) -> Text:
        text = Text()
        file_count = len(self.diff_data.files)
        file_word = "file" if file_count == 1 else "files"
        commit_count = self.diff_data.commit_count
        commit_word = "commit" if commit_count == 1 else "commits"

        text.append(f"{file_count} {file_word} changed", style="bold white")
        text.append("  •  ", style="#64748b")
        text.append(f"+{self.diff_data.total_additions}", style="bold #4ade80")
        text.append("  ", style="#64748b")
        text.append(f"-{self.diff_data.total_deletions}", style="bold #f87171")
        text.append("  •  ", style="#64748b")
        text.append(f"{commit_count} {commit_word}", style="#94a3b8")

        return text


class FileDiffToggled(Message):
    def __init__(self, path: str, expanded: bool):
        super().__init__()
        self.path = path
        self.expanded = expanded


class FileDiffHeader(Static, can_focus=True):
    BINDINGS = [
        Binding("enter", "toggle_diff", "Toggle", show=False),
        Binding("space", "toggle_diff", "Toggle", show=False),
    ]

    DEFAULT_CSS = """
    FileDiffHeader {
        height: 2;
        padding: 0 1;
        background: #0f172a;
        border-bottom: solid #334155;
    }

    FileDiffHeader:hover {
        background: #1e293b;
    }

    FileDiffHeader:focus {
        background: #1e293b;
        border-left: thick #6366f1;
    }

    FileDiffHeader.expanded {
        background: #1e293b;
    }
    """

    def __init__(self, file_diff: FileDiff, expanded: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.file_diff = file_diff
        self._expanded = expanded

    def render(self) -> Text:
        text = Text()

        # Expand/collapse indicator
        icon = "▼" if self._expanded else "▶"
        text.append(f"{icon} ", style="#64748b")

        # Status icon
        status_styles = {
            FileStatus.ADDED: ("A", "#4ade80"),
            FileStatus.MODIFIED: ("M", "#fbbf24"),
            FileStatus.DELETED: ("D", "#f87171"),
            FileStatus.RENAMED: ("R", "#818cf8"),
            FileStatus.COPIED: ("C", "#22d3ee"),
            FileStatus.UNKNOWN: ("?", "#64748b"),
        }
        status_char, status_color = status_styles.get(
            self.file_diff.status, ("?", "#64748b")
        )
        text.append(f"[{status_char}] ", style=status_color)

        # File path
        path = self.file_diff.path
        if self.file_diff.old_path:
            path = f"{self.file_diff.old_path} → {path}"
        text.append(path, style="bold #e2e8f0")

        # Spacer
        text.append("  ", style="")

        # Stats (right-aligned conceptually, but we'll just add spacing)
        if self.file_diff.additions > 0:
            text.append(f"+{self.file_diff.additions}", style="bold #4ade80")
            text.append(" ", style="")
        if self.file_diff.deletions > 0:
            text.append(f"-{self.file_diff.deletions}", style="bold #f87171")

        return text

    def toggle_expanded(self) -> None:
        """Toggle expanded state."""
        self._expanded = not self._expanded
        if self._expanded:
            self.add_class("expanded")
        else:
            self.remove_class("expanded")
        self.refresh()
        # Notify parent to show/hide content
        self.post_message(FileDiffToggled(self.file_diff.path, self._expanded))

    def action_toggle_diff(self) -> None:
        """Handle toggle action from keybinding."""
        self.toggle_expanded()

    def on_click(self) -> None:
        """Handle click to toggle."""
        self.toggle_expanded()


class FileDiffContent(Static):
    """Syntax-highlighted diff content for a single file."""

    DEFAULT_CSS = """
    FileDiffContent {
        height: auto;
        padding: 0 1;
        background: #0a0f1a;
        border-bottom: solid #334155;
        overflow-x: auto;
    }

    FileDiffContent.hidden {
        display: none;
    }
    """

    def __init__(self, file_diff: FileDiff, **kwargs):
        super().__init__(**kwargs)
        self.file_diff = file_diff
        self.add_class("hidden")  # Start collapsed

    def render(self) -> Syntax | Text:
        if not self.file_diff.diff_content:
            return Text("(no diff content)", style="#64748b italic")

        # Use Rich Syntax for diff highlighting
        # Strip the header lines (diff --git, index, ---, +++) for cleaner display
        content = self._strip_diff_header(self.file_diff.diff_content)
        if not content.strip():
            return Text("(binary file or no textual changes)", style="#64748b italic")

        return Syntax(
            content,
            "diff",
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )

    def _strip_diff_header(self, diff: str) -> str:
        """Strip the git diff header, keeping only the hunks."""
        lines = diff.split("\n")
        # Find the first hunk (starts with @@)
        for i, line in enumerate(lines):
            if line.startswith("@@"):
                return "\n".join(lines[i:])
        return diff

    def show(self) -> None:
        """Show the diff content."""
        self.remove_class("hidden")

    def hide(self) -> None:
        """Hide the diff content."""
        self.add_class("hidden")


class FileDiffSection(Vertical):
    """A complete file diff section with header and expandable content."""

    DEFAULT_CSS = """
    FileDiffSection {
        height: auto;
        margin: 0;
        padding: 0;
    }
    """

    def __init__(self, file_diff: FileDiff, start_expanded: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.file_diff = file_diff
        self.start_expanded = start_expanded

    def compose(self) -> ComposeResult:
        yield FileDiffHeader(self.file_diff, expanded=self.start_expanded)
        content = FileDiffContent(self.file_diff)
        if self.start_expanded:
            content.remove_class("hidden")
        yield content

    def on_file_diff_toggled(self, event: FileDiffToggled) -> None:
        """Handle toggle events from the header."""
        if event.path == self.file_diff.path:
            content = self.query_one(FileDiffContent)
            if event.expanded:
                content.show()
            else:
                content.hide()
            event.stop()


class MergeDiffView(Vertical):
    """Complete merge diff view with summary and file list.

    This is the main widget to use in the merge approval screen.
    """

    DEFAULT_CSS = """
    MergeDiffView {
        height: 100%;
        width: 100%;
    }

    MergeDiffView .files-header {
        height: 2;
        padding: 0 2;
        background: #1e1e2e;
        color: #94a3b8;
        text-style: bold;
        border-bottom: solid #334155;
    }

    MergeDiffView .files-scroll {
        height: 1fr;
    }

    MergeDiffView .no-changes {
        height: auto;
        padding: 2;
        color: #64748b;
        text-align: center;
    }
    """

    def __init__(self, diff_data: MergeDiffData | None, **kwargs):
        super().__init__(**kwargs)
        self.diff_data = diff_data

    def compose(self) -> ComposeResult:
        if not self.diff_data or not self.diff_data.files:
            yield Static("No changes to display", classes="no-changes")
            return

        # Summary bar at top
        yield DiffSummaryBar(self.diff_data)

        # Files header
        yield Static("FILES CHANGED", classes="files-header")

        # Scrollable file list
        with VerticalScroll(classes="files-scroll"):
            # Expand first file by default if there are few files
            expand_first = len(self.diff_data.files) <= 3
            for i, file_diff in enumerate(self.diff_data.files):
                yield FileDiffSection(
                    file_diff,
                    start_expanded=(i == 0 and expand_first),
                )

    def expand_all(self) -> None:
        """Expand all file sections."""
        for section in self.query(FileDiffSection):
            header = section.query_one(FileDiffHeader)
            if not header._expanded:
                header.toggle_expanded()

    def collapse_all(self) -> None:
        """Collapse all file sections."""
        for section in self.query(FileDiffSection):
            header = section.query_one(FileDiffHeader)
            if header._expanded:
                header.toggle_expanded()
