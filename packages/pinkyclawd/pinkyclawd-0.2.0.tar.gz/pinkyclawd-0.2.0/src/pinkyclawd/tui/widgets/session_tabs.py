"""
Session tabs widget with drag-drop reordering.

Matches OpenCode's session tab management:
- Multiple session tabs
- Drag-drop reordering
- Close buttons
- Active indicator
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static, Button
from rich.text import Text


@dataclass
class SessionTabInfo:
    """Information about a session tab."""

    id: str
    title: str
    is_active: bool = False
    is_modified: bool = False
    message_count: int = 0
    model: str | None = None


class SessionTab(Horizontal):
    """Individual session tab."""

    DEFAULT_CSS = """
    SessionTab {
        height: 3;
        min-width: 20;
        max-width: 40;
        padding: 0 1;
        background: $surface;
        border-right: solid $border;
    }

    SessionTab:hover {
        background: $primary 20%;
    }

    SessionTab.active {
        background: $primary 30%;
        border-bottom: thick $primary;
    }

    SessionTab.modified {
        border-left: thick $warning;
    }

    .tab-title {
        width: 1fr;
        text-style: bold;
    }

    .tab-count {
        color: $text-muted;
        padding: 0 1;
    }

    .tab-close {
        width: 3;
        height: 1;
        text-align: center;
        color: $text-muted;
    }

    .tab-close:hover {
        color: $error;
    }
    """

    class Selected(Message):
        """Message sent when tab is selected."""

        def __init__(self, session_id: str) -> None:
            super().__init__()
            self.session_id = session_id

    class CloseRequested(Message):
        """Message sent when tab close is requested."""

        def __init__(self, session_id: str) -> None:
            super().__init__()
            self.session_id = session_id

    def __init__(self, info: SessionTabInfo, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.info = info

        if info.is_active:
            self.add_class("active")
        if info.is_modified:
            self.add_class("modified")

    def compose(self) -> ComposeResult:
        # Title (truncated)
        title = self.info.title[:20]
        if len(self.info.title) > 20:
            title += "..."
        yield Static(title, classes="tab-title")

        # Message count
        if self.info.message_count > 0:
            yield Static(f"({self.info.message_count})", classes="tab-count")

        # Close button
        yield Static("×", classes="tab-close", id=f"close-{self.info.id}")

    def on_click(self) -> None:
        """Handle tab click."""
        self.post_message(self.Selected(self.info.id))

    def on_static_clicked(self, event: Static.Click) -> None:
        """Handle close button click."""
        if event.static.id and event.static.id.startswith("close-"):
            event.stop()
            self.post_message(self.CloseRequested(self.info.id))


class SessionTabBar(Horizontal):
    """
    Tab bar for managing multiple sessions.

    Features:
    - Multiple tabs with titles
    - Active tab indicator
    - Close buttons
    - New session button
    - Tab overflow handling
    """

    BINDINGS = [
        Binding("ctrl+tab", "next_tab", "Next Tab"),
        Binding("ctrl+shift+tab", "prev_tab", "Previous Tab"),
        Binding("ctrl+w", "close_tab", "Close Tab"),
        Binding("ctrl+t", "new_tab", "New Tab"),
    ]

    DEFAULT_CSS = """
    SessionTabBar {
        height: 3;
        width: 100%;
        background: $panel;
        border-bottom: solid $border;
    }

    .tabs-container {
        width: 1fr;
        height: 3;
        overflow-x: auto;
    }

    .tabs-actions {
        width: auto;
        height: 3;
        padding: 0 1;
        background: $surface;
        border-left: solid $border;
    }

    .new-tab-btn {
        width: 3;
        height: 3;
        text-align: center;
        color: $primary;
    }

    .new-tab-btn:hover {
        background: $primary 20%;
    }
    """

    class TabSelected(Message):
        """Message sent when a tab is selected."""

        def __init__(self, session_id: str) -> None:
            super().__init__()
            self.session_id = session_id

    class TabClosed(Message):
        """Message sent when a tab is closed."""

        def __init__(self, session_id: str) -> None:
            super().__init__()
            self.session_id = session_id

    class NewTabRequested(Message):
        """Message sent when new tab is requested."""
        pass

    def __init__(
        self,
        tabs: list[SessionTabInfo] | None = None,
        on_select: Callable[[str], None] | None = None,
        on_close: Callable[[str], None] | None = None,
        on_new: Callable[[], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._tabs = tabs or []
        self._on_select = on_select
        self._on_close = on_close
        self._on_new = on_new

    def compose(self) -> ComposeResult:
        # Tabs container
        with Horizontal(classes="tabs-container"):
            for tab_info in self._tabs:
                yield SessionTab(tab_info)

        # Actions
        with Horizontal(classes="tabs-actions"):
            yield Static("+", classes="new-tab-btn", id="new-tab")

    def on_session_tab_selected(self, event: SessionTab.Selected) -> None:
        """Handle tab selection."""
        self._select_tab(event.session_id)
        self.post_message(self.TabSelected(event.session_id))
        if self._on_select:
            self._on_select(event.session_id)

    def on_session_tab_close_requested(self, event: SessionTab.CloseRequested) -> None:
        """Handle tab close."""
        self.post_message(self.TabClosed(event.session_id))
        if self._on_close:
            self._on_close(event.session_id)

    def on_static_clicked(self, event: Static.Click) -> None:
        """Handle new tab button click."""
        if event.static.id == "new-tab":
            self.post_message(self.NewTabRequested())
            if self._on_new:
                self._on_new()

    def _select_tab(self, session_id: str) -> None:
        """Update tab selection state."""
        for tab_info in self._tabs:
            tab_info.is_active = (tab_info.id == session_id)
        self.refresh(recompose=True)

    def set_tabs(self, tabs: list[SessionTabInfo]) -> None:
        """Set the tab list."""
        self._tabs = tabs
        self.refresh(recompose=True)

    def add_tab(self, tab: SessionTabInfo) -> None:
        """Add a new tab."""
        self._tabs.append(tab)
        self.refresh(recompose=True)

    def remove_tab(self, session_id: str) -> None:
        """Remove a tab by session ID."""
        self._tabs = [t for t in self._tabs if t.id != session_id]
        self.refresh(recompose=True)

    def update_tab(self, session_id: str, **updates: Any) -> None:
        """Update a tab's properties."""
        for tab in self._tabs:
            if tab.id == session_id:
                for key, value in updates.items():
                    if hasattr(tab, key):
                        setattr(tab, key, value)
                break
        self.refresh(recompose=True)

    def action_next_tab(self) -> None:
        """Switch to next tab."""
        if not self._tabs:
            return

        current_idx = next(
            (i for i, t in enumerate(self._tabs) if t.is_active),
            0
        )
        next_idx = (current_idx + 1) % len(self._tabs)
        self._select_tab(self._tabs[next_idx].id)
        self.post_message(self.TabSelected(self._tabs[next_idx].id))

    def action_prev_tab(self) -> None:
        """Switch to previous tab."""
        if not self._tabs:
            return

        current_idx = next(
            (i for i, t in enumerate(self._tabs) if t.is_active),
            0
        )
        prev_idx = (current_idx - 1) % len(self._tabs)
        self._select_tab(self._tabs[prev_idx].id)
        self.post_message(self.TabSelected(self._tabs[prev_idx].id))

    def action_close_tab(self) -> None:
        """Close current tab."""
        for tab in self._tabs:
            if tab.is_active:
                self.post_message(self.TabClosed(tab.id))
                if self._on_close:
                    self._on_close(tab.id)
                break

    def action_new_tab(self) -> None:
        """Create new tab."""
        self.post_message(self.NewTabRequested())
        if self._on_new:
            self._on_new()


