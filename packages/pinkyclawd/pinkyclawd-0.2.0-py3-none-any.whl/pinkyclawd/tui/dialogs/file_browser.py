"""
File browser dialogs for PinkyClawd TUI.

Matches OpenCode's file/directory selection:
- File browser with preview
- Directory browser
- Multi-select support
- Recent files
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, Container
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DirectoryTree,
    Input,
    Label,
    Static,
    ListView,
    ListItem,
)
from rich.text import Text
from rich.syntax import Syntax

from pinkyclawd.tui.widgets.file_tree import get_file_icon


class FilePreview(Static):
    """Preview panel for selected file."""

    DEFAULT_CSS = """
    FilePreview {
        height: 100%;
        padding: 1;
        background: $surface;
        overflow: auto;
    }

    .preview-header {
        text-style: bold;
        margin-bottom: 1;
    }

    .preview-meta {
        color: $text-muted;
        margin-bottom: 1;
    }

    .preview-content {
        height: 1fr;
        overflow: auto;
    }

    .no-preview {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }
    """

    def __init__(self, path: Path | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._path = path

    def compose(self) -> ComposeResult:
        if not self._path or not self._path.exists():
            yield Static("No file selected", classes="no-preview")
            return

        if self._path.is_dir():
            yield Static(f"Directory: {self._path.name}", classes="preview-header")
            try:
                children = list(self._path.iterdir())[:20]
                for child in children:
                    icon = get_file_icon(child)
                    yield Static(f"{icon} {child.name}")
                if len(list(self._path.iterdir())) > 20:
                    yield Static(f"... and more", classes="text-muted")
            except PermissionError:
                yield Static("Permission denied", classes="no-preview")
            return

        # File preview
        yield Static(f"{get_file_icon(self._path)} {self._path.name}", classes="preview-header")

        # File metadata
        try:
            stat = self._path.stat()
            size = stat.st_size
            if size < 1024:
                size_str = f"{size} bytes"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            yield Static(size_str, classes="preview-meta")
        except Exception:
            pass

        # File content preview
        if self._is_text_file():
            try:
                content = self._path.read_text(errors="replace")[:5000]
                yield Static(content, classes="preview-content")
            except Exception as e:
                yield Static(f"Cannot read file: {e}", classes="no-preview")
        else:
            yield Static("Binary file", classes="no-preview")

    def _is_text_file(self) -> bool:
        """Check if file appears to be text."""
        text_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".rb",
            ".java", ".kt", ".c", ".cpp", ".h", ".hpp", ".cs", ".swift",
            ".php", ".lua", ".r", ".sql", ".html", ".htm", ".css",
            ".scss", ".sass", ".json", ".yaml", ".yml", ".toml", ".xml",
            ".md", ".txt", ".rst", ".sh", ".bash", ".zsh", ".fish",
            ".ps1", ".bat", ".cmd", ".dockerfile", ".makefile",
            ".gitignore", ".env", ".cfg", ".ini", ".conf",
        }
        return self._path.suffix.lower() in text_extensions

    def set_file(self, path: Path | None) -> None:
        """Update the preview file."""
        self._path = path
        self.refresh(recompose=True)


class RecentFileItem(ListItem):
    """Recent file list item."""

    def __init__(self, path: Path, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.path = path

    def compose(self) -> ComposeResult:
        text = Text()
        text.append(f"{get_file_icon(self.path)} ")
        text.append(self.path.name, style="bold")
        text.append(f"\n  {self.path.parent}", style="dim")
        yield Label(text)


class FileBrowserDialog(ModalScreen[list[Path] | None]):
    """
    File browser dialog with preview.

    Features:
    - Directory tree navigation
    - File preview
    - Multi-select
    - Recent files
    - Search/filter
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select", "Select"),
        Binding("ctrl+a", "select_all", "Select All"),
    ]

    CSS = """
    FileBrowserDialog {
        align: center middle;
    }

    FileBrowserDialog > Container {
        width: 95%;
        max-width: 120;
        height: 90%;
        max-height: 40;
        background: $panel;
        border: thick $primary;
    }

    .browser-header {
        height: 5;
        padding: 1;
        background: $surface;
        border-bottom: solid $border;
    }

    .browser-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .browser-body {
        height: 1fr;
    }

    .browser-tree {
        width: 1fr;
        height: 100%;
        border-right: solid $border;
    }

    .browser-preview {
        width: 1fr;
        height: 100%;
    }

    .browser-footer {
        height: 3;
        padding: 0 1;
        background: $surface;
        border-top: solid $border;
        content-align: right middle;
    }

    .browser-footer Button {
        margin-left: 1;
    }

    .selected-count {
        width: 1fr;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        root: Path | None = None,
        title: str = "Select File",
        multi_select: bool = False,
        file_filter: Callable[[Path], bool] | None = None,
        recent_files: list[Path] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.root = root or Path.cwd()
        self.title_text = title
        self.multi_select = multi_select
        self.file_filter = file_filter
        self.recent_files = recent_files or []
        self._selected: set[Path] = set()
        self._current_path: Path | None = None

    def compose(self) -> ComposeResult:
        with Container():
            # Header
            with Vertical(classes="browser-header"):
                yield Static(self.title_text, classes="browser-title")
                yield Input(
                    placeholder="Search files...",
                    id="search",
                )

            # Body
            with Horizontal(classes="browser-body"):
                # Directory tree
                with Vertical(classes="browser-tree"):
                    yield DirectoryTree(str(self.root), id="tree")

                # Preview
                with Vertical(classes="browser-preview"):
                    yield FilePreview(id="preview")

            # Footer
            with Horizontal(classes="browser-footer"):
                yield Static("0 files selected", classes="selected-count", id="count")
                yield Button("Cancel", id="cancel")
                yield Button("Select", variant="primary", id="select")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection in tree."""
        path = Path(event.path)

        # Apply filter if set
        if self.file_filter and not self.file_filter(path):
            return

        self._current_path = path

        # Update preview
        preview = self.query_one("#preview", FilePreview)
        preview.set_file(path)

        # Handle selection
        if self.multi_select:
            if path in self._selected:
                self._selected.discard(path)
            else:
                self._selected.add(path)
        else:
            self._selected = {path}

        self._update_count()

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        """Handle directory selection."""
        path = Path(event.path)
        preview = self.query_one("#preview", FilePreview)
        preview.set_file(path)

    def _update_count(self) -> None:
        """Update the selection count."""
        count = self.query_one("#count", Static)
        n = len(self._selected)
        count.update(f"{n} file{'s' if n != 1 else ''} selected")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "select":
            if self._selected:
                self.dismiss(list(self._selected))
            elif self._current_path:
                self.dismiss([self._current_path])
            else:
                self.dismiss(None)

    def action_cancel(self) -> None:
        """Cancel selection."""
        self.dismiss(None)

    def action_select(self) -> None:
        """Confirm selection."""
        if self._selected:
            self.dismiss(list(self._selected))
        elif self._current_path:
            self.dismiss([self._current_path])
        else:
            self.dismiss(None)

    def action_select_all(self) -> None:
        """Select all files in current directory."""
        if not self.multi_select:
            return

        try:
            tree = self.query_one("#tree", DirectoryTree)
            # Get current directory from tree
            if tree.cursor_node and tree.cursor_node.data:
                current = Path(str(tree.cursor_node.data.path))
                if current.is_dir():
                    for child in current.iterdir():
                        if child.is_file():
                            if not self.file_filter or self.file_filter(child):
                                self._selected.add(child)
                    self._update_count()
        except Exception:
            pass


