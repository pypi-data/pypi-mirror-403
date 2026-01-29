"""
Layout system with resizable panels.

Matches OpenCode's layout with:
- Resizable sidebar
- Resizable terminal panel
- Flexible content area
- Panel visibility toggles
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, Container
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static


class PanelPosition(Enum):
    """Panel position in the layout."""

    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


@dataclass
class PanelState:
    """State of a panel."""

    visible: bool = True
    size: int = 30  # Width or height depending on position
    min_size: int = 10
    max_size: int = 100
    collapsed: bool = False


class ResizeHandle(Static):
    """Draggable resize handle for panels."""

    DEFAULT_CSS = """
    ResizeHandle {
        width: 1;
        height: 100%;
        background: $border;
    }

    ResizeHandle:hover {
        background: $primary;
        cursor: ew-resize;
    }

    ResizeHandle.horizontal {
        width: 100%;
        height: 1;
    }

    ResizeHandle.horizontal:hover {
        cursor: ns-resize;
    }

    ResizeHandle.dragging {
        background: $accent;
    }
    """

    class Dragging(Message):
        """Message sent while dragging."""

        def __init__(self, delta: int, horizontal: bool) -> None:
            super().__init__()
            self.delta = delta
            self.horizontal = horizontal

    class DragStart(Message):
        """Message sent when drag starts."""
        pass

    class DragEnd(Message):
        """Message sent when drag ends."""
        pass

    def __init__(self, horizontal: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._horizontal = horizontal
        self._dragging = False
        self._start_pos = 0

        if horizontal:
            self.add_class("horizontal")

    def on_mouse_down(self, event) -> None:
        """Start dragging."""
        self._dragging = True
        self._start_pos = event.y if self._horizontal else event.x
        self.add_class("dragging")
        self.capture_mouse()
        self.post_message(self.DragStart())

    def on_mouse_up(self, event) -> None:
        """Stop dragging."""
        if self._dragging:
            self._dragging = False
            self.remove_class("dragging")
            self.release_mouse()
            self.post_message(self.DragEnd())

    def on_mouse_move(self, event) -> None:
        """Handle drag movement."""
        if self._dragging:
            current = event.y if self._horizontal else event.x
            delta = current - self._start_pos
            if delta != 0:
                self.post_message(self.Dragging(delta, self._horizontal))
                self._start_pos = current


class Panel(Vertical):
    """
    A panel in the layout with resize support.

    Features:
    - Resize handle
    - Visibility toggle
    - Min/max size constraints
    """

    DEFAULT_CSS = """
    Panel {
        height: 100%;
    }

    Panel.left {
        border-right: solid $border;
    }

    Panel.right {
        border-left: solid $border;
    }

    Panel.top {
        border-bottom: solid $border;
    }

    Panel.bottom {
        border-top: solid $border;
    }

    Panel.collapsed {
        display: none;
    }

    .panel-content {
        height: 1fr;
        overflow: auto;
    }
    """

    visible: reactive[bool] = reactive(True)
    size: reactive[int] = reactive(30)

    class Resized(Message):
        """Message sent when panel is resized."""

        def __init__(self, new_size: int) -> None:
            super().__init__()
            self.new_size = new_size

    def __init__(
        self,
        position: PanelPosition = PanelPosition.LEFT,
        initial_size: int = 30,
        min_size: int = 10,
        max_size: int = 100,
        resizable: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.position = position
        self.size = initial_size
        self.min_size = min_size
        self.max_size = max_size
        self.resizable = resizable

        self.add_class(position.value)

    def compose(self) -> ComposeResult:
        # Resize handle (left/top panels have handle on right/bottom)
        if self.resizable:
            if self.position in (PanelPosition.LEFT, PanelPosition.RIGHT):
                yield ResizeHandle(horizontal=False)
            else:
                yield ResizeHandle(horizontal=True)

        # Content container
        yield Container(classes="panel-content", id="panel-content")

    def watch_visible(self, visible: bool) -> None:
        """React to visibility changes."""
        if visible:
            self.remove_class("collapsed")
        else:
            self.add_class("collapsed")

    def on_resize_handle_dragging(self, event: ResizeHandle.Dragging) -> None:
        """Handle resize."""
        if self.position in (PanelPosition.LEFT, PanelPosition.TOP):
            new_size = self.size + event.delta
        else:
            new_size = self.size - event.delta

        new_size = max(self.min_size, min(self.max_size, new_size))

        if new_size != self.size:
            self.size = new_size
            self._update_size()
            self.post_message(self.Resized(new_size))

    def _update_size(self) -> None:
        """Update the panel's size style."""
        if self.position in (PanelPosition.LEFT, PanelPosition.RIGHT):
            self.styles.width = self.size
        else:
            self.styles.height = self.size

    def toggle(self) -> None:
        """Toggle panel visibility."""
        self.visible = not self.visible

    def show(self) -> None:
        """Show the panel."""
        self.visible = True

    def hide(self) -> None:
        """Hide the panel."""
        self.visible = False

    def set_content(self, *children) -> None:
        """Set the panel content."""
        content = self.query_one("#panel-content", Container)
        content.remove_children()
        for child in children:
            content.mount(child)