class SessionManager(Vertical):
    """
    Complete session management widget.

    Features:
    - Session tabs
    - Session list (for overflow)
    - Quick session switching
    - Session metadata
    """

    DEFAULT_CSS = """
    SessionManager {
        height: auto;
    }

    .session-info {
        height: 2;
        padding: 0 1;
        background: $surface;
        border-bottom: solid $border;
    }

    .session-title {
        text-style: bold;
    }

    .session-meta {
        color: $text-muted;
    }
    """

    def __init__(
        self,
        tabs: list[SessionTabInfo] | None = None,
        current_session: SessionTabInfo | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._tabs = tabs or []
        self._current = current_session

    def compose(self) -> ComposeResult:
        yield SessionTabBar(tabs=self._tabs, id="tab-bar")

        if self._current:
            with Horizontal(classes="session-info"):
                yield Static(self._current.title, classes="session-title")
                meta = Text()
                if self._current.model:
                    meta.append(f" | {self._current.model}", style="dim")
                if self._current.message_count:
                    meta.append(f" | {self._current.message_count} messages", style="dim")
                yield Static(meta, classes="session-meta")

    def set_current_session(self, session: SessionTabInfo) -> None:
        """Set the current session."""
        self._current = session
        self.refresh(recompose=True)

    def on_session_tab_bar_tab_selected(self, event: SessionTabBar.TabSelected) -> None:
        """Forward tab selection."""
        for tab in self._tabs:
            if tab.id == event.session_id:
                self.set_current_session(tab)
                break
