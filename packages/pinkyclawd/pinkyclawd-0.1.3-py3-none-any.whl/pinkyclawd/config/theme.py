"""
Theme system for PinkyClawd TUI.

Supports 15+ built-in themes plus custom themes from ~/.config/pinkyclawd/themes/
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pinkyclawd.config.paths import get_themes_dir


@dataclass
class SyntaxColors:
    """Syntax highlighting colors."""

    keyword: str = "#ff79c6"
    string: str = "#f1fa8c"
    number: str = "#bd93f9"
    comment: str = "#6272a4"
    function: str = "#50fa7b"
    variable: str = "#f8f8f2"
    type: str = "#8be9fd"
    operator: str = "#ff79c6"
    punctuation: str = "#f8f8f2"


@dataclass
class DiffColors:
    """Diff visualization colors."""

    added: str = "#50fa7b"
    added_bg: str = "#1a3d1a"
    removed: str = "#ff5555"
    removed_bg: str = "#3d1a1a"
    modified: str = "#f1fa8c"
    modified_bg: str = "#3d3d1a"


@dataclass
class Theme:
    """Complete theme definition."""

    name: str = "pinkyclawd"
    display_name: str = "PinkyClawd"
    mode: Literal["dark", "light"] = "dark"

    # Primary colors
    primary: str = "#bd93f9"
    secondary: str = "#6272a4"
    accent: str = "#ff79c6"

    # Status colors
    error: str = "#ff5555"
    warning: str = "#ffb86c"
    success: str = "#50fa7b"
    info: str = "#8be9fd"

    # Background layers
    background: str = "#282a36"
    background_panel: str = "#1e1f29"
    background_element: str = "#44475a"

    # Text colors
    text: str = "#f8f8f2"
    text_muted: str = "#6272a4"
    text_accent: str = "#bd93f9"

    # Border colors
    border: str = "#44475a"
    border_focus: str = "#bd93f9"

    # Selection
    selection: str = "#44475a"
    selection_text: str = "#f8f8f2"

    # Syntax highlighting
    syntax: SyntaxColors = field(default_factory=SyntaxColors)

    # Diff colors
    diff: DiffColors = field(default_factory=DiffColors)

    def to_dict(self) -> dict:
        """Convert theme to dictionary."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "mode": self.mode,
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "error": self.error,
            "warning": self.warning,
            "success": self.success,
            "info": self.info,
            "background": self.background,
            "background_panel": self.background_panel,
            "background_element": self.background_element,
            "text": self.text,
            "text_muted": self.text_muted,
            "text_accent": self.text_accent,
            "border": self.border,
            "border_focus": self.border_focus,
            "selection": self.selection,
            "selection_text": self.selection_text,
            "syntax": {
                "keyword": self.syntax.keyword,
                "string": self.syntax.string,
                "number": self.syntax.number,
                "comment": self.syntax.comment,
                "function": self.syntax.function,
                "variable": self.syntax.variable,
                "type": self.syntax.type,
                "operator": self.syntax.operator,
                "punctuation": self.syntax.punctuation,
            },
            "diff": {
                "added": self.diff.added,
                "added_bg": self.diff.added_bg,
                "removed": self.diff.removed,
                "removed_bg": self.diff.removed_bg,
                "modified": self.diff.modified,
                "modified_bg": self.diff.modified_bg,
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> Theme:
        """Create theme from dictionary."""
        syntax_data = data.get("syntax", {})
        diff_data = data.get("diff", {})

        return cls(
            name=data.get("name", "custom"),
            display_name=data.get("display_name", "Custom"),
            mode=data.get("mode", "dark"),
            primary=data.get("primary", "#bd93f9"),
            secondary=data.get("secondary", "#6272a4"),
            accent=data.get("accent", "#ff79c6"),
            error=data.get("error", "#ff5555"),
            warning=data.get("warning", "#ffb86c"),
            success=data.get("success", "#50fa7b"),
            info=data.get("info", "#8be9fd"),
            background=data.get("background", "#282a36"),
            background_panel=data.get("background_panel", "#1e1f29"),
            background_element=data.get("background_element", "#44475a"),
            text=data.get("text", "#f8f8f2"),
            text_muted=data.get("text_muted", "#6272a4"),
            text_accent=data.get("text_accent", "#bd93f9"),
            border=data.get("border", "#44475a"),
            border_focus=data.get("border_focus", "#bd93f9"),
            selection=data.get("selection", "#44475a"),
            selection_text=data.get("selection_text", "#f8f8f2"),
            syntax=SyntaxColors(
                keyword=syntax_data.get("keyword", "#ff79c6"),
                string=syntax_data.get("string", "#f1fa8c"),
                number=syntax_data.get("number", "#bd93f9"),
                comment=syntax_data.get("comment", "#6272a4"),
                function=syntax_data.get("function", "#50fa7b"),
                variable=syntax_data.get("variable", "#f8f8f2"),
                type=syntax_data.get("type", "#8be9fd"),
                operator=syntax_data.get("operator", "#ff79c6"),
                punctuation=syntax_data.get("punctuation", "#f8f8f2"),
            ),
            diff=DiffColors(
                added=diff_data.get("added", "#50fa7b"),
                added_bg=diff_data.get("added_bg", "#1a3d1a"),
                removed=diff_data.get("removed", "#ff5555"),
                removed_bg=diff_data.get("removed_bg", "#3d1a1a"),
                modified=diff_data.get("modified", "#f1fa8c"),
                modified_bg=diff_data.get("modified_bg", "#3d3d1a"),
            ),
        )


# Built-in themes (30+ themes matching OpenCode)
BUILTIN_THEMES: dict[str, Theme] = {
    # Default theme
    "pinkyclawd": Theme(),
    # Dark themes
    "aura": Theme(
        name="aura",
        display_name="Aura",
        mode="dark",
        primary="#a277ff",
        secondary="#61ffca",
        accent="#ffca85",
        error="#ff6767",
        warning="#ffca85",
        success="#61ffca",
        info="#82e2ff",
        background="#15141b",
        background_panel="#110f18",
        background_element="#1c1b22",
        text="#edecee",
        text_muted="#6d6d6d",
        text_accent="#a277ff",
    ),
    "ayu": Theme(
        name="ayu",
        display_name="Ayu Dark",
        mode="dark",
        primary="#ffcc66",
        secondary="#5c6773",
        accent="#f29e74",
        error="#f07178",
        warning="#ffcc66",
        success="#bae67e",
        info="#5ccfe6",
        background="#0a0e14",
        background_panel="#050709",
        background_element="#1d2530",
        text="#b3b1ad",
        text_muted="#5c6773",
        text_accent="#ffcc66",
    ),
    "catppuccin_mocha": Theme(
        name="catppuccin_mocha",
        display_name="Catppuccin Mocha",
        mode="dark",
        primary="#cba6f7",
        secondary="#6c7086",
        accent="#f5c2e7",
        error="#f38ba8",
        warning="#fab387",
        success="#a6e3a1",
        info="#89dceb",
        background="#1e1e2e",
        background_panel="#181825",
        background_element="#313244",
        text="#cdd6f4",
        text_muted="#6c7086",
        text_accent="#cba6f7",
    ),
    "catppuccin_macchiato": Theme(
        name="catppuccin_macchiato",
        display_name="Catppuccin Macchiato",
        mode="dark",
        primary="#c6a0f6",
        secondary="#6e738d",
        accent="#f4dbd6",
        error="#ed8796",
        warning="#f5a97f",
        success="#a6da95",
        info="#8aadf4",
        background="#24273a",
        background_panel="#1e2030",
        background_element="#363a4f",
        text="#cad3f5",
        text_muted="#6e738d",
        text_accent="#c6a0f6",
    ),
    "catppuccin_frappe": Theme(
        name="catppuccin_frappe",
        display_name="Catppuccin Frappé",
        mode="dark",
        primary="#ca9ee6",
        secondary="#737994",
        accent="#f2d5cf",
        error="#e78284",
        warning="#ef9f76",
        success="#a6d189",
        info="#85c1dc",
        background="#303446",
        background_panel="#292c3c",
        background_element="#414559",
        text="#c6d0f5",
        text_muted="#737994",
        text_accent="#ca9ee6",
    ),
    "cobalt2": Theme(
        name="cobalt2",
        display_name="Cobalt2",
        mode="dark",
        primary="#ffc600",
        secondary="#0088ff",
        accent="#ff9d00",
        error="#ff628c",
        warning="#ffc600",
        success="#3ad900",
        info="#0088ff",
        background="#193549",
        background_panel="#122738",
        background_element="#1f4662",
        text="#ffffff",
        text_muted="#0088ff",
        text_accent="#ffc600",
    ),
    "cursor": Theme(
        name="cursor",
        display_name="Cursor",
        mode="dark",
        primary="#0078d4",
        secondary="#6b6b6b",
        accent="#007acc",
        error="#f14c4c",
        warning="#cca700",
        success="#89d185",
        info="#3794ff",
        background="#1e1e1e",
        background_panel="#181818",
        background_element="#252526",
        text="#cccccc",
        text_muted="#6b6b6b",
        text_accent="#0078d4",
    ),
    "dracula": Theme(
        name="dracula",
        display_name="Dracula",
        mode="dark",
        primary="#bd93f9",
        secondary="#6272a4",
        accent="#ff79c6",
        error="#ff5555",
        warning="#ffb86c",
        success="#50fa7b",
        info="#8be9fd",
        background="#282a36",
        background_panel="#1e1f29",
        background_element="#44475a",
        text="#f8f8f2",
        text_muted="#6272a4",
        text_accent="#bd93f9",
    ),
    "everforest": Theme(
        name="everforest",
        display_name="Everforest",
        mode="dark",
        primary="#a7c080",
        secondary="#859289",
        accent="#e67e80",
        error="#e67e80",
        warning="#dbbc7f",
        success="#a7c080",
        info="#7fbbb3",
        background="#2d353b",
        background_panel="#272e33",
        background_element="#3d484d",
        text="#d3c6aa",
        text_muted="#859289",
        text_accent="#a7c080",
    ),
    "flexoki": Theme(
        name="flexoki",
        display_name="Flexoki",
        mode="dark",
        primary="#d0a215",
        secondary="#878580",
        accent="#ce5d97",
        error="#d14d41",
        warning="#da702c",
        success="#879a39",
        info="#4385be",
        background="#100f0f",
        background_panel="#0a0909",
        background_element="#1c1b1a",
        text="#cecdc3",
        text_muted="#878580",
        text_accent="#d0a215",
    ),
    "github_dark": Theme(
        name="github_dark",
        display_name="GitHub Dark",
        mode="dark",
        primary="#58a6ff",
        secondary="#8b949e",
        accent="#f778ba",
        error="#f85149",
        warning="#d29922",
        success="#3fb950",
        info="#58a6ff",
        background="#0d1117",
        background_panel="#010409",
        background_element="#161b22",
        text="#c9d1d9",
        text_muted="#8b949e",
        text_accent="#58a6ff",
    ),
    "gruvbox": Theme(
        name="gruvbox",
        display_name="Gruvbox Dark",
        mode="dark",
        primary="#fabd2f",
        secondary="#665c54",
        accent="#fe8019",
        error="#fb4934",
        warning="#fabd2f",
        success="#b8bb26",
        info="#83a598",
        background="#282828",
        background_panel="#1d2021",
        background_element="#3c3836",
        text="#ebdbb2",
        text_muted="#665c54",
        text_accent="#fabd2f",
    ),
    "kanagawa": Theme(
        name="kanagawa",
        display_name="Kanagawa",
        mode="dark",
        primary="#7e9cd8",
        secondary="#727169",
        accent="#957fb8",
        error="#e82424",
        warning="#ff9e3b",
        success="#76946a",
        info="#7fb4ca",
        background="#1f1f28",
        background_panel="#16161d",
        background_element="#2a2a37",
        text="#dcd7ba",
        text_muted="#727169",
        text_accent="#7e9cd8",
    ),
    "material": Theme(
        name="material",
        display_name="Material",
        mode="dark",
        primary="#82aaff",
        secondary="#546e7a",
        accent="#c792ea",
        error="#ff5370",
        warning="#ffcb6b",
        success="#c3e88d",
        info="#89ddff",
        background="#263238",
        background_panel="#1e272c",
        background_element="#37474f",
        text="#eeffff",
        text_muted="#546e7a",
        text_accent="#82aaff",
    ),
    "matrix": Theme(
        name="matrix",
        display_name="Matrix",
        mode="dark",
        primary="#00ff00",
        secondary="#003300",
        accent="#00cc00",
        error="#ff0000",
        warning="#cccc00",
        success="#00ff00",
        info="#00cccc",
        background="#000000",
        background_panel="#000000",
        background_element="#0a0a0a",
        text="#00ff00",
        text_muted="#006600",
        text_accent="#00ff00",
    ),
    "mercury": Theme(
        name="mercury",
        display_name="Mercury",
        mode="dark",
        primary="#90a4ae",
        secondary="#546e7a",
        accent="#80cbc4",
        error="#ef5350",
        warning="#ffb74d",
        success="#81c784",
        info="#4fc3f7",
        background="#263238",
        background_panel="#1e272c",
        background_element="#37474f",
        text="#eceff1",
        text_muted="#546e7a",
        text_accent="#90a4ae",
    ),
    "monokai": Theme(
        name="monokai",
        display_name="Monokai Pro",
        mode="dark",
        primary="#a9dc76",
        secondary="#727072",
        accent="#ff6188",
        error="#ff6188",
        warning="#ffd866",
        success="#a9dc76",
        info="#78dce8",
        background="#2d2a2e",
        background_panel="#221f22",
        background_element="#403e41",
        text="#fcfcfa",
        text_muted="#727072",
        text_accent="#a9dc76",
    ),
    "nightowl": Theme(
        name="nightowl",
        display_name="Night Owl",
        mode="dark",
        primary="#82aaff",
        secondary="#637777",
        accent="#c792ea",
        error="#ef5350",
        warning="#ffcb6b",
        success="#c3e88d",
        info="#89ddff",
        background="#011627",
        background_panel="#001122",
        background_element="#0b2942",
        text="#d6deeb",
        text_muted="#637777",
        text_accent="#82aaff",
    ),
    "nord": Theme(
        name="nord",
        display_name="Nord",
        mode="dark",
        primary="#88c0d0",
        secondary="#4c566a",
        accent="#81a1c1",
        error="#bf616a",
        warning="#ebcb8b",
        success="#a3be8c",
        info="#88c0d0",
        background="#2e3440",
        background_panel="#242933",
        background_element="#3b4252",
        text="#eceff4",
        text_muted="#4c566a",
        text_accent="#88c0d0",
    ),
    "onedark": Theme(
        name="onedark",
        display_name="One Dark Pro",
        mode="dark",
        primary="#61afef",
        secondary="#5c6370",
        accent="#c678dd",
        error="#e06c75",
        warning="#e5c07b",
        success="#98c379",
        info="#56b6c2",
        background="#282c34",
        background_panel="#21252b",
        background_element="#2c313a",
        text="#abb2bf",
        text_muted="#5c6370",
        text_accent="#61afef",
    ),
    "orng": Theme(
        name="orng",
        display_name="Orng",
        mode="dark",
        primary="#ff9800",
        secondary="#757575",
        accent="#ff5722",
        error="#f44336",
        warning="#ff9800",
        success="#4caf50",
        info="#2196f3",
        background="#121212",
        background_panel="#0a0a0a",
        background_element="#1e1e1e",
        text="#ffffff",
        text_muted="#757575",
        text_accent="#ff9800",
    ),
    "osaka_jade": Theme(
        name="osaka_jade",
        display_name="Osaka Jade",
        mode="dark",
        primary="#8ec07c",
        secondary="#7c6f64",
        accent="#b8bb26",
        error="#fb4934",
        warning="#fabd2f",
        success="#8ec07c",
        info="#83a598",
        background="#282828",
        background_panel="#1d2021",
        background_element="#32302f",
        text="#ebdbb2",
        text_muted="#7c6f64",
        text_accent="#8ec07c",
    ),
    "palenight": Theme(
        name="palenight",
        display_name="Palenight",
        mode="dark",
        primary="#82aaff",
        secondary="#676e95",
        accent="#c792ea",
        error="#ff5370",
        warning="#ffcb6b",
        success="#c3e88d",
        info="#89ddff",
        background="#292d3e",
        background_panel="#1f2233",
        background_element="#34324a",
        text="#bfc7d5",
        text_muted="#676e95",
        text_accent="#82aaff",
    ),
    "rosepine": Theme(
        name="rosepine",
        display_name="Rosé Pine",
        mode="dark",
        primary="#ebbcba",
        secondary="#6e6a86",
        accent="#c4a7e7",
        error="#eb6f92",
        warning="#f6c177",
        success="#31748f",
        info="#9ccfd8",
        background="#191724",
        background_panel="#1f1d2e",
        background_element="#26233a",
        text="#e0def4",
        text_muted="#6e6a86",
        text_accent="#ebbcba",
    ),
    "solarized": Theme(
        name="solarized",
        display_name="Solarized Dark",
        mode="dark",
        primary="#268bd2",
        secondary="#586e75",
        accent="#2aa198",
        error="#dc322f",
        warning="#b58900",
        success="#859900",
        info="#2aa198",
        background="#002b36",
        background_panel="#001e26",
        background_element="#073642",
        text="#839496",
        text_muted="#586e75",
        text_accent="#268bd2",
    ),
    "synthwave84": Theme(
        name="synthwave84",
        display_name="SynthWave '84",
        mode="dark",
        primary="#ff7edb",
        secondary="#848bbd",
        accent="#fede5d",
        error="#fe4450",
        warning="#fede5d",
        success="#72f1b8",
        info="#36f9f6",
        background="#262335",
        background_panel="#1a1826",
        background_element="#34294f",
        text="#ffffff",
        text_muted="#848bbd",
        text_accent="#ff7edb",
    ),
    "tokyonight": Theme(
        name="tokyonight",
        display_name="Tokyo Night",
        mode="dark",
        primary="#7aa2f7",
        secondary="#565f89",
        accent="#bb9af7",
        error="#f7768e",
        warning="#e0af68",
        success="#9ece6a",
        info="#7dcfff",
        background="#1a1b26",
        background_panel="#16161e",
        background_element="#24283b",
        text="#c0caf5",
        text_muted="#565f89",
        text_accent="#7aa2f7",
    ),
    "vercel": Theme(
        name="vercel",
        display_name="Vercel",
        mode="dark",
        primary="#ffffff",
        secondary="#666666",
        accent="#0070f3",
        error="#ee0000",
        warning="#f5a623",
        success="#0070f3",
        info="#0070f3",
        background="#000000",
        background_panel="#000000",
        background_element="#111111",
        text="#ffffff",
        text_muted="#666666",
        text_accent="#ffffff",
    ),
    "vesper": Theme(
        name="vesper",
        display_name="Vesper",
        mode="dark",
        primary="#ffc799",
        secondary="#575279",
        accent="#d7827e",
        error="#eb6f92",
        warning="#f6c177",
        success="#9ccfd8",
        info="#c4a7e7",
        background="#101010",
        background_panel="#080808",
        background_element="#1a1a1a",
        text="#ffffff",
        text_muted="#575279",
        text_accent="#ffc799",
    ),
    "zenburn": Theme(
        name="zenburn",
        display_name="Zenburn",
        mode="dark",
        primary="#f0dfaf",
        secondary="#7f9f7f",
        accent="#cc9393",
        error="#cc9393",
        warning="#f0dfaf",
        success="#7f9f7f",
        info="#8cd0d3",
        background="#3f3f3f",
        background_panel="#2f2f2f",
        background_element="#4f4f4f",
        text="#dcdccc",
        text_muted="#7f9f7f",
        text_accent="#f0dfaf",
    ),
    "carbonfox": Theme(
        name="carbonfox",
        display_name="Carbonfox",
        mode="dark",
        primary="#78a9ff",
        secondary="#525252",
        accent="#be95ff",
        error="#ee5396",
        warning="#3ddbd9",
        success="#42be65",
        info="#82cfff",
        background="#161616",
        background_panel="#0d0d0d",
        background_element="#262626",
        text="#f2f4f8",
        text_muted="#525252",
        text_accent="#78a9ff",
    ),
    # Light themes
    "catppuccin_latte": Theme(
        name="catppuccin_latte",
        display_name="Catppuccin Latte",
        mode="light",
        primary="#8839ef",
        secondary="#9ca0b0",
        accent="#ea76cb",
        error="#d20f39",
        warning="#df8e1d",
        success="#40a02b",
        info="#04a5e5",
        background="#eff1f5",
        background_panel="#e6e9ef",
        background_element="#ccd0da",
        text="#4c4f69",
        text_muted="#9ca0b0",
        text_accent="#8839ef",
    ),
    "solarized_light": Theme(
        name="solarized_light",
        display_name="Solarized Light",
        mode="light",
        primary="#268bd2",
        secondary="#93a1a1",
        accent="#2aa198",
        error="#dc322f",
        warning="#b58900",
        success="#859900",
        info="#2aa198",
        background="#fdf6e3",
        background_panel="#eee8d5",
        background_element="#eee8d5",
        text="#657b83",
        text_muted="#93a1a1",
        text_accent="#268bd2",
    ),
    "github_light": Theme(
        name="github_light",
        display_name="GitHub Light",
        mode="light",
        primary="#0969da",
        secondary="#57606a",
        accent="#8250df",
        error="#cf222e",
        warning="#bf8700",
        success="#1a7f37",
        info="#0969da",
        background="#ffffff",
        background_panel="#f6f8fa",
        background_element="#f3f4f6",
        text="#24292f",
        text_muted="#57606a",
        text_accent="#0969da",
    ),
    "gruvbox_light": Theme(
        name="gruvbox_light",
        display_name="Gruvbox Light",
        mode="light",
        primary="#b57614",
        secondary="#928374",
        accent="#af3a03",
        error="#9d0006",
        warning="#b57614",
        success="#79740e",
        info="#076678",
        background="#fbf1c7",
        background_panel="#f2e5bc",
        background_element="#ebdbb2",
        text="#3c3836",
        text_muted="#928374",
        text_accent="#b57614",
    ),
    "rosepine_dawn": Theme(
        name="rosepine_dawn",
        display_name="Rosé Pine Dawn",
        mode="light",
        primary="#d7827e",
        secondary="#9893a5",
        accent="#907aa9",
        error="#b4637a",
        warning="#ea9d34",
        success="#56949f",
        info="#286983",
        background="#faf4ed",
        background_panel="#fffaf3",
        background_element="#f2e9de",
        text="#575279",
        text_muted="#9893a5",
        text_accent="#d7827e",
    ),
}


class ThemeManager:
    """Manages theme loading and switching."""

    def __init__(self) -> None:
        self._current: Theme = BUILTIN_THEMES["pinkyclawd"]
        self._custom_themes: dict[str, Theme] = {}
        self._load_custom_themes()

    def _load_custom_themes(self) -> None:
        """Load custom themes from user directory."""
        themes_dir = get_themes_dir()
        for theme_file in themes_dir.glob("*.json"):
            try:
                data = json.loads(theme_file.read_text())
                theme = Theme.from_dict(data)
                self._custom_themes[theme.name] = theme
            except (json.JSONDecodeError, OSError):
                continue

    @property
    def current(self) -> Theme:
        """Get current theme."""
        return self._current

    def set_theme(self, name: str) -> bool:
        """Set the current theme by name."""
        if name in BUILTIN_THEMES:
            self._current = BUILTIN_THEMES[name]
            return True
        if name in self._custom_themes:
            self._current = self._custom_themes[name]
            return True
        return False

    def list_themes(self) -> list[Theme]:
        """List all available themes."""
        all_themes = list(BUILTIN_THEMES.values()) + list(self._custom_themes.values())
        return sorted(all_themes, key=lambda t: t.display_name)

    def get_theme(self, name: str) -> Theme | None:
        """Get a theme by name."""
        if name in BUILTIN_THEMES:
            return BUILTIN_THEMES[name]
        return self._custom_themes.get(name)

    def save_custom_theme(self, theme: Theme) -> None:
        """Save a custom theme to user directory."""
        themes_dir = get_themes_dir()
        theme_file = themes_dir / f"{theme.name}.json"
        theme_file.write_text(json.dumps(theme.to_dict(), indent=2))
        self._custom_themes[theme.name] = theme


# Global theme manager
_theme_manager: ThemeManager | None = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def get_current_theme() -> Theme:
    """Get the current theme."""
    return get_theme_manager().current
