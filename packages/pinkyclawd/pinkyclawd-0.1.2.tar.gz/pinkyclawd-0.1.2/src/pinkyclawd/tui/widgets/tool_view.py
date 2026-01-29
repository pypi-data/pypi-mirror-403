"""
Tool-specific rendering widgets for different tool types.

Matches OpenCode's tool display with inline and block views,
custom icons, and detailed output formatting.
"""

from __future__ import annotations

from typing import Any

from textual.widgets import Static, Collapsible
from textual.containers import Vertical, Horizontal, Container
from textual.app import ComposeResult
from rich.text import Text
from rich.syntax import Syntax


class ToolView(Static):
    """
    Base class for tool views.

    Supports both inline (collapsed) and block (expanded) display modes.
    """

    DEFAULT_CSS = """
    ToolView {
        padding: 0 1;
        margin: 0;
    }

    ToolView.inline {
        height: 1;
    }

    ToolView.block {
        height: auto;
        margin: 1 0;
        background: $surface;
        border-left: thick $primary;
        padding: 1;
    }

    ToolView.error {
        border-left: thick $error;
    }

    ToolView.success {
        border-left: thick $success;
    }

    .tool-icon {
        width: 3;
        color: $text-muted;
    }

    .tool-name {
        color: $warning;
        text-style: bold;
        width: auto;
    }

    .tool-summary {
        color: $text-muted;
        padding-left: 1;
    }

    .tool-output {
        margin-top: 1;
    }

    .tool-error {
        color: $error;
    }

    .line-number {
        color: $text-muted;
        width: 4;
        text-align: right;
    }

    .diff-added {
        color: $success;
        background: $success 10%;
    }

    .diff-removed {
        color: $error;
        background: $error 10%;
    }
    """

    TOOL_ICONS = {
        "bash": "$",
        "glob": "*",
        "read": "->",
        "grep": "%",
        "write": "#",
        "edit": "~",
        "list": ">",
        "task": "@",
        "webfetch": "W",
        "websearch": "?",
        "todowrite": "[]",
        "question": "Q",
        "apply_patch": "P",
        "default": ".",
    }

    def __init__(
        self,
        tool_name: str,
        tool_input: dict[str, Any] | None = None,
        tool_output: str | None = None,
        is_error: bool = False,
        is_running: bool = False,
        show_details: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.tool_input = tool_input or {}
        self.tool_output = tool_output
        self.is_error = is_error
        self.is_running = is_running
        self.show_details = show_details

        if is_error:
            self.add_class("error")
        elif not is_running and tool_output:
            self.add_class("success")

    def compose(self) -> ComposeResult:
        """Compose the tool view based on type."""
        if self.show_details:
            self.add_class("block")
            yield from self._render_block()
        else:
            self.add_class("inline")
            yield from self._render_inline()

    def _get_icon(self) -> str:
        """Get the icon for this tool type."""
        return self.TOOL_ICONS.get(self.tool_name.lower(), self.TOOL_ICONS["default"])

    def _render_inline(self) -> ComposeResult:
        """Render inline (collapsed) view."""
        icon = self._get_icon()
        summary = self._get_summary()

        text = Text()
        text.append(f" {icon} ", style="dim")
        text.append(self.tool_name, style="bold yellow")
        if summary:
            text.append(f" {summary}", style="dim")

        if self.is_running:
            text.append(" ...", style="dim italic")
        elif self.is_error:
            text.append(" (error)", style="bold red")

        yield Static(text)

    def _render_block(self) -> ComposeResult:
        """Render block (expanded) view."""
        yield from self._render_header()
        yield from self._render_body()

    def _render_header(self) -> ComposeResult:
        """Render the tool header."""
        icon = self._get_icon()
        text = Text()
        text.append(f" {icon} ", style="dim")
        text.append(self.tool_name, style="bold yellow")
        yield Static(text, classes="tool-header")

    def _render_body(self) -> ComposeResult:
        """Render the tool body. Override in subclasses."""
        if self.tool_output:
            yield Static(self.tool_output[:500], classes="tool-output")

    def _get_summary(self) -> str:
        """Get a summary of the tool call. Override in subclasses."""
        return ""


class BashToolView(ToolView):
    """Render bash/shell commands."""

    def _get_summary(self) -> str:
        command = self.tool_input.get("command", "")
        if len(command) > 60:
            command = command[:57] + "..."
        return f'"{command}"'

    def _render_body(self) -> ComposeResult:
        command = self.tool_input.get("command", "")
        yield Static(f"$ {command}", classes="tool-command")

        if self.tool_output:
            # Limit output to first 20 lines
            lines = self.tool_output.split("\n")[:20]
            output = "\n".join(lines)
            if len(lines) < len(self.tool_output.split("\n")):
                output += f"\n... ({len(self.tool_output.split(chr(10)))} total lines)"
            yield Static(output, classes="tool-output")


class GlobToolView(ToolView):
    """Render glob/file search results."""

    def _get_summary(self) -> str:
        pattern = self.tool_input.get("pattern", "")
        if self.tool_output:
            count = len(self.tool_output.strip().split("\n"))
            return f'"{pattern}" ({count} matches)'
        return f'"{pattern}"'

    def _render_body(self) -> ComposeResult:
        pattern = self.tool_input.get("pattern", "")
        yield Static(f"Pattern: {pattern}")

        if self.tool_output:
            files = self.tool_output.strip().split("\n")[:15]
            for f in files:
                yield Static(f"  {f}", classes="file-match")
            if len(files) < len(self.tool_output.strip().split("\n")):
                total = len(self.tool_output.strip().split("\n"))
                yield Static(f"  ... and {total - 15} more", classes="tool-truncated")


class ReadToolView(ToolView):
    """Render file read operations."""

    def _get_summary(self) -> str:
        path = self.tool_input.get("file_path", self.tool_input.get("path", ""))
        if "/" in path:
            path = path.split("/")[-1]
        return path

    def _render_body(self) -> ComposeResult:
        path = self.tool_input.get("file_path", self.tool_input.get("path", ""))
        yield Static(f"File: {path}")

        if self.tool_output:
            # Show first 15 lines with line numbers
            lines = self.tool_output.split("\n")[:15]
            for i, line in enumerate(lines, 1):
                truncated = line[:100] + "..." if len(line) > 100 else line
                yield Static(f"{i:4} | {truncated}")
            if len(lines) < len(self.tool_output.split("\n")):
                total = len(self.tool_output.split("\n"))
                yield Static(f"     ... ({total} total lines)")


class GrepToolView(ToolView):
    """Render grep/search results."""

    def _get_summary(self) -> str:
        pattern = self.tool_input.get("pattern", "")
        if self.tool_output:
            count = len([l for l in self.tool_output.split("\n") if l.strip()])
            return f'"{pattern}" ({count} matches)'
        return f'"{pattern}"'

    def _render_body(self) -> ComposeResult:
        pattern = self.tool_input.get("pattern", "")
        yield Static(f"Search: {pattern}")

        if self.tool_output:
            matches = self.tool_output.strip().split("\n")[:20]
            for match in matches:
                yield Static(f"  {match}", classes="grep-match")


class WriteToolView(ToolView):
    """Render file write operations."""

    def _get_summary(self) -> str:
        path = self.tool_input.get("file_path", self.tool_input.get("path", ""))
        if "/" in path:
            path = path.split("/")[-1]
        return f"Wrote {path}"

    def _render_body(self) -> ComposeResult:
        path = self.tool_input.get("file_path", self.tool_input.get("path", ""))
        content = self.tool_input.get("content", "")
        lines = len(content.split("\n"))
        yield Static(f"# Wrote {path} ({lines} lines)")

        # Show preview of content
        if content:
            preview_lines = content.split("\n")[:10]
            for i, line in enumerate(preview_lines, 1):
                truncated = line[:80] + "..." if len(line) > 80 else line
                text = Text()
                text.append(f"{i:4} ", style="dim")
                text.append(truncated, style="green")
                yield Static(text)


class EditToolView(ToolView):
    """Render file edit operations with diff."""

    def _get_summary(self) -> str:
        path = self.tool_input.get("file_path", self.tool_input.get("path", ""))
        if "/" in path:
            path = path.split("/")[-1]
        return f"Edited {path}"

    def _render_body(self) -> ComposeResult:
        path = self.tool_input.get("file_path", self.tool_input.get("path", ""))
        old = self.tool_input.get("old_string", "")
        new = self.tool_input.get("new_string", "")

        yield Static(f"# Edited {path}")

        # Show diff
        if old:
            for line in old.split("\n")[:5]:
                text = Text()
                text.append("- ", style="bold red")
                text.append(line, style="red")
                yield Static(text)

        if new:
            for line in new.split("\n")[:5]:
                text = Text()
                text.append("+ ", style="bold green")
                text.append(line, style="green")
                yield Static(text)


class TaskToolView(ToolView):
    """Render subagent task execution."""

    def _get_summary(self) -> str:
        desc = self.tool_input.get("description", "")
        agent = self.tool_input.get("subagent_type", "")
        return f"@{agent}: {desc}"

    def _render_body(self) -> ComposeResult:
        desc = self.tool_input.get("description", "")
        agent = self.tool_input.get("subagent_type", "")
        prompt = self.tool_input.get("prompt", "")[:200]

        yield Static(f"@ Agent: {agent}")
        yield Static(f"  Task: {desc}")
        if prompt:
            yield Static(f"  Prompt: {prompt}...")


class TodoWriteToolView(ToolView):
    """Render todo list updates."""

    def _get_summary(self) -> str:
        todos = self.tool_input.get("todos", [])
        if isinstance(todos, list):
            return f"({len(todos)} items)"
        return ""

    def _render_body(self) -> ComposeResult:
        todos = self.tool_input.get("todos", [])
        if not isinstance(todos, list):
            return

        yield Static("Todo List:")
        for todo in todos[:10]:
            if isinstance(todo, dict):
                status = todo.get("status", "pending")
                content = todo.get("content", "")
                icon = {"pending": "[ ]", "in_progress": "[~]", "completed": "[x]"}.get(
                    status, "[ ]"
                )
                style = {
                    "pending": "dim",
                    "in_progress": "yellow",
                    "completed": "green dim",
                }.get(status, "")
                text = Text()
                text.append(f"  {icon} ", style=style)
                text.append(content, style=style)
                yield Static(text)


class QuestionToolView(ToolView):
    """Render question prompts."""

    def _get_summary(self) -> str:
        questions = self.tool_input.get("questions", [])
        if isinstance(questions, list) and questions:
            return f"({len(questions)} questions)"
        return ""


def get_tool_view(
    tool_name: str,
    tool_input: dict[str, Any] | None = None,
    tool_output: str | None = None,
    is_error: bool = False,
    is_running: bool = False,
    show_details: bool = False,
) -> ToolView:
    """Get the appropriate tool view for a tool type."""
    tool_views = {
        "bash": BashToolView,
        "glob": GlobToolView,
        "read": ReadToolView,
        "grep": GrepToolView,
        "write": WriteToolView,
        "edit": EditToolView,
        "task": TaskToolView,
        "todowrite": TodoWriteToolView,
        "question": QuestionToolView,
    }

    view_class = tool_views.get(tool_name.lower(), ToolView)
    return view_class(
        tool_name=tool_name,
        tool_input=tool_input,
        tool_output=tool_output,
        is_error=is_error,
        is_running=is_running,
        show_details=show_details,
    )
