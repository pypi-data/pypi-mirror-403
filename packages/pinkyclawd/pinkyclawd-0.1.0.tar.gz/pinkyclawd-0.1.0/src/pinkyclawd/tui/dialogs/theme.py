"""
Theme selector dialog with preview.

Allows users to change the color theme with live preview.
"""

from __future__ import annotations

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Static, ListView, ListItem, Label


@dataclass
class ThemeInfo:
    """Information about a color theme."""

    id: str
    name: str
    description: str
    is_dark: bool = True
    colors: dict[str, str] | None = None

    # Preview colors
    primary: str = "#7C3AED"
    secondary: str = "#10B981"
    background: str = "#1A1A2E"
    surface: str = "#25253A"
    text: str = "#E4E4E7"
    text_muted: str = "#71717A"


class ThemeListItem(ListItem):
    """A list item for a theme."""

    def __init__(self, theme: ThemeInfo, is_current: bool = False) -> None:
        super().__init__()
        self.theme = theme
        self.is_current = is_current

    def compose(self) -> ComposeResult:
        with Container(classes="theme-item"):
            with Horizontal():
                yield Label(self.theme.name, classes="theme-name")
                if self.is_current:
                    yield Label("(current)", classes="theme-current")
                yield Label(
                    "dark" if self.theme.is_dark else "light",
                    classes="theme-mode",
                )
            yield Label(self.theme.description, classes="theme-description")


class ThemePreview(Static):
    """Preview widget showing theme colors."""

    CSS = """
    ThemePreview {
        height: 10;
        padding: 1;
        margin-top: 1;
        border: round $primary 50%;
    }

    .preview-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .color-row {
        height: 1;
    }

    .color-swatch {
        width: 4;
        margin-right: 1;
    }

    .color-name {
        width: 12;
    }

    .color-value {
        color: $text-muted;
    }
    """

    def __init__(self, theme: ThemeInfo | None = None) -> None:
        super().__init__()
        self._theme = theme

    def compose(self) -> ComposeResult:
        yield Static("Preview", classes="preview-title")
        with Container(id="preview-colors"):
            yield Static("")

    def update_theme(self, theme: ThemeInfo) -> None:
        """Update the preview with a new theme."""
        self._theme = theme
        preview = self.query_one("#preview-colors", Container)

        # Build preview content
        colors = [
            ("Primary", theme.primary),
            ("Secondary", theme.secondary),
            ("Background", theme.background),
            ("Surface", theme.surface),
            ("Text", theme.text),
        ]

        lines = []
        for name, value in colors:
            lines.append(f"  {name:12} {value}")

        preview.query_one(Static).update("\n".join(lines))


