"""
File tree widget with icons and navigation.

Matches OpenCode's file tree with:
- Directory expansion
- File type icons
- Drag-drop support
- File selection for context
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any, Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static, Tree
from textual.widgets.tree import TreeNode
from rich.text import Text


# File type to icon mapping (similar to OpenCode's 100+ icons)
FILE_ICONS: dict[str, str] = {
    # Languages
    ".py": "🐍",
    ".pyw": "🐍",
    ".pyx": "🐍",
    ".pxd": "🐍",
    ".pyi": "🐍",
    ".js": "📜",
    ".jsx": "⚛️",
    ".ts": "📘",
    ".tsx": "⚛️",
    ".go": "🐹",
    ".rs": "🦀",
    ".rb": "💎",
    ".java": "☕",
    ".kt": "🎯",
    ".kts": "🎯",
    ".scala": "⚡",
    ".c": "🔧",
    ".cpp": "🔧",
    ".cc": "🔧",
    ".cxx": "🔧",
    ".h": "📋",
    ".hpp": "📋",
    ".hxx": "📋",
    ".cs": "🎮",
    ".fs": "🔷",
    ".fsx": "🔷",
    ".swift": "🕊️",
    ".m": "📱",
    ".mm": "📱",
    ".php": "🐘",
    ".lua": "🌙",
    ".r": "📊",
    ".R": "📊",
    ".jl": "📐",
    ".ex": "💧",
    ".exs": "💧",
    ".erl": "📡",
    ".hrl": "📡",
    ".hs": "λ",
    ".lhs": "λ",
    ".clj": "🔮",
    ".cljs": "🔮",
    ".cljc": "🔮",
    ".lisp": "🔮",
    ".el": "🔮",
    ".ml": "🐪",
    ".mli": "🐪",
    ".pl": "🐪",
    ".pm": "🐪",
    ".zig": "⚡",
    ".nim": "👑",
    ".d": "🔶",
    ".v": "🔷",
    ".vhdl": "🔷",
    ".vhd": "🔷",
    ".sv": "🔷",
    ".asm": "⚙️",
    ".s": "⚙️",
    ".S": "⚙️",
    # Web
    ".html": "🌐",
    ".htm": "🌐",
    ".xhtml": "🌐",
    ".css": "🎨",
    ".scss": "🎨",
    ".sass": "🎨",
    ".less": "🎨",
    ".styl": "🎨",
    ".vue": "💚",
    ".svelte": "🔥",
    ".astro": "🚀",
    # Data
    ".json": "📋",
    ".jsonc": "📋",
    ".yaml": "📝",
    ".yml": "📝",
    ".toml": "⚙️",
    ".xml": "📄",
    ".csv": "📊",
    ".tsv": "📊",
    ".sql": "🗄️",
    ".graphql": "◆",
    ".gql": "◆",
    # Config
    ".ini": "⚙️",
    ".cfg": "⚙️",
    ".conf": "⚙️",
    ".config": "⚙️",
    ".env": "🔐",
    ".env.local": "🔐",
    ".env.development": "🔐",
    ".env.production": "🔐",
    # Docs
    ".md": "📝",
    ".markdown": "📝",
    ".mdx": "📝",
    ".rst": "📝",
    ".txt": "📄",
    ".rtf": "📄",
    ".doc": "📘",
    ".docx": "📘",
    ".pdf": "📕",
    ".tex": "📐",
    ".latex": "📐",
    # Shell
    ".sh": "🐚",
    ".bash": "🐚",
    ".zsh": "🐚",
    ".fish": "🐟",
    ".ps1": "💻",
    ".psm1": "💻",
    ".bat": "📦",
    ".cmd": "📦",
    # Build
    ".make": "🔨",
    ".makefile": "🔨",
    ".cmake": "🔨",
    ".dockerfile": "🐳",
    ".gradle": "🐘",
    ".maven": "🐘",
    # Images
    ".png": "🖼️",
    ".jpg": "🖼️",
    ".jpeg": "🖼️",
    ".gif": "🖼️",
    ".webp": "🖼️",
    ".svg": "🎨",
    ".ico": "🎯",
    ".bmp": "🖼️",
    ".tiff": "🖼️",
    # Audio/Video
    ".mp3": "🎵",
    ".wav": "🎵",
    ".ogg": "🎵",
    ".flac": "🎵",
    ".mp4": "🎬",
    ".webm": "🎬",
    ".avi": "🎬",
    ".mkv": "🎬",
    # Archives
    ".zip": "📦",
    ".tar": "📦",
    ".gz": "📦",
    ".bz2": "📦",
    ".xz": "📦",
    ".7z": "📦",
    ".rar": "📦",
    # Lock files
    ".lock": "🔒",
    # Git
    ".gitignore": "🙈",
    ".gitattributes": "🔧",
    ".gitmodules": "🔗",
}

# Special file names
SPECIAL_FILES: dict[str, str] = {
    "Dockerfile": "🐳",
    "docker-compose.yml": "🐳",
    "docker-compose.yaml": "🐳",
    "Makefile": "🔨",
    "CMakeLists.txt": "🔨",
    "package.json": "📦",
    "package-lock.json": "🔒",
    "yarn.lock": "🔒",
    "pnpm-lock.yaml": "🔒",
    "Cargo.toml": "🦀",
    "Cargo.lock": "🔒",
    "go.mod": "🐹",
    "go.sum": "🔒",
    "Gemfile": "💎",
    "Gemfile.lock": "🔒",
    "requirements.txt": "📋",
    "pyproject.toml": "🐍",
    "setup.py": "🐍",
    "setup.cfg": "🐍",
    "poetry.lock": "🔒",
    "Pipfile": "🐍",
    "Pipfile.lock": "🔒",
    "LICENSE": "📜",
    "LICENSE.md": "📜",
    "README.md": "📖",
    "README": "📖",
    "CHANGELOG.md": "📋",
    "CONTRIBUTING.md": "🤝",
    ".editorconfig": "⚙️",
    ".prettierrc": "✨",
    ".eslintrc": "⚠️",
    ".eslintrc.js": "⚠️",
    ".eslintrc.json": "⚠️",
    "tsconfig.json": "📘",
    "jsconfig.json": "📜",
    "babel.config.js": "🔧",
    ".babelrc": "🔧",
    "webpack.config.js": "📦",
    "vite.config.ts": "⚡",
    "vite.config.js": "⚡",
    "rollup.config.js": "📦",
    "jest.config.js": "🃏",
    "vitest.config.ts": "🃏",
    ".dockerignore": "🙈",
    ".npmignore": "🙈",
    ".nvmrc": "📗",
    ".node-version": "📗",
    ".python-version": "🐍",
    ".ruby-version": "💎",
    ".tool-versions": "🔧",
    "CLAUDE.md": "🤖",
}

# Directory icons
DIR_ICONS: dict[str, str] = {
    "src": "📁",
    "lib": "📚",
    "bin": "⚙️",
    "test": "🧪",
    "tests": "🧪",
    "spec": "🧪",
    "__tests__": "🧪",
    "docs": "📚",
    "doc": "📚",
    "build": "🔨",
    "dist": "📦",
    "out": "📦",
    "target": "🎯",
    "node_modules": "📦",
    "vendor": "📦",
    ".git": "🔀",
    ".github": "🐙",
    ".vscode": "💻",
    ".idea": "💡",
    "config": "⚙️",
    "scripts": "📜",
    "assets": "🖼️",
    "static": "📂",
    "public": "🌐",
    "templates": "📄",
    "migrations": "🔄",
    "fixtures": "📋",
    "examples": "💡",
}


def get_file_icon(path: Path) -> str:
    """Get icon for a file based on its name/extension."""
    name = path.name

    # Check special file names first
    if name in SPECIAL_FILES:
        return SPECIAL_FILES[name]

    # Check by extension
    suffix = path.suffix.lower()
    if suffix in FILE_ICONS:
        return FILE_ICONS[suffix]

    # Default icons
    if path.is_dir():
        return DIR_ICONS.get(name, "📁")

    return "📄"


def get_dir_icon(name: str) -> str:
    """Get icon for a directory."""
    return DIR_ICONS.get(name, "📁")


class FileTreeNode:
    """Represents a node in the file tree."""

    def __init__(self, path: Path, is_dir: bool = False) -> None:
        self.path = path
        self.is_dir = is_dir
        self.name = path.name
        self.icon = get_dir_icon(self.name) if is_dir else get_file_icon(path)

    def __str__(self) -> str:
        return f"{self.icon} {self.name}"


class FileTree(Tree[FileTreeNode]):
    """
    File tree widget with icons and navigation.

    Features:
    - Directory expansion with lazy loading
    - File type detection and icons
    - Selection for adding to context
    - Filtering hidden files
    - Path display
    """

    BINDINGS = [
        Binding("enter", "select_file", "Select"),
        Binding("space", "toggle_select", "Toggle"),
        Binding("h", "toggle_hidden", "Hidden"),
        Binding("r", "refresh", "Refresh"),
    ]

    DEFAULT_CSS = """
    FileTree {
        height: 100%;
        background: $surface;
        padding: 0;
    }

    FileTree > .tree--label {
        padding: 0 1;
    }

    FileTree > .tree--cursor {
        background: $primary 20%;
    }

    FileTree > .tree--guides {
        color: $text-muted;
    }

    FileTree > .tree--highlight {
        background: $primary 40%;
    }

    .file-selected {
        background: $accent 30%;
    }
    """

    show_hidden: reactive[bool] = reactive(False)
    selected_files: reactive[set[Path]] = reactive(set, init=False)

    class FileSelected(Message):
        """Message sent when a file is selected."""

        def __init__(self, path: Path) -> None:
            super().__init__()
            self.path = path

    class FileToggled(Message):
        """Message sent when a file selection is toggled."""

        def __init__(self, path: Path, selected: bool) -> None:
            super().__init__()
            self.path = path
            self.selected = selected

    def __init__(
        self,
        root: Path | None = None,
        show_hidden: bool = False,
        on_select: Callable[[Path], Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self.root_path = root or Path.cwd()
        self._on_select = on_select
        self._selected_files: set[Path] = set()

        # Create root node
        root_node = FileTreeNode(self.root_path, is_dir=True)
        super().__init__(str(root_node), data=root_node, **kwargs)

        self.show_hidden = show_hidden

    def on_mount(self) -> None:
        """Load the initial tree."""
        self._load_directory(self.root, self.root_path)
        self.root.expand()

    def _should_show(self, path: Path) -> bool:
        """Check if a path should be shown."""
        name = path.name

        # Skip hidden files unless enabled
        if not self.show_hidden and name.startswith("."):
            # Allow some dotfiles
            allowed = {".github", ".vscode", ".gitignore", ".env", ".env.local"}
            if name not in allowed:
                return False

        # Skip common junk directories
        skip_dirs = {
            "__pycache__", ".pytest_cache", ".mypy_cache",
            "node_modules", ".git", ".svn", ".hg",
            "venv", ".venv", "env", ".env",
            ".tox", ".nox", "build", "dist", "*.egg-info",
        }
        if path.is_dir() and name in skip_dirs:
            return False

        return True

    def _load_directory(self, node: TreeNode[FileTreeNode], path: Path) -> None:
        """Load a directory's contents into a tree node."""
        try:
            entries = sorted(
                path.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )

            for entry in entries:
                if self._should_show(entry):
                    file_node = FileTreeNode(entry, is_dir=entry.is_dir())
                    child = node.add(str(file_node), data=file_node)

                    if entry.is_dir():
                        # Add placeholder for lazy loading
                        child.allow_expand = True

        except PermissionError:
            node.add("[Permission Denied]")
        except OSError as e:
            node.add(f"[Error: {e}]")

    def on_tree_node_expanded(self, event: Tree.NodeExpanded[FileTreeNode]) -> None:
        """Handle node expansion - lazy load directory contents."""
        node = event.node
        if node.data and node.data.is_dir:
            # Check if already loaded
            if len(list(node.children)) == 0 or (
                len(list(node.children)) == 1 and
                list(node.children)[0].data is None
            ):
                # Clear any placeholder
                node.remove_children()
                # Load directory contents
                self._load_directory(node, node.data.path)

    def on_tree_node_selected(self, event: Tree.NodeSelected[FileTreeNode]) -> None:
        """Handle node selection."""
        node = event.node
        if node.data and not node.data.is_dir:
            self.post_message(self.FileSelected(node.data.path))
            if self._on_select:
                self._on_select(node.data.path)

    def action_select_file(self) -> None:
        """Select the current file."""
        node = self.cursor_node
        if node and node.data and not node.data.is_dir:
            self.post_message(self.FileSelected(node.data.path))
            if self._on_select:
                self._on_select(node.data.path)

    def action_toggle_select(self) -> None:
        """Toggle file selection for context."""
        node = self.cursor_node
        if node and node.data and not node.data.is_dir:
            path = node.data.path
            if path in self._selected_files:
                self._selected_files.discard(path)
                self.post_message(self.FileToggled(path, False))
            else:
                self._selected_files.add(path)
                self.post_message(self.FileToggled(path, True))
            self.refresh()

    def action_toggle_hidden(self) -> None:
        """Toggle hidden file visibility."""
        self.show_hidden = not self.show_hidden
        self.action_refresh()

    def action_refresh(self) -> None:
        """Refresh the tree."""
        self.clear()
        root_node = FileTreeNode(self.root_path, is_dir=True)
        self.root.data = root_node
        self.root.set_label(str(root_node))
        self._load_directory(self.root, self.root_path)
        self.root.expand()

    def get_selected_files(self) -> list[Path]:
        """Get list of selected files."""
        return list(self._selected_files)

    def clear_selection(self) -> None:
        """Clear file selection."""
        self._selected_files.clear()
        self.refresh()

    def select_file(self, path: Path) -> None:
        """Programmatically select a file."""
        if path.exists() and path.is_file():
            self._selected_files.add(path)
            self.post_message(self.FileToggled(path, True))
            self.refresh()


