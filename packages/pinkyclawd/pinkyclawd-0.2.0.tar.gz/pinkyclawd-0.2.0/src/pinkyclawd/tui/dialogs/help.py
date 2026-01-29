"""
Help dialog with keyboard shortcuts reference.

Matches OpenCode's help dialog with categorized keybindings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Static, Label, TabPane, TabbedContent
from rich.text import Text
from rich.table import Table
from rich.console import Group


@dataclass
class KeybindInfo:
    """Information about a keyboard shortcut."""

    key: str
    description: str
    category: str = "General"


# Default keybindings organized by category
DEFAULT_KEYBINDS = [
    # Navigation
    KeybindInfo("Ctrl+P", "Open command palette", "Navigation"),
    KeybindInfo("Ctrl+N", "New session", "Navigation"),
    KeybindInfo("Ctrl+L", "Toggle sidebar", "Navigation"),
    KeybindInfo("Ctrl+K", "Show context usage", "Navigation"),
    KeybindInfo("Escape", "Stop generation / Close dialog", "Navigation"),

    # Messages
    KeybindInfo("Enter", "Send message", "Messages"),
    KeybindInfo("Shift+Enter", "New line in prompt", "Messages"),
    KeybindInfo("Up/Down", "Navigate history", "Messages"),
    KeybindInfo("Ctrl+Up", "Scroll messages up", "Messages"),
    KeybindInfo("Ctrl+Down", "Scroll messages down", "Messages"),

    # Session
    KeybindInfo("Ctrl+S", "Session list", "Session"),
    KeybindInfo("Ctrl+R", "Rename session", "Session"),
    KeybindInfo("Ctrl+F", "Fork session", "Session"),
    KeybindInfo("Ctrl+E", "Export session", "Session"),
    KeybindInfo("Ctrl+T", "Timeline view", "Session"),

    # Model & Agent
    KeybindInfo("F2", "Select model", "Model"),
    KeybindInfo("F3", "Select agent", "Model"),
    KeybindInfo("Tab", "Cycle agent", "Model"),

    # View
    KeybindInfo("Ctrl+B", "Toggle sidebar", "View"),
    KeybindInfo("Ctrl+\\", "Toggle thinking blocks", "View"),
    KeybindInfo("Ctrl+/", "Toggle timestamps", "View"),
    KeybindInfo("Ctrl+.", "Toggle tool details", "View"),

    # System
    KeybindInfo("Ctrl+C", "Quit / Cancel", "System"),
    KeybindInfo("F1", "Show this help", "System"),
    KeybindInfo("Ctrl+Z", "Undo", "System"),
    KeybindInfo("Ctrl+Y", "Redo", "System"),
]

# Slash commands
SLASH_COMMANDS = [
    ("/help", "Show help"),
    ("/new", "New session"),
    ("/clear", "Clear messages"),
    ("/compact", "Compact context"),
    ("/context", "Show context usage"),
    ("/model", "Change model"),
    ("/agent", "Change agent"),
    ("/theme", "Change theme"),
    ("/export", "Export session"),
    ("/share", "Share session"),
    ("/fork", "Fork session"),
    ("/rename", "Rename session"),
    ("/sessions", "List sessions"),
    ("/quit", "Exit application"),
]


class HelpDialog(ModalScreen[None]):
    """
    Help dialog showing keyboard shortcuts and commands.

    Organized into tabs for easy navigation.
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("q", "close", "Close"),
    ]

    CSS = """
    HelpDialog {
        align: center middle;
    }

    HelpDialog > Container {
        width: 80;
        max-width: 95%;
        height: 85%;
        background: $surface;
        border: tall $primary;
        padding: 1;
    }

    .dialog-header {
        height: 3;
        text-align: center;
        padding: 1;
    }

    .dialog-title {
        text-style: bold;
    }

    .dialog-version {
        color: $text-muted;
    }

    HelpDialog TabbedContent {
        height: 1fr;
    }

    HelpDialog TabPane {
        padding: 1;
    }

    .keybind-section {
        margin-bottom: 1;
    }

    .keybind-category {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .keybind-row {
        height: 1;
        margin-bottom: 0;
    }

    .keybind-key {
        width: 20;
        color: $accent;
    }

    .keybind-desc {
        width: 1fr;
        color: $text;
    }

    .command-row {
        height: 1;
    }

    .command-name {
        width: 15;
        color: $warning;
    }

    .command-desc {
        width: 1fr;
        color: $text-muted;
    }

    .dialog-footer {
        height: 2;
        text-align: center;
        color: $text-muted;
        padding: 1;
    }

    .about-section {
        padding: 1;
    }

    .about-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .about-text {
        margin-bottom: 1;
    }

    .about-link {
        color: $accent;
        text-style: underline;
    }
    """

    def __init__(self, version: str = "0.1.0", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.version = version

    def compose(self) -> ComposeResult:
        with Container():
            # Header
            with Vertical(classes="dialog-header"):
                yield Static("PinkyClawd Help", classes="dialog-title")
                yield Static(f"v{self.version}", classes="dialog-version")

            # Tabbed content
            with TabbedContent():
                with TabPane("Keybindings", id="keybinds"):
                    yield from self._compose_keybindings()

                with TabPane("Commands", id="commands"):
                    yield from self._compose_commands()

                with TabPane("About", id="about"):
                    yield from self._compose_about()

            # Footer
            yield Static("Press [Esc] or [Q] to close", classes="dialog-footer")

    def _compose_keybindings(self) -> ComposeResult:
        """Compose keybindings tab content."""
        with ScrollableContainer():
            # Group by category
            categories: dict[str, list[KeybindInfo]] = {}
            for kb in DEFAULT_KEYBINDS:
                if kb.category not in categories:
                    categories[kb.category] = []
                categories[kb.category].append(kb)

            for category, keybinds in categories.items():
                with Vertical(classes="keybind-section"):
                    yield Static(category, classes="keybind-category")
                    for kb in keybinds:
                        with Horizontal(classes="keybind-row"):
                            yield Static(kb.key, classes="keybind-key")
                            yield Static(kb.description, classes="keybind-desc")

    def _compose_commands(self) -> ComposeResult:
        """Compose slash commands tab content."""
        with ScrollableContainer():
            yield Static("Slash Commands", classes="keybind-category")
            yield Static("Type these in the prompt to execute:", classes="about-text")

            for cmd, desc in SLASH_COMMANDS:
                with Horizontal(classes="command-row"):
                    yield Static(cmd, classes="command-name")
                    yield Static(desc, classes="command-desc")

    def _compose_about(self) -> ComposeResult:
        """Compose about tab content."""
        with ScrollableContainer():
            with Vertical(classes="about-section"):
                yield Static("PinkyClawd", classes="about-title")
                yield Static(
                    "AI-Powered Development Tool with RLM Context Management",
                    classes="about-text",
                )

                yield Static("Features", classes="about-title")
                features = [
                    "• Unlimited conversation context via RLM",
                    "• Multi-model support (Claude, GPT, Local)",
                    "• 30+ color themes",
                    "• Session management (fork, share, export)",
                    "• Rich tool output display",
                    "• MCP server integration",
                    "• LSP support",
                ]
                for feature in features:
                    yield Static(feature, classes="about-text")

                yield Static("Links", classes="about-title")
                yield Static(
                    "GitHub: https://github.com/tekcin/PinkyClawd",
                    classes="about-link",
                )
                yield Static(
                    "Author: Michael Thornton <tekcin@yahoo.com>",
                    classes="about-text",
                )

    def action_close(self) -> None:
        """Close the dialog."""
        self.dismiss(None)


class StatusDialog(ModalScreen[None]):
    """System status dialog showing diagnostics."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]

    CSS = """
    StatusDialog {
        align: center middle;
    }

    StatusDialog > Container {
        width: 70;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: tall $primary;
        padding: 2;
    }

    .dialog-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    .status-section {
        margin-bottom: 1;
        padding: 1;
        background: $panel;
    }

    .status-title {
        text-style: bold;
        color: $primary;
    }

    .status-row {
        height: 1;
    }

    .status-label {
        width: 20;
        color: $text-muted;
    }

    .status-value {
        width: 1fr;
    }

    .status-ok {
        color: $success;
    }

    .status-warn {
        color: $warning;
    }

    .status-error {
        color: $error;
    }
    """

    def __init__(
        self,
        session_id: str | None = None,
        model: str | None = None,
        context_tokens: int = 0,
        context_limit: int = 200000,
        mcp_count: int = 0,
        lsp_count: int = 0,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.session_id = session_id
        self.model = model
        self.context_tokens = context_tokens
        self.context_limit = context_limit
        self.mcp_count = mcp_count
        self.lsp_count = lsp_count

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("System Status", classes="dialog-title")

            # Session info
            with Vertical(classes="status-section"):
                yield Static("Session", classes="status-title")
                with Horizontal(classes="status-row"):
                    yield Static("ID:", classes="status-label")
                    yield Static(self.session_id or "None", classes="status-value")

            # Model info
            with Vertical(classes="status-section"):
                yield Static("Model", classes="status-title")
                with Horizontal(classes="status-row"):
                    yield Static("Current:", classes="status-label")
                    yield Static(self.model or "Not set", classes="status-value")

            # Context info
            with Vertical(classes="status-section"):
                yield Static("Context", classes="status-title")
                percentage = (self.context_tokens / self.context_limit * 100) if self.context_limit else 0
                status_class = "status-ok" if percentage < 80 else "status-warn" if percentage < 95 else "status-error"

                with Horizontal(classes="status-row"):
                    yield Static("Tokens:", classes="status-label")
                    yield Static(f"{self.context_tokens:,} / {self.context_limit:,}", classes=f"status-value {status_class}")
                with Horizontal(classes="status-row"):
                    yield Static("Usage:", classes="status-label")
                    yield Static(f"{percentage:.1f}%", classes=f"status-value {status_class}")

            # Connections
            with Vertical(classes="status-section"):
                yield Static("Connections", classes="status-title")
                with Horizontal(classes="status-row"):
                    yield Static("MCP Servers:", classes="status-label")
                    yield Static(str(self.mcp_count), classes="status-value status-ok" if self.mcp_count > 0 else "status-value")
                with Horizontal(classes="status-row"):
                    yield Static("LSP Servers:", classes="status-label")
                    yield Static(str(self.lsp_count), classes="status-value status-ok" if self.lsp_count > 0 else "status-value")

            yield Static("[Esc] Close", classes="dialog-footer")

    def action_close(self) -> None:
        self.dismiss(None)