class DirectoryBrowserDialog(ModalScreen[Path | None]):
    """
    Directory browser dialog.

    Features:
    - Directory tree navigation
    - Create new directory
    - Path input
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select", "Select"),
    ]

    CSS = """
    DirectoryBrowserDialog {
        align: center middle;
    }

    DirectoryBrowserDialog > Container {
        width: 80%;
        max-width: 80;
        height: 80%;
        max-height: 30;
        background: $panel;
        border: thick $primary;
    }

    .browser-header {
        height: 5;
        padding: 1;
        background: $surface;
        border-bottom: solid $border;
    }

    .browser-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .browser-body {
        height: 1fr;
        padding: 1;
    }

    .browser-footer {
        height: 3;
        padding: 0 1;
        background: $surface;
        border-top: solid $border;
        content-align: right middle;
    }

    .browser-footer Button {
        margin-left: 1;
    }

    .current-path {
        width: 1fr;
        color: $primary;
    }
    """

    def __init__(
        self,
        root: Path | None = None,
        title: str = "Select Directory",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.root = root or Path.cwd()
        self.title_text = title
        self._selected_path: Path | None = self.root

    def compose(self) -> ComposeResult:
        with Container():
            # Header
            with Vertical(classes="browser-header"):
                yield Static(self.title_text, classes="browser-title")
                yield Input(
                    value=str(self.root),
                    placeholder="Path...",
                    id="path-input",
                )

            # Body
            with Vertical(classes="browser-body"):
                yield DirectoryTree(str(self.root), id="tree")

            # Footer
            with Horizontal(classes="browser-footer"):
                yield Static(str(self._selected_path), classes="current-path", id="current")
                yield Button("New Folder", id="new-folder")
                yield Button("Cancel", id="cancel")
                yield Button("Select", variant="primary", id="select")

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        """Handle directory selection."""
        self._selected_path = Path(event.path)
        current = self.query_one("#current", Static)
        current.update(str(self._selected_path))

        path_input = self.query_one("#path-input", Input)
        path_input.value = str(self._selected_path)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle path input."""
        path = Path(event.value)
        if path.exists() and path.is_dir():
            self._selected_path = path
            current = self.query_one("#current", Static)
            current.update(str(self._selected_path))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "select":
            self.dismiss(self._selected_path)
        elif event.button.id == "new-folder":
            # TODO: Implement new folder creation dialog
            pass

    def action_cancel(self) -> None:
        """Cancel selection."""
        self.dismiss(None)

    def action_select(self) -> None:
        """Confirm selection."""
        self.dismiss(self._selected_path)
