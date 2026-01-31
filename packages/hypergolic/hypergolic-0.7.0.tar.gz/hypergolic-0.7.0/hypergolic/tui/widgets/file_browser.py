"""File browser sidebar widget using Textual's DirectoryTree."""

from collections.abc import Iterable
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import DirectoryTree, Static


class FilteredDirectoryTree(DirectoryTree):
    """DirectoryTree that filters out common noise directories."""

    IGNORED_DIRS = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        ".venv",
        "venv",
        ".tox",
        ".eggs",
        "*.egg-info",
        ".coverage",
        "htmlcov",
        "dist",
        "build",
    }

    def filter_paths(self, paths: Iterable[Path]) -> list[Path]:
        """Filter out ignored directories and hidden files."""
        return [
            path
            for path in paths
            if path.name not in self.IGNORED_DIRS
            and not (path.name.startswith(".") and path.name not in {".github"})
            and not path.name.endswith(".egg-info")
        ]


class FileBrowser(Vertical):
    """File browser panel for navigating project files."""

    DEFAULT_CSS = """
    FileBrowser {
        dock: left;
        width: 32;
        background: #0f172a;
        border-right: solid #334155;
    }

    FileBrowser.hidden {
        display: none;
    }

    FileBrowser .browser-title {
        text-style: bold;
        color: #818cf8;
        text-align: center;
        padding: 1 0;
        border-bottom: double #4f46e5;
    }

    FileBrowser FilteredDirectoryTree {
        background: #0f172a;
        padding: 0 1;
        scrollbar-gutter: stable;
    }

    FileBrowser FilteredDirectoryTree:focus {
        border: none;
    }

    FileBrowser FilteredDirectoryTree > .directory-tree--folder {
        color: #818cf8;
    }

    FileBrowser FilteredDirectoryTree > .directory-tree--file {
        color: #e2e8f0;
    }

    FileBrowser FilteredDirectoryTree > .directory-tree--extension {
        color: #64748b;
    }

    FileBrowser FilteredDirectoryTree > .tree--cursor {
        background: #334155;
    }

    FileBrowser FilteredDirectoryTree > .tree--highlight {
        background: #1e293b;
    }
    """

    def __init__(
        self,
        root_path: Path,
        expand_to: Path | None = None,
        project_name: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.root_path = root_path
        self.expand_to = expand_to
        self.project_name = project_name or root_path.name

    def compose(self) -> ComposeResult:
        yield Static("📁 Files", classes="browser-title")
        tree = FilteredDirectoryTree(self.root_path, id="directory-tree")
        yield tree

    def on_mount(self) -> None:
        """Set the root label to the project name after mounting."""
        tree = self.query_one("#directory-tree", FilteredDirectoryTree)
        tree.root.set_label(self.project_name)
        tree.root.expand()

    def toggle(self) -> None:
        """Toggle file browser visibility."""
        self.toggle_class("hidden")

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        event.stop()
        self.post_message(FileBrowserFileSelected(event.path))


class FileBrowserFileSelected(Message):
    """Message posted when a file is selected in the browser."""

    def __init__(self, path: Path):
        super().__init__()
        self.path = path
