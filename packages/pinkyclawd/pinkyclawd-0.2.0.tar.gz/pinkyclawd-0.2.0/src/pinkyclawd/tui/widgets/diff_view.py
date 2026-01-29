"""
Diff view widget with split and unified modes.

Matches OpenCode's diff display with:
- Split (side-by-side) view
- Unified view
- Syntax highlighting
- Line numbers
- Change indicators
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static, Button, Label
from rich.text import Text
from rich.syntax import Syntax


class DiffMode(Enum):
    """Diff display mode."""

    UNIFIED = "unified"
    SPLIT = "split"


@dataclass
class DiffLine:
    """Represents a line in the diff."""

    type: str  # "add", "remove", "context", "header"
    content: str
    old_line_no: int | None = None
    new_line_no: int | None = None


@dataclass
class FileDiff:
    """Represents a diff for a single file."""

    path: str
    old_content: str = ""
    new_content: str = ""
    added: int = 0
    removed: int = 0
    is_new: bool = False
    is_deleted: bool = False
    is_binary: bool = False
    lines: list[DiffLine] = field(default_factory=list)


def compute_diff(old_content: str, new_content: str) -> list[DiffLine]:
    """Compute diff between two strings."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff_lines: list[DiffLine] = []
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

    old_line_no = 0
    new_line_no = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for i in range(i2 - i1):
                old_line_no += 1
                new_line_no += 1
                content = old_lines[i1 + i].rstrip("\n\r")
                diff_lines.append(DiffLine(
                    type="context",
                    content=content,
                    old_line_no=old_line_no,
                    new_line_no=new_line_no,
                ))

        elif tag == "delete":
            for i in range(i2 - i1):
                old_line_no += 1
                content = old_lines[i1 + i].rstrip("\n\r")
                diff_lines.append(DiffLine(
                    type="remove",
                    content=content,
                    old_line_no=old_line_no,
                    new_line_no=None,
                ))

        elif tag == "insert":
            for j in range(j2 - j1):
                new_line_no += 1
                content = new_lines[j1 + j].rstrip("\n\r")
                diff_lines.append(DiffLine(
                    type="add",
                    content=content,
                    old_line_no=None,
                    new_line_no=new_line_no,
                ))

        elif tag == "replace":
            # First show removals
            for i in range(i2 - i1):
                old_line_no += 1
                content = old_lines[i1 + i].rstrip("\n\r")
                diff_lines.append(DiffLine(
                    type="remove",
                    content=content,
                    old_line_no=old_line_no,
                    new_line_no=None,
                ))
            # Then show additions
            for j in range(j2 - j1):
                new_line_no += 1
                content = new_lines[j1 + j].rstrip("\n\r")
                diff_lines.append(DiffLine(
                    type="add",
                    content=content,
                    old_line_no=None,
                    new_line_no=new_line_no,
                ))

    return diff_lines


def get_language_from_path(path: str) -> str:
    """Determine language from file path for syntax highlighting."""
    ext_to_lang = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "jsx",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".java": "java",
        ".kt": "kotlin",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".swift": "swift",
        ".php": "php",
        ".lua": "lua",
        ".r": "r",
        ".R": "r",
        ".sql": "sql",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".xml": "xml",
        ".md": "markdown",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "zsh",
        ".dockerfile": "dockerfile",
        ".makefile": "makefile",
    }

    p = Path(path)
    ext = p.suffix.lower()
    name = p.name.lower()

    # Check special filenames
    if name == "dockerfile":
        return "dockerfile"
    if name == "makefile":
        return "makefile"

    return ext_to_lang.get(ext, "text")