class FileTreePanel(Vertical):
    """
    File tree panel with header and controls.

    Features:
    - Header with file count
    - Selected files display
    - Search/filter
    - Expand/collapse all
    """

    DEFAULT_CSS = """
    FileTreePanel {
        height: 100%;
        background: $panel;
    }

    .file-tree-header {
        height: 3;
        padding: 1;
        background: $surface;
        border-bottom: solid $border;
    }

    .file-tree-title {
        text-style: bold;
    }

    .file-tree-count {
        color: $text-muted;
    }

    .selected-files {
        height: auto;
        max-height: 6;
        padding: 1;
        background: $accent 10%;
        border-bottom: solid $border;
    }

    .selected-file {
        padding: 0 1;
    }

    .no-selection {
        color: $text-muted;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        root: Path | None = None,
        show_hidden: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.root = root or Path.cwd()
        self.show_hidden = show_hidden
        self._selected_count = 0

    def compose(self) -> ComposeResult:
        with Vertical(classes="file-tree-header"):
            yield Static(f"📁 {self.root.name}", classes="file-tree-title")
            yield Static("0 files selected", classes="file-tree-count", id="file-count")

        with Vertical(classes="selected-files", id="selected-files"):
            yield Static("No files selected", classes="no-selection")

        yield FileTree(
            root=self.root,
            show_hidden=self.show_hidden,
            id="file-tree",
        )

    def on_file_tree_file_toggled(self, event: FileTree.FileToggled) -> None:
        """Update selected files display."""
        tree = self.query_one("#file-tree", FileTree)
        selected = tree.get_selected_files()
        self._selected_count = len(selected)

        # Update count
        count_widget = self.query_one("#file-count", Static)
        count_widget.update(f"{self._selected_count} files selected")

        # Update selected files display
        selected_container = self.query_one("#selected-files", Vertical)
        selected_container.remove_children()

        if selected:
            for path in selected[:5]:
                selected_container.mount(
                    Static(f"✓ {path.name}", classes="selected-file")
                )
            if len(selected) > 5:
                selected_container.mount(
                    Static(f"... and {len(selected) - 5} more", classes="no-selection")
                )
        else:
            selected_container.mount(
                Static("No files selected", classes="no-selection")
            )

    def get_selected_files(self) -> list[Path]:
        """Get selected files."""
        return self.query_one("#file-tree", FileTree).get_selected_files()

    def clear_selection(self) -> None:
        """Clear selection."""
        self.query_one("#file-tree", FileTree).clear_selection()
