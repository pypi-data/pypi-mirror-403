"""
Session management dialog.

Allows users to view, switch, rename, and delete sessions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Static, ListView, ListItem, Label, Input, Button

from pinkyclawd.session.manager import SessionInfo, get_session_manager


class SessionListItem(ListItem):
    """A list item for a session."""

    def __init__(self, session: SessionInfo, is_current: bool = False) -> None:
        super().__init__()
        self.session = session
        self.is_current = is_current

    def compose(self) -> ComposeResult:
        with Container(classes="session-item"):
            with Horizontal():
                yield Label(self.session.title, classes="session-title")
                if self.is_current:
                    yield Label("(current)", classes="session-current")
                yield Label(
                    self._format_time(self.session.updated_at),
                    classes="session-time",
                )
            with Horizontal(classes="session-meta"):
                yield Label(f"{self.session.message_count} messages", classes="session-messages")
                if self.session.is_archived:
                    yield Label("archived", classes="session-archived")

    def _format_time(self, dt: datetime) -> str:
        """Format datetime as relative time."""
        now = datetime.now()
        diff = now - dt

        if diff.days > 7:
            return dt.strftime("%b %d")
        if diff.days > 0:
            return f"{diff.days}d ago"
        if diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        if diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        return "just now"


class SessionDialog(
    ModalScreen[tuple[Literal["switch", "delete", "rename", "fork", "export"], SessionInfo] | None]
):
    """
    Session management modal dialog.

    Shows sessions with options to switch, rename, delete, fork, or export.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "switch", "Switch"),
        Binding("d", "delete", "Delete"),
        Binding("r", "rename", "Rename"),
        Binding("f", "fork", "Fork"),
        Binding("e", "export", "Export"),
        Binding("up", "cursor_up", "Up"),
        Binding("down", "cursor_down", "Down"),
    ]

    CSS = """
    SessionDialog {
        align: center middle;
    }

    SessionDialog > Container {
        width: 80;
        max-width: 90%;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: tall $primary;
        padding: 1;
    }

    SessionDialog .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    SessionDialog ListView {
        height: auto;
        max-height: 20;
    }

    .session-item {
        padding: 0 1;
    }

    .session-item Horizontal {
        height: 1;
    }

    .session-title {
        width: 1fr;
        text-style: bold;
    }

    .session-current {
        color: $success;
        margin: 0 1;
    }

    .session-time {
        width: auto;
        color: $text-muted;
    }

    .session-meta {
        padding-left: 2;
    }

    .session-messages {
        color: $text-muted;
        margin-right: 2;
    }

    .session-archived {
        color: $warning;
    }

    SessionDialog ListItem {
        padding: 0;
        height: 3;
    }

    SessionDialog ListItem:hover {
        background: $primary 20%;
    }

    SessionDialog ListItem.-selected {
        background: $primary 40%;
    }

    .actions {
        margin-top: 1;
        height: 1;
    }

    .actions Label {
        margin-right: 2;
        color: $text-muted;
    }

    .rename-input {
        display: none;
        margin-top: 1;
    }

    .rename-input.visible {
        display: block;
    }
    """

    def __init__(
        self,
        current_session_id: str | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self._manager = get_session_manager()
        self._current_session_id = current_session_id
        self._sessions: list[SessionInfo] = []
        self._rename_mode = False

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Sessions", classes="title")
            yield ListView(id="session-list")
            with Horizontal(classes="actions"):
                yield Label("[Enter] Switch")
                yield Label("[R] Rename")
                yield Label("[F] Fork")
                yield Label("[D] Delete")
                yield Label("[E] Export")
            with Container(classes="rename-input", id="rename-container"):
                yield Input(placeholder="New name...", id="rename-input")

    def on_mount(self) -> None:
        """Populate the session list."""
        self._refresh_list()

    def _refresh_list(self) -> None:
        """Refresh the session list."""
        list_view = self.query_one("#session-list", ListView)
        list_view.clear()

        self._sessions = self._manager.list(limit=50)

        current_index = 0
        for i, session in enumerate(self._sessions):
            is_current = session.id == self._current_session_id
            if is_current:
                current_index = i
            list_view.append(SessionListItem(session, is_current))

        if self._sessions:
            list_view.index = current_index

    def _get_selected(self) -> SessionInfo | None:
        """Get the currently selected session."""
        list_view = self.query_one("#session-list", ListView)
        if list_view.index is not None and self._sessions:
            return self._sessions[list_view.index]
        return None

    def action_cancel(self) -> None:
        """Cancel dialog."""
        if self._rename_mode:
            self._exit_rename_mode()
        else:
            self.dismiss(None)

    def action_switch(self) -> None:
        """Switch to selected session."""
        if self._rename_mode:
            self._confirm_rename()
            return

        selected = self._get_selected()
        if selected:
            self.dismiss(("switch", selected))

    def action_delete(self) -> None:
        """Delete selected session."""
        selected = self._get_selected()
        if selected and selected.id != self._current_session_id:
            self.dismiss(("delete", selected))

    def action_rename(self) -> None:
        """Enter rename mode."""
        selected = self._get_selected()
        if selected:
            self._enter_rename_mode(selected)

    def action_fork(self) -> None:
        """Fork selected session."""
        selected = self._get_selected()
        if selected:
            self.dismiss(("fork", selected))

    def action_export(self) -> None:
        """Export selected session."""
        selected = self._get_selected()
        if selected:
            self.dismiss(("export", selected))

    def _enter_rename_mode(self, session: SessionInfo) -> None:
        """Enter rename mode for a session."""
        self._rename_mode = True
        container = self.query_one("#rename-container")
        container.add_class("visible")

        input_widget = self.query_one("#rename-input", Input)
        input_widget.value = session.title
        input_widget.focus()

    def _exit_rename_mode(self) -> None:
        """Exit rename mode."""
        self._rename_mode = False
        container = self.query_one("#rename-container")
        container.remove_class("visible")

    def _confirm_rename(self) -> None:
        """Confirm the rename."""
        selected = self._get_selected()
        input_widget = self.query_one("#rename-input", Input)
        new_name = input_widget.value.strip()

        if selected and new_name:
            self.dismiss(
                (
                    "rename",
                    SessionInfo(
                        id=selected.id,
                        title=new_name,  # New title
                        directory=selected.directory,
                        message_count=selected.message_count,
                        created_at=selected.created_at,
                        updated_at=selected.updated_at,
                        is_archived=selected.is_archived,
                    ),
                )
            )
        else:
            self._exit_rename_mode()

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        list_view = self.query_one("#session-list", ListView)
        if list_view.index is not None and list_view.index > 0:
            list_view.index -= 1

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        list_view = self.query_one("#session-list", ListView)
        if list_view.index is not None:
            if list_view.index < len(self._sessions) - 1:
                list_view.index += 1

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection."""
        if isinstance(event.item, SessionListItem):
            self.dismiss(("switch", event.item.session))


class SessionRenameDialog(ModalScreen[str | None]):
    """Dialog for renaming a session."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    CSS = """
    SessionRenameDialog {
        align: center middle;
    }

    SessionRenameDialog > Container {
        width: 60;
        height: auto;
        background: $surface;
        border: tall $primary;
        padding: 2;
    }

    .dialog-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    SessionRenameDialog Input {
        margin: 1 0;
    }

    .button-row {
        margin-top: 1;
        align: center middle;
    }

    .button-row Button {
        margin: 0 1;
    }
    """

    def __init__(self, current_title: str = "") -> None:
        super().__init__()
        self.current_title = current_title

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Rename Session", classes="dialog-title")
            yield Input(value=self.current_title, placeholder="Enter new name...", id="name")
            with Horizontal(classes="button-row"):
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Rename", variant="primary", id="rename")

    def on_mount(self) -> None:
        inp = self.query_one("#name", Input)
        inp.focus()
        inp.cursor_position = len(self.current_title)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "rename":
            name = self.query_one("#name", Input).value.strip()
            if name:
                self.dismiss(name)

    def action_cancel(self) -> None:
        self.dismiss(None)


class SessionShareDialog(ModalScreen[str | None]):
    """Dialog showing share URL."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("c", "copy", "Copy"),
    ]

    CSS = """
    SessionShareDialog {
        align: center middle;
    }

    SessionShareDialog > Container {
        width: 70;
        height: auto;
        background: $surface;
        border: tall $primary;
        padding: 2;
    }

    .dialog-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    .share-url {
        padding: 1;
        background: $panel;
        text-align: center;
        margin: 1 0;
    }

    .dialog-footer {
        text-align: center;
        color: $text-muted;
    }
    """

    def __init__(self, share_url: str) -> None:
        super().__init__()
        self.share_url = share_url

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Share Session", classes="dialog-title")
            yield Static("Your session share URL:")
            yield Static(self.share_url, classes="share-url", id="url")
            yield Static("[C] Copy to clipboard  [Esc] Close", classes="dialog-footer")

    def action_close(self) -> None:
        self.dismiss(None)

    def action_copy(self) -> None:
        self.dismiss(self.share_url)