class ThemeSelector(ModalScreen[ThemeInfo | None]):
    """
    Theme selector modal with live preview.

    Shows available themes with a preview of their colors.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select", "Select"),
        Binding("up", "cursor_up", "Up"),
        Binding("down", "cursor_down", "Down"),
    ]

    CSS = """
    ThemeSelector {
        align: center middle;
    }

    ThemeSelector > Container {
        width: 70;
        max-width: 90%;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: tall $primary;
        padding: 1;
    }

    ThemeSelector .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    ThemeSelector ListView {
        height: auto;
        max-height: 15;
    }

    .theme-item {
        padding: 0 1;
    }

    .theme-item Horizontal {
        height: 1;
    }

    .theme-name {
        width: 1fr;
        text-style: bold;
    }

    .theme-current {
        color: $success;
        margin: 0 1;
    }

    .theme-mode {
        width: auto;
        color: $text-muted;
    }

    .theme-description {
        color: $text-muted;
    }

    ThemeSelector ListItem {
        padding: 0;
        height: 3;
    }

    ThemeSelector ListItem:hover {
        background: $primary 20%;
    }

    ThemeSelector ListItem.-selected {
        background: $primary 40%;
    }
    """

    def __init__(
        self,
        current_theme: str | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self._themes = get_default_themes()
        self._current_theme = current_theme

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Select Theme", classes="title")
            yield ListView(id="theme-list")
            yield ThemePreview(id="preview")

    def on_mount(self) -> None:
        """Populate the theme list."""
        list_view = self.query_one("#theme-list", ListView)

        current_index = 0
        for i, theme in enumerate(self._themes):
            is_current = theme.id == self._current_theme
            if is_current:
                current_index = i
            list_view.append(ThemeListItem(theme, is_current))

        list_view.index = current_index

        # Show initial preview
        if self._themes:
            self._update_preview(self._themes[current_index])

    def _update_preview(self, theme: ThemeInfo) -> None:
        """Update the preview widget."""
        preview = self.query_one("#preview", ThemePreview)
        preview.update_theme(theme)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Update preview when selection changes."""
        if isinstance(event.item, ThemeListItem):
            self._update_preview(event.item.theme)

    def action_cancel(self) -> None:
        """Cancel selection."""
        self.dismiss(None)

    def action_select(self) -> None:
        """Select current theme."""
        list_view = self.query_one("#theme-list", ListView)
        if list_view.index is not None and self._themes:
            selected = self._themes[list_view.index]
            self.dismiss(selected)

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        list_view = self.query_one("#theme-list", ListView)
        if list_view.index is not None and list_view.index > 0:
            list_view.index -= 1

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        list_view = self.query_one("#theme-list", ListView)
        if list_view.index is not None:
            if list_view.index < len(self._themes) - 1:
                list_view.index += 1

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection."""
        if isinstance(event.item, ThemeListItem):
            self.dismiss(event.item.theme)


def get_default_themes() -> list[ThemeInfo]:
    """Get the default list of available themes."""
    return [
        ThemeInfo(
            id="pinkyclawd",
            name="PinkyClawd",
            description="Default dark theme with purple accents",
            is_dark=True,
            primary="#7C3AED",
            secondary="#10B981",
            background="#1A1A2E",
            surface="#25253A",
            text="#E4E4E7",
        ),
        ThemeInfo(
            id="dracula",
            name="Dracula",
            description="Popular dark theme with vibrant colors",
            is_dark=True,
            primary="#BD93F9",
            secondary="#50FA7B",
            background="#282A36",
            surface="#44475A",
            text="#F8F8F2",
        ),
        ThemeInfo(
            id="nord",
            name="Nord",
            description="Arctic, north-bluish color palette",
            is_dark=True,
            primary="#88C0D0",
            secondary="#A3BE8C",
            background="#2E3440",
            surface="#3B4252",
            text="#ECEFF4",
        ),
        ThemeInfo(
            id="monokai",
            name="Monokai",
            description="Classic Monokai from Sublime Text",
            is_dark=True,
            primary="#F92672",
            secondary="#A6E22E",
            background="#272822",
            surface="#3E3D32",
            text="#F8F8F2",
        ),
        ThemeInfo(
            id="solarized-dark",
            name="Solarized Dark",
            description="Precision colors for machines and people",
            is_dark=True,
            primary="#268BD2",
            secondary="#859900",
            background="#002B36",
            surface="#073642",
            text="#839496",
        ),
        ThemeInfo(
            id="github-dark",
            name="GitHub Dark",
            description="GitHub's dark theme",
            is_dark=True,
            primary="#58A6FF",
            secondary="#3FB950",
            background="#0D1117",
            surface="#161B22",
            text="#C9D1D9",
        ),
        ThemeInfo(
            id="one-dark",
            name="One Dark",
            description="Atom's iconic dark theme",
            is_dark=True,
            primary="#61AFEF",
            secondary="#98C379",
            background="#282C34",
            surface="#21252B",
            text="#ABB2BF",
        ),
        ThemeInfo(
            id="catppuccin",
            name="Catppuccin Mocha",
            description="Soothing pastel theme",
            is_dark=True,
            primary="#CBA6F7",
            secondary="#A6E3A1",
            background="#1E1E2E",
            surface="#313244",
            text="#CDD6F4",
        ),
    ]
