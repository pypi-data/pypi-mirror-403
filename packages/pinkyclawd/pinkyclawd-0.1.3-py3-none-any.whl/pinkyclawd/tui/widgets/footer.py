"""
Status footer widget showing keybindings and context usage.
"""

from __future__ import annotations

from typing import Any

from textual.widgets import Static
from textual.containers import Horizontal
from textual.app import ComposeResult


class StatusFooter(Horizontal):
    """
    Footer bar with keybindings and status info.

    Displays:
    - Common keybindings
    - Context usage bar
    - Current status
    """

    DEFAULT_CSS = """
    StatusFooter {
        height: 1;
        background: $panel;
        border-top: solid $primary;
    }
    
    .footer-left {
        width: 1fr;
    }
    
    .footer-right {
        width: auto;
    }
    
    .keybind {
        margin-right: 2;
    }
    
    .key {
        background: $primary 40%;
        padding: 0 1;
    }
    
    .context-bar {
        width: 20;
        margin-left: 1;
    }
    """

    def __init__(
        self,
        context_usage: float = 0.0,
        context_tokens: int = 0,
        context_limit: int = 128000,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._context_usage = context_usage
        self._context_tokens = context_tokens
        self._context_limit = context_limit

    def compose(self) -> ComposeResult:
        # Left side: keybindings
        with Horizontal(classes="footer-left"):
            yield self._keybind("^C", "Quit")
            yield self._keybind("^P", "Commands")
            yield self._keybind("^N", "New")
            yield self._keybind("F2", "Model")
            yield self._keybind("Tab", "Agent")

        # Right side: context usage
        with Horizontal(classes="footer-right"):
            yield Static(self._format_context(), classes="context-bar")

    def _keybind(self, key: str, action: str) -> Static:
        """Create a keybind display."""
        return Static(f"[{key}] {action}", classes="keybind")

    def _format_context(self) -> str:
        """Format context usage display."""
        pct = int(self._context_usage * 100)
        bar_width = 10
        filled = int(bar_width * self._context_usage)
        bar = "" * filled + "" * (bar_width - filled)

        if self._context_tokens > 0:
            tokens_k = self._context_tokens / 1000
            return f"{bar} {tokens_k:.1f}k ({pct}%)"

        return f"{bar} {pct}%"

    def update_context(
        self,
        usage: float,
        tokens: int = 0,
        limit: int = 128000,
    ) -> None:
        """Update context usage display."""
        self._context_usage = usage
        self._context_tokens = tokens
        self._context_limit = limit
        self.refresh()
