"""
Sidebar widget with session info, context usage, MCP/LSP status, todos, and diffs.

Matches OpenCode's sidebar with expandable sections.
"""

from __future__ import annotations

from typing import Any

from textual.widgets import Static, ListView, ListItem, Label, Collapsible
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from rich.text import Text

from pinkyclawd.config.storage import Session


class SessionItem(ListItem):
    """A session item in the sidebar list."""

    def __init__(self, session: Session, is_current: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.session = session
        self.is_current = is_current

    def compose(self) -> ComposeResult:
        text = Text()
        if self.is_current:
            text.append("* ", style="bold green")
        text.append(self.session.title or "Untitled", style="bold" if self.is_current else "")
        yield Label(text)


class ContextUsage(Static):
    """Display context token usage."""

    DEFAULT_CSS = """
    ContextUsage {
        padding: 1;
        background: $surface;
    }

    .context-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .context-bar {
        height: 1;
        background: $primary 20%;
    }

    .context-bar-fill {
        height: 1;
        background: $primary;
    }

    .context-stats {
        color: $text-muted;
        margin-top: 1;
    }
    """

    tokens: reactive[int] = reactive(0)
    limit: reactive[int] = reactive(200000)
    cost: reactive[float] = reactive(0.0)

    def compose(self) -> ComposeResult:
        yield Static("Context", classes="context-title")

        # Progress bar
        percentage = min(100, (self.tokens / self.limit * 100) if self.limit else 0)
        bar_width = 20
        fill_width = int(bar_width * percentage / 100)

        bar = Text()
        bar.append("█" * fill_width, style="green" if percentage < 80 else "yellow" if percentage < 95 else "red")
        bar.append("░" * (bar_width - fill_width), style="dim")
        bar.append(f" {percentage:.1f}%", style="dim")
        yield Static(bar)

        # Stats
        stats = Text()
        stats.append(f"{self.tokens:,}", style="bold")
        stats.append(f" / {self.limit:,} tokens", style="dim")
        if self.cost > 0:
            stats.append(f" | ${self.cost:.4f}", style="green dim")
        yield Static(stats, classes="context-stats")


class MCPStatus(Collapsible):
    """Display MCP server connection status."""

    DEFAULT_CSS = """
    MCPStatus {
        margin: 1 0;
    }

    .mcp-server {
        padding: 0 1;
    }

    .mcp-connected {
        color: $success;
    }

    .mcp-disconnected {
        color: $error;
    }

    .mcp-connecting {
        color: $warning;
    }
    """

    def __init__(
        self,
        servers: dict[str, dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        connected = sum(1 for s in (servers or {}).values() if s.get("status") == "connected")
        total = len(servers or {})
        super().__init__(title=f"MCP ({connected}/{total})", collapsed=True, **kwargs)
        self.servers = servers or {}

    def compose(self) -> ComposeResult:
        if not self.servers:
            yield Static("No MCP servers configured", classes="mcp-server")
            return

        for name, status in self.servers.items():
            state = status.get("status", "disconnected")
            icon = {"connected": "●", "connecting": "◐", "disconnected": "○"}.get(state, "○")
            style_class = f"mcp-{state}"

            text = Text()
            text.append(f" {icon} ", style=style_class.replace("mcp-", ""))
            text.append(name, style="bold" if state == "connected" else "dim")

            error = status.get("error")
            if error:
                text.append(f"\n    {error[:40]}...", style="dim red")

            yield Static(text, classes="mcp-server")


class LSPStatus(Collapsible):
    """Display LSP server status."""

    DEFAULT_CSS = """
    LSPStatus {
        margin: 1 0;
    }

    .lsp-server {
        padding: 0 1;
    }
    """

    def __init__(
        self,
        servers: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(title=f"LSP ({len(servers or [])})", collapsed=True, **kwargs)
        self.servers = servers or []

    def compose(self) -> ComposeResult:
        if not self.servers:
            yield Static("No LSP servers running", classes="lsp-server")
            return

        for server in self.servers:
            name = server.get("name", "unknown")
            language = server.get("language", "")
            text = Text()
            text.append(f" ● {name}", style="bold")
            if language:
                text.append(f" ({language})", style="dim")
            yield Static(text, classes="lsp-server")


class TodoList(Collapsible):
    """Display current todo items."""

    DEFAULT_CSS = """
    TodoList {
        margin: 1 0;
    }

    .todo-item {
        padding: 0 1;
    }

    .todo-pending {
        color: $text-muted;
    }

    .todo-in-progress {
        color: $warning;
    }

    .todo-completed {
        color: $success;
        text-style: dim;
    }
    """

    def __init__(
        self,
        todos: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        completed = sum(1 for t in (todos or []) if t.get("status") == "completed")
        total = len(todos or [])
        super().__init__(title=f"Todos ({completed}/{total})", collapsed=True, **kwargs)
        self.todos = todos or []

    def compose(self) -> ComposeResult:
        if not self.todos:
            yield Static("No todos", classes="todo-item")
            return

        for todo in self.todos[:10]:
            status = todo.get("status", "pending")
            content = todo.get("content", "")
            active = todo.get("activeForm", content)

            icon = {"pending": "[ ]", "in_progress": "[~]", "completed": "[x]"}.get(status, "[ ]")

            text = Text()
            text.append(f" {icon} ", style=f"todo-{status}".replace("_", "-"))
            text.append(
                active if status == "in_progress" else content,
                style=f"todo-{status}".replace("_", "-"),
            )
            yield Static(text, classes="todo-item")


class DiffSummary(Collapsible):
    """Display modified files summary."""

    DEFAULT_CSS = """
    DiffSummary {
        margin: 1 0;
    }

    .diff-file {
        padding: 0 1;
    }

    .diff-added {
        color: $success;
    }

    .diff-removed {
        color: $error;
    }
    """

    def __init__(
        self,
        files: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(title=f"Modified ({len(files or [])})", collapsed=True, **kwargs)
        self.files = files or []

    def compose(self) -> ComposeResult:
        if not self.files:
            yield Static("No modified files", classes="diff-file")
            return

        for file in self.files[:10]:
            path = file.get("path", "")
            if "/" in path:
                path = path.split("/")[-1]
            added = file.get("added", 0)
            removed = file.get("removed", 0)

            text = Text()
            text.append(f" {path} ", style="bold")
            if added:
                text.append(f"+{added}", style="green")
            if removed:
                if added:
                    text.append(" ")
                text.append(f"-{removed}", style="red")

            yield Static(text, classes="diff-file")


class Sidebar(Vertical):
    """
    Sidebar with comprehensive session information.

    Features:
    - Session metadata (title, share URL)
    - Context usage (tokens, percentage, cost)
    - MCP server status (expandable)
    - LSP server list
    - Todo items (expandable)
    - Modified files diff summary
    - Recent sessions list
    """

    DEFAULT_CSS = """
    Sidebar {
        width: 32;
        background: $panel;
        border-right: solid $border;
    }

    .sidebar-header {
        height: 3;
        padding: 1;
        text-align: center;
        text-style: bold;
        background: $primary 30%;
    }

    .sidebar-section {
        padding: 1;
        border-bottom: solid $border;
    }

    .section-title {
        text-style: bold;
        color: $text-muted;
        margin-bottom: 1;
    }

    .session-info {
        padding: 1;
    }

    .session-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .session-share {
        color: $info;
        text-style: underline;
    }

    .session-list {
        height: auto;
        max-height: 15;
    }

    .sidebar-footer {
        height: auto;
        padding: 1;
        border-top: solid $border;
    }

    .shortcuts {
        color: $text-muted;
    }
    """

    class SessionSelected(Message):
        """Message sent when a session is selected."""

        def __init__(self, session_id: str) -> None:
            super().__init__()
            self.session_id = session_id

    def __init__(
        self,
        sessions: list[Session] | None = None,
        current_session: Session | None = None,
        mcp_servers: dict[str, dict[str, Any]] | None = None,
        lsp_servers: list[dict[str, Any]] | None = None,
        todos: list[dict[str, Any]] | None = None,
        modified_files: list[dict[str, Any]] | None = None,
        context_tokens: int = 0,
        context_limit: int = 200000,
        context_cost: float = 0.0,
        share_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.sessions = sessions or []
        self.current_session = current_session
        self.mcp_servers = mcp_servers or {}
        self.lsp_servers = lsp_servers or []
        self.todos = todos or []
        self.modified_files = modified_files or []
        self.context_tokens = context_tokens
        self.context_limit = context_limit
        self.context_cost = context_cost
        self.share_url = share_url

    def compose(self) -> ComposeResult:
        # Logo/Header
        yield Static("PinkyClawd", classes="sidebar-header")

        # Session info section
        with Vertical(classes="session-info"):
            if self.current_session:
                yield Static(self.current_session.title or "Untitled", classes="session-title")
                if self.share_url:
                    yield Static(f"Share: {self.share_url}", classes="session-share")

        # Context usage
        context = ContextUsage()
        context.tokens = self.context_tokens
        context.limit = self.context_limit
        context.cost = self.context_cost
        yield context

        # MCP Status
        yield MCPStatus(self.mcp_servers)

        # LSP Status
        yield LSPStatus(self.lsp_servers)

        # Todos
        yield TodoList(self.todos)

        # Modified files
        yield DiffSummary(self.modified_files)

        # Sessions section
        with Vertical(classes="sidebar-section"):
            yield Static("Recent Sessions", classes="section-title")
            session_list = ListView(classes="session-list")
            for session in self.sessions[:8]:
                is_current = (
                    self.current_session and session.id == self.current_session.id
                )
                session_list.append(SessionItem(session, is_current=is_current))
            yield session_list

        # Footer with shortcuts
        with Vertical(classes="sidebar-footer"):
            yield Static("[N] New  [S] Share  [?] Help", classes="shortcuts")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle session selection."""
        if isinstance(event.item, SessionItem):
            self.post_message(self.SessionSelected(event.item.session.id))

    def update_context(
        self,
        tokens: int,
        limit: int,
        cost: float = 0.0,
    ) -> None:
        """Update context usage display."""
        self.context_tokens = tokens
        self.context_limit = limit
        self.context_cost = cost
        try:
            context = self.query_one(ContextUsage)
            context.tokens = tokens
            context.limit = limit
            context.cost = cost
        except Exception:
            pass

    def update_todos(self, todos: list[dict[str, Any]]) -> None:
        """Update todo list."""
        self.todos = todos
        self.refresh(recompose=True)

    def update_mcp(self, servers: dict[str, dict[str, Any]]) -> None:
        """Update MCP status."""
        self.mcp_servers = servers
        self.refresh(recompose=True)

    def update_sessions(self, sessions: list[Session]) -> None:
        """Update the session list."""
        self.sessions = sessions
        try:
            session_list = self.query_one(".session-list", ListView)
            session_list.clear()
            for session in sessions[:8]:
                is_current = (
                    self.current_session and session.id == self.current_session.id
                )
                session_list.append(SessionItem(session, is_current=is_current))
        except Exception:
            pass

    def set_current_session(self, session: Session) -> None:
        """Set the current session."""
        self.current_session = session
        self.refresh(recompose=True)