class DiffLineWidget(Static):
    """Widget for a single diff line."""

    DEFAULT_CSS = """
    DiffLineWidget {
        height: 1;
        width: 100%;
    }

    DiffLineWidget.add {
        background: $success 15%;
    }

    DiffLineWidget.remove {
        background: $error 15%;
    }

    DiffLineWidget.context {
        background: transparent;
    }

    DiffLineWidget.header {
        background: $primary 20%;
        text-style: bold;
    }

    .line-number {
        width: 5;
        color: $text-muted;
        text-align: right;
        padding-right: 1;
    }

    .line-indicator {
        width: 1;
        text-style: bold;
    }

    .line-content {
        width: 1fr;
    }
    """

    def __init__(self, line: DiffLine, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.line = line
        self.add_class(line.type)

    def compose(self) -> ComposeResult:
        text = Text()

        # Line number
        line_no = self.line.new_line_no or self.line.old_line_no or ""
        text.append(f"{line_no:>4} ", style="dim")

        # Indicator
        indicator = {
            "add": "+",
            "remove": "-",
            "context": " ",
            "header": "@",
        }.get(self.line.type, " ")

        indicator_style = {
            "add": "bold green",
            "remove": "bold red",
            "context": "dim",
            "header": "bold cyan",
        }.get(self.line.type, "")

        text.append(indicator, style=indicator_style)
        text.append(" ")

        # Content
        content_style = {
            "add": "green",
            "remove": "red",
            "context": "",
            "header": "cyan",
        }.get(self.line.type, "")

        text.append(self.line.content, style=content_style)

        yield Static(text)


class UnifiedDiffView(ScrollableContainer):
    """Unified diff view (traditional patch format)."""

    DEFAULT_CSS = """
    UnifiedDiffView {
        height: 100%;
        width: 100%;
        background: $surface;
        padding: 1;
    }

    .diff-header {
        height: 3;
        padding: 0 1;
        background: $primary 20%;
        margin-bottom: 1;
    }

    .diff-path {
        text-style: bold;
    }

    .diff-stats {
        color: $text-muted;
    }

    .diff-content {
        height: auto;
    }
    """

    def __init__(self, file_diff: FileDiff, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.file_diff = file_diff

    def compose(self) -> ComposeResult:
        # Header
        with Vertical(classes="diff-header"):
            yield Static(self.file_diff.path, classes="diff-path")
            stats = Text()
            stats.append(f"+{self.file_diff.added}", style="green")
            stats.append(" / ")
            stats.append(f"-{self.file_diff.removed}", style="red")
            yield Static(stats, classes="diff-stats")

        # Diff lines
        with Vertical(classes="diff-content"):
            if self.file_diff.is_binary:
                yield Static("Binary file", classes="diff-binary")
            elif self.file_diff.is_new:
                yield Static("(new file)", classes="diff-new")
            elif self.file_diff.is_deleted:
                yield Static("(deleted)", classes="diff-deleted")
            else:
                for line in self.file_diff.lines:
                    yield DiffLineWidget(line)


class SplitDiffPane(Vertical):
    """One side of a split diff view."""

    DEFAULT_CSS = """
    SplitDiffPane {
        width: 1fr;
        height: 100%;
        background: $surface;
        border-right: solid $border;
    }

    SplitDiffPane:last-child {
        border-right: none;
    }

    .pane-header {
        height: 2;
        padding: 0 1;
        background: $primary 20%;
        text-style: bold;
    }

    .pane-content {
        height: 1fr;
        overflow-y: scroll;
    }
    """

    def __init__(
        self,
        title: str,
        lines: list[DiffLine],
        side: str,  # "old" or "new"
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.title = title
        self.lines = lines
        self.side = side

    def compose(self) -> ComposeResult:
        yield Static(self.title, classes="pane-header")

        with ScrollableContainer(classes="pane-content"):
            for line in self.lines:
                # Filter lines based on side
                if self.side == "old":
                    if line.type == "add":
                        continue
                    yield DiffLineWidget(line)
                else:  # new
                    if line.type == "remove":
                        continue
                    yield DiffLineWidget(line)


class SplitDiffView(Horizontal):
    """Split (side-by-side) diff view."""

    DEFAULT_CSS = """
    SplitDiffView {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, file_diff: FileDiff, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.file_diff = file_diff

    def compose(self) -> ComposeResult:
        yield SplitDiffPane(
            title="Before",
            lines=self.file_diff.lines,
            side="old",
        )
        yield SplitDiffPane(
            title="After",
            lines=self.file_diff.lines,
            side="new",
        )


class DiffView(Vertical):
    """
    Complete diff view with mode toggle.

    Features:
    - Unified/split view toggle
    - File header with stats
    - Syntax highlighting
    - Keyboard navigation
    """

    BINDINGS = [
        Binding("u", "unified_mode", "Unified"),
        Binding("s", "split_mode", "Split"),
        Binding("c", "collapse", "Collapse"),
    ]

    DEFAULT_CSS = """
    DiffView {
        height: 100%;
        width: 100%;
        background: $panel;
    }

    .diff-toolbar {
        height: 3;
        padding: 0 1;
        background: $surface;
        border-bottom: solid $border;
    }

    .diff-toolbar Button {
        margin-right: 1;
    }

    .diff-container {
        height: 1fr;
    }

    .no-diff {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }
    """

    mode: reactive[DiffMode] = reactive(DiffMode.UNIFIED)

    class ModeChanged(Message):
        """Message sent when diff mode changes."""

        def __init__(self, mode: DiffMode) -> None:
            super().__init__()
            self.mode = mode

    def __init__(
        self,
        file_diff: FileDiff | None = None,
        mode: DiffMode = DiffMode.UNIFIED,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.file_diff = file_diff
        self.mode = mode

    def compose(self) -> ComposeResult:
        # Toolbar
        with Horizontal(classes="diff-toolbar"):
            yield Button("Unified", id="btn-unified", variant="primary")
            yield Button("Split", id="btn-split")
            if self.file_diff:
                stats = Text()
                stats.append(f"+{self.file_diff.added}", style="green")
                stats.append(" ")
                stats.append(f"-{self.file_diff.removed}", style="red")
                yield Static(stats, id="diff-stats")

        # Diff content
        with Vertical(classes="diff-container", id="diff-container"):
            if not self.file_diff:
                yield Static("No changes to display", classes="no-diff")
            elif self.mode == DiffMode.UNIFIED:
                yield UnifiedDiffView(self.file_diff)
            else:
                yield SplitDiffView(self.file_diff)

    def watch_mode(self, mode: DiffMode) -> None:
        """React to mode changes."""
        # Update button states
        try:
            unified_btn = self.query_one("#btn-unified", Button)
            split_btn = self.query_one("#btn-split", Button)

            if mode == DiffMode.UNIFIED:
                unified_btn.variant = "primary"
                split_btn.variant = "default"
            else:
                unified_btn.variant = "default"
                split_btn.variant = "primary"
        except Exception:
            pass

        # Refresh the diff display
        self._refresh_diff()

    def _refresh_diff(self) -> None:
        """Refresh the diff display."""
        container = self.query_one("#diff-container", Vertical)
        container.remove_children()

        if not self.file_diff:
            container.mount(Static("No changes to display", classes="no-diff"))
        elif self.mode == DiffMode.UNIFIED:
            container.mount(UnifiedDiffView(self.file_diff))
        else:
            container.mount(SplitDiffView(self.file_diff))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-unified":
            self.mode = DiffMode.UNIFIED
        elif event.button.id == "btn-split":
            self.mode = DiffMode.SPLIT

        self.post_message(self.ModeChanged(self.mode))

    def action_unified_mode(self) -> None:
        """Switch to unified mode."""
        self.mode = DiffMode.UNIFIED

    def action_split_mode(self) -> None:
        """Switch to split mode."""
        self.mode = DiffMode.SPLIT

    def action_collapse(self) -> None:
        """Collapse the diff view."""
        self.display = False

    def set_diff(self, file_diff: FileDiff) -> None:
        """Set the diff to display."""
        self.file_diff = file_diff
        self._refresh_diff()


class DiffSummaryItem(Static):
    """Summary item for a modified file."""

    DEFAULT_CSS = """
    DiffSummaryItem {
        height: 1;
        padding: 0 1;
    }

    DiffSummaryItem:hover {
        background: $primary 20%;
    }

    DiffSummaryItem.selected {
        background: $primary 40%;
    }

    .file-name {
        width: 1fr;
    }

    .file-stats {
        width: auto;
    }
    """

    def __init__(self, file_diff: FileDiff, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.file_diff = file_diff

    def compose(self) -> ComposeResult:
        text = Text()

        # File icon
        icon = "📄"
        if self.file_diff.is_new:
            icon = "✨"
        elif self.file_diff.is_deleted:
            icon = "🗑️"

        text.append(f"{icon} {Path(self.file_diff.path).name} ")

        # Stats
        if self.file_diff.added > 0:
            text.append(f"+{self.file_diff.added}", style="green")
        if self.file_diff.removed > 0:
            if self.file_diff.added > 0:
                text.append(" ")
            text.append(f"-{self.file_diff.removed}", style="red")

        yield Static(text)


class DiffPanel(Vertical):
    """
    Complete diff panel with file list and diff view.

    Features:
    - File list with change summary
    - Selectable diff view
    - Mode toggle
    """

    DEFAULT_CSS = """
    DiffPanel {
        height: 100%;
        width: 100%;
    }

    .file-list {
        height: 10;
        background: $surface;
        border-bottom: solid $border;
    }

    .file-list-header {
        height: 2;
        padding: 0 1;
        background: $primary 20%;
        text-style: bold;
    }

    .file-list-content {
        height: 1fr;
        overflow-y: scroll;
    }

    .diff-area {
        height: 1fr;
    }
    """

    def __init__(
        self,
        diffs: list[FileDiff] | None = None,
        mode: DiffMode = DiffMode.UNIFIED,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.diffs = diffs or []
        self.mode = mode
        self.selected_index = 0

    def compose(self) -> ComposeResult:
        # File list
        with Vertical(classes="file-list"):
            total_added = sum(d.added for d in self.diffs)
            total_removed = sum(d.removed for d in self.diffs)

            header = Text()
            header.append(f"Modified Files ({len(self.diffs)}) ")
            header.append(f"+{total_added}", style="green")
            header.append(" ")
            header.append(f"-{total_removed}", style="red")

            yield Static(header, classes="file-list-header")

            with ScrollableContainer(classes="file-list-content"):
                for i, diff in enumerate(self.diffs):
                    item = DiffSummaryItem(diff)
                    if i == self.selected_index:
                        item.add_class("selected")
                    yield item

        # Diff view
        with Vertical(classes="diff-area"):
            if self.diffs:
                yield DiffView(
                    file_diff=self.diffs[self.selected_index] if self.diffs else None,
                    mode=self.mode,
                    id="diff-view",
                )
            else:
                yield Static("No changes", classes="no-diff")

    def set_diffs(self, diffs: list[FileDiff]) -> None:
        """Set the diffs to display."""
        self.diffs = diffs
        self.selected_index = 0
        self.refresh(recompose=True)

    def select_file(self, index: int) -> None:
        """Select a file by index."""
        if 0 <= index < len(self.diffs):
            self.selected_index = index
            try:
                diff_view = self.query_one("#diff-view", DiffView)
                diff_view.set_diff(self.diffs[index])
            except Exception:
                pass
            self.refresh(recompose=True)


def create_file_diff(
    path: str,
    old_content: str,
    new_content: str,
) -> FileDiff:
    """Create a FileDiff from old and new content."""
    lines = compute_diff(old_content, new_content)

    added = sum(1 for line in lines if line.type == "add")
    removed = sum(1 for line in lines if line.type == "remove")

    return FileDiff(
        path=path,
        old_content=old_content,
        new_content=new_content,
        added=added,
        removed=removed,
        is_new=not old_content,
        is_deleted=not new_content,
        lines=lines,
    )
