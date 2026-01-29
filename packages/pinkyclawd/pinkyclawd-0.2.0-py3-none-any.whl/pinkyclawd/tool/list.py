"""
List tool for directory listing with tree structure.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pinkyclawd.tool.base import (
    BOOLEAN_PARAM,
    INTEGER_PARAM,
    STRING_PARAM,
    Tool,
    ToolContext,
    ToolResult,
    make_schema,
)

# Default ignore patterns (similar to .gitignore defaults)
DEFAULT_IGNORE_PATTERNS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".env",
    ".idea",
    ".vscode",
    ".DS_Store",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "*.egg-info",
    ".tox",
    ".nox",
    "coverage",
    ".coverage",
    "htmlcov",
    ".hypothesis",
}


class ListTool(Tool):
    """List directory contents with optional tree structure."""

    MAX_ENTRIES = 1000
    MAX_DEPTH = 10

    @property
    def name(self) -> str:
        return "list"

    @property
    def description(self) -> str:
        return """List directory contents with tree structure.

Shows files and directories in the specified path.
Respects ignore patterns (.git, node_modules, __pycache__, etc.).
Use depth parameter to control recursion level.
Use showHidden=true to include hidden files."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                ("path", "Directory path to list (absolute or relative)", STRING_PARAM),
            ],
            optional=[
                (
                    "depth",
                    "Maximum depth for tree display (default: 2, max: 10)",
                    INTEGER_PARAM,
                ),
                (
                    "showHidden",
                    "Include hidden files (default: false)",
                    BOOLEAN_PARAM,
                ),
                (
                    "ignore",
                    "Additional patterns to ignore (comma-separated)",
                    STRING_PARAM,
                ),
            ],
        )

    def _should_ignore(self, name: str, ignore_patterns: set[str]) -> bool:
        """Check if a file/directory should be ignored."""
        # Check exact matches
        if name in ignore_patterns:
            return True

        # Check wildcard patterns
        for pattern in ignore_patterns:
            if "*" in pattern:
                # Simple glob matching
                if pattern.startswith("*"):
                    if name.endswith(pattern[1:]):
                        return True
                elif pattern.endswith("*"):
                    if name.startswith(pattern[:-1]):
                        return True

        return False

    def _build_tree(
        self,
        path: Path,
        prefix: str,
        depth: int,
        max_depth: int,
        show_hidden: bool,
        ignore_patterns: set[str],
        entry_count: list[int],
    ) -> list[str]:
        """Build tree structure recursively."""
        if entry_count[0] >= self.MAX_ENTRIES:
            return []

        if depth >= max_depth:
            return []

        lines: list[str] = []

        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return [f"{prefix}[permission denied]"]
        except Exception:
            return []

        # Filter entries
        filtered_entries = []
        for entry in entries:
            # Skip hidden files unless requested
            if not show_hidden and entry.name.startswith("."):
                continue

            # Skip ignored patterns
            if self._should_ignore(entry.name, ignore_patterns):
                continue

            filtered_entries.append(entry)

        for i, entry in enumerate(filtered_entries):
            if entry_count[0] >= self.MAX_ENTRIES:
                lines.append(f"{prefix}... (truncated)")
                break

            entry_count[0] += 1

            is_last = i == len(filtered_entries) - 1
            connector = "└── " if is_last else "├── "
            child_prefix = "    " if is_last else "│   "

            # Format entry
            name = entry.name
            if entry.is_dir():
                name += "/"
            elif entry.is_symlink():
                try:
                    target = entry.resolve()
                    name += f" -> {target}"
                except Exception:
                    name += " -> [broken link]"

            lines.append(f"{prefix}{connector}{name}")

            # Recurse into directories
            if entry.is_dir() and not entry.is_symlink():
                child_lines = self._build_tree(
                    entry,
                    prefix + child_prefix,
                    depth + 1,
                    max_depth,
                    show_hidden,
                    ignore_patterns,
                    entry_count,
                )
                lines.extend(child_lines)

        return lines

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """List directory contents."""
        path_str = kwargs.get("path", ".")
        depth = kwargs.get("depth", 2)
        show_hidden = kwargs.get("showHidden", False)
        extra_ignore = kwargs.get("ignore", "")

        # Clamp depth
        depth = min(max(1, depth), self.MAX_DEPTH)

        # Resolve path
        path = Path(path_str)
        if not path.is_absolute():
            path = ctx.working_directory / path

        if not path.exists():
            return ToolResult.fail(f"Path not found: {path}")

        if not path.is_dir():
            return ToolResult.fail(f"Not a directory: {path}")

        # Build ignore patterns
        ignore_patterns = DEFAULT_IGNORE_PATTERNS.copy()
        if extra_ignore:
            for pattern in extra_ignore.split(","):
                pattern = pattern.strip()
                if pattern:
                    ignore_patterns.add(pattern)

        # Build tree
        entry_count = [0]
        lines = [str(path)]
        entry_count[0] += 1

        tree_lines = self._build_tree(
            path,
            "",
            0,
            depth,
            show_hidden,
            ignore_patterns,
            entry_count,
        )
        lines.extend(tree_lines)

        truncated = entry_count[0] >= self.MAX_ENTRIES

        output = "\n".join(lines)
        if truncated:
            output += f"\n\n(Showing first {self.MAX_ENTRIES} entries)"

        return ToolResult.ok(
            output,
            count=entry_count[0],
            truncated=truncated,
            depth=depth,
        )
