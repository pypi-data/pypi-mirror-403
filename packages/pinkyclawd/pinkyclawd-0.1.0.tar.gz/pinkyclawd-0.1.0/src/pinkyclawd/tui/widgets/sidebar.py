"""
Sidebar widget for session and project navigation.
"""

from __future__ import annotations

from typing import Any

from textual.widgets import Static, ListView, ListItem, Label
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.message import Message

from pinkyclawd.config.storage import Session


class SessionItem(ListItem):
    """A session item in the sidebar list."""

    def __init__(self, session: Session, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.session = session

    def compose(self) -> ComposeResult:
        yield Label(self.session.title or "Untitled")


class Sidebar(Vertical):
    """
    Sidebar with session list and navigation.

    Features:
    - Recent sessions list
    - Project switcher
    - Settings access
    - Help access
    """

    DEFAULT_CSS = """
    Sidebar {
        width: 30;
        background: $panel;
        border-right: solid $primary;
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
    }

    .section-title {
        text-style: bold;
        margin-bottom: 1;
        color: $text-muted;
    }

    .session-list {
        height: 1fr;
    }

    .sidebar-footer {
        height: auto;
        padding: 1;
        border-top: solid $border;
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
        current_session_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.sessions = sessions or []
        self.current_session_id = current_session_id

    def compose(self) -> ComposeResult:
        # Logo/Header
        yield Static("PinkyClawd", classes="sidebar-header")

        # Sessions section
        with Vertical(classes="sidebar-section"):
            yield Static("Sessions", classes="section-title")

            session_list = ListView(classes="session-list")
            for session in self.sessions[:10]:  # Show last 10
                session_list.append(SessionItem(session))
            yield session_list

        # Footer with shortcuts
        with Vertical(classes="sidebar-footer"):
            yield Static("[N] New  [L] List  [?] Help")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle session selection."""
        if isinstance(event.item, SessionItem):
            self.post_message(self.SessionSelected(event.item.session.id))

    def update_sessions(self, sessions: list[Session]) -> None:
        """Update the session list."""
        self.sessions = sessions
        # Re-render session list
        session_list = self.query_one(".session-list", ListView)
        session_list.clear()
        for session in sessions[:10]:
            session_list.append(SessionItem(session))

    def set_current_session(self, session_id: str) -> None:
        """Highlight the current session."""
        self.current_session_id = session_id
        # Update highlighting in list