class SessionExportDialog(ModalScreen[tuple[str, str] | None]):
    """Dialog for exporting session to file."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    CSS = """
    SessionExportDialog {
        align: center middle;
    }

    SessionExportDialog > Container {
        width: 60;
        height: auto;
        background: $surface;
        border: tall $primary;
        padding: 2;
    }

    .dialog-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    SessionExportDialog ListView {
        height: 5;
        margin: 1 0;
    }

    SessionExportDialog Input {
        margin: 1 0;
    }

    .button-row {
        margin-top: 1;
        align: center middle;
    }

    .button-row Button {
        margin: 0 1;
    }
    """

    def __init__(self, default_name: str = "session") -> None:
        super().__init__()
        self.default_name = default_name

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Export Session", classes="dialog-title")
            yield Static("Export format:")
            yield ListView(id="format-list")
            yield Static("Filename:")
            yield Input(value=f"{self.default_name}.md", placeholder="filename.md", id="filename")
            with Horizontal(classes="button-row"):
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Export", variant="primary", id="export")

    def on_mount(self) -> None:
        list_view = self.query_one("#format-list", ListView)
        list_view.append(ListItem(Label("Markdown (.md) - Human-readable format")))
        list_view.append(ListItem(Label("JSON (.json) - Machine-readable format")))
        list_view.append(ListItem(Label("Text (.txt) - Plain text format")))
        list_view.index = 0

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "export":
            filename = self.query_one("#filename", Input).value.strip()
            list_view = self.query_one("#format-list", ListView)
            formats = ["md", "json", "txt"]
            format_type = formats[list_view.index] if list_view.index is not None else "md"
            if filename:
                self.dismiss((filename, format_type))

    def action_cancel(self) -> None:
        self.dismiss(None)


class TimelineDialog(ModalScreen[int | None]):
    """Timeline navigation dialog showing message history."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select", "Jump"),
    ]

    CSS = """
    TimelineDialog {
        align: center middle;
    }

    TimelineDialog > Container {
        width: 80;
        max-width: 90%;
        height: 80%;
        background: $surface;
        border: tall $primary;
        padding: 1;
    }

    .dialog-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    TimelineDialog ListView {
        height: 1fr;
    }

    TimelineDialog ListItem {
        padding: 1;
    }

    .dialog-footer {
        height: 2;
        margin-top: 1;
        color: $text-muted;
    }
    """

    def __init__(self, messages: list, current_index: int = -1) -> None:
        super().__init__()
        self.messages = messages
        self.current_index = current_index if current_index >= 0 else len(messages) - 1

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Timeline", classes="dialog-title")
            yield ListView(id="timeline-list")
            yield Static("[Enter] Jump to message  [Esc] Cancel", classes="dialog-footer")

    def on_mount(self) -> None:
        from rich.text import Text

        list_view = self.query_one("#timeline-list", ListView)

        for i, msg in enumerate(self.messages):
            role = getattr(msg, "role", "unknown")
            role_str = role.value if hasattr(role, "value") else str(role)
            created = getattr(msg, "created_at", None)
            time_str = created.strftime("%H:%M") if created else ""

            # Get content preview
            content = ""
            parts = getattr(msg, "parts", [])
            for part in parts:
                if hasattr(part, "content") and isinstance(part.content, dict):
                    content = part.content.get("text", "")[:50]
                    break
            if not content:
                content = str(getattr(msg, "content", ""))[:50]

            text = Text()
            text.append(f"{time_str} ", style="dim")
            text.append(f"[{role_str}] ", style="bold")
            text.append(content + "..." if len(content) == 50 else content)
            if i == self.current_index:
                text.append(" <", style="bold yellow")

            list_view.append(ListItem(Label(text)))

        if self.messages:
            list_view.index = self.current_index

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_select(self) -> None:
        list_view = self.query_one("#timeline-list", ListView)
        if list_view.index is not None:
            self.dismiss(list_view.index)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        list_view = self.query_one("#timeline-list", ListView)
        if list_view.index is not None:
            self.dismiss(list_view.index)