class FlexLayout(Horizontal):
    """
    Flexible layout with resizable panels.

    Features:
    - Left/right sidebars
    - Bottom panel (terminal/output)
    - Central content area
    - Panel state persistence
    """

    BINDINGS = [
        Binding("ctrl+b", "toggle_sidebar", "Toggle Sidebar"),
        Binding("ctrl+`", "toggle_terminal", "Toggle Terminal"),
        Binding("ctrl+e", "toggle_explorer", "Toggle Explorer"),
    ]

    DEFAULT_CSS = """
    FlexLayout {
        width: 100%;
        height: 100%;
    }

    .layout-main {
        width: 1fr;
        height: 100%;
    }

    .layout-content {
        height: 1fr;
    }

    #sidebar {
        width: 32;
        min-width: 20;
        max-width: 60;
    }

    #explorer {
        width: 28;
        min-width: 15;
        max-width: 50;
    }

    #terminal-panel {
        height: 20;
        min-height: 5;
        max-height: 40;
    }
    """

    sidebar_visible: reactive[bool] = reactive(True)
    explorer_visible: reactive[bool] = reactive(False)
    terminal_visible: reactive[bool] = reactive(False)

    class LayoutChanged(Message):
        """Message sent when layout changes."""

        def __init__(self, panel: str, visible: bool) -> None:
            super().__init__()
            self.panel = panel
            self.visible = visible

    def __init__(
        self,
        show_sidebar: bool = True,
        show_explorer: bool = False,
        show_terminal: bool = False,
        sidebar_width: int = 32,
        explorer_width: int = 28,
        terminal_height: int = 20,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.sidebar_visible = show_sidebar
        self.explorer_visible = show_explorer
        self.terminal_visible = show_terminal
        self._sidebar_width = sidebar_width
        self._explorer_width = explorer_width
        self._terminal_height = terminal_height

    def compose(self) -> ComposeResult:
        # Left sidebar
        sidebar = Panel(
            position=PanelPosition.LEFT,
            initial_size=self._sidebar_width,
            id="sidebar",
        )
        sidebar.visible = self.sidebar_visible
        yield sidebar

        # Main area (content + terminal)
        with Vertical(classes="layout-main"):
            # Content area with optional explorer
            with Horizontal(classes="layout-content"):
                # Explorer panel
                explorer = Panel(
                    position=PanelPosition.LEFT,
                    initial_size=self._explorer_width,
                    id="explorer",
                )
                explorer.visible = self.explorer_visible
                yield explorer

                # Main content
                yield Container(id="main-content")

            # Terminal panel
            terminal = Panel(
                position=PanelPosition.BOTTOM,
                initial_size=self._terminal_height,
                id="terminal-panel",
            )
            terminal.visible = self.terminal_visible
            yield terminal

    def watch_sidebar_visible(self, visible: bool) -> None:
        """React to sidebar visibility changes."""
        try:
            sidebar = self.query_one("#sidebar", Panel)
            sidebar.visible = visible
            self.post_message(self.LayoutChanged("sidebar", visible))
        except Exception:
            pass

    def watch_explorer_visible(self, visible: bool) -> None:
        """React to explorer visibility changes."""
        try:
            explorer = self.query_one("#explorer", Panel)
            explorer.visible = visible
            self.post_message(self.LayoutChanged("explorer", visible))
        except Exception:
            pass

    def watch_terminal_visible(self, visible: bool) -> None:
        """React to terminal visibility changes."""
        try:
            terminal = self.query_one("#terminal-panel", Panel)
            terminal.visible = visible
            self.post_message(self.LayoutChanged("terminal", visible))
        except Exception:
            pass

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        self.sidebar_visible = not self.sidebar_visible

    def action_toggle_terminal(self) -> None:
        """Toggle terminal visibility."""
        self.terminal_visible = not self.terminal_visible

    def action_toggle_explorer(self) -> None:
        """Toggle explorer visibility."""
        self.explorer_visible = not self.explorer_visible

    def set_sidebar_content(self, *children) -> None:
        """Set sidebar content."""
        sidebar = self.query_one("#sidebar", Panel)
        sidebar.set_content(*children)

    def set_explorer_content(self, *children) -> None:
        """Set explorer content."""
        explorer = self.query_one("#explorer", Panel)
        explorer.set_content(*children)

    def set_terminal_content(self, *children) -> None:
        """Set terminal panel content."""
        terminal = self.query_one("#terminal-panel", Panel)
        terminal.set_content(*children)

    def set_main_content(self, *children) -> None:
        """Set main content area."""
        content = self.query_one("#main-content", Container)
        content.remove_children()
        for child in children:
            content.mount(child)

    def get_layout_state(self) -> dict[str, PanelState]:
        """Get current layout state for persistence."""
        return {
            "sidebar": PanelState(
                visible=self.sidebar_visible,
                size=self._sidebar_width,
            ),
            "explorer": PanelState(
                visible=self.explorer_visible,
                size=self._explorer_width,
            ),
            "terminal": PanelState(
                visible=self.terminal_visible,
                size=self._terminal_height,
            ),
        }

    def restore_layout_state(self, state: dict[str, PanelState]) -> None:
        """Restore layout state from persistence."""
        if "sidebar" in state:
            self.sidebar_visible = state["sidebar"].visible
            self._sidebar_width = state["sidebar"].size

        if "explorer" in state:
            self.explorer_visible = state["explorer"].visible
            self._explorer_width = state["explorer"].size

        if "terminal" in state:
            self.terminal_visible = state["terminal"].visible
            self._terminal_height = state["terminal"].size

        self.refresh(recompose=True)
