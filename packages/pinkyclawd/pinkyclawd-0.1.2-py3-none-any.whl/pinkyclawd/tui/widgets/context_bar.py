"""
Context usage bar widget showing token consumption.
"""

from __future__ import annotations

from typing import Any

from textual.widgets import Static, ProgressBar
from textual.containers import Vertical
from textual.app import ComposeResult


class ContextBar(Vertical):
    """
    Visual indicator of context window usage.

    Shows:
    - Progress bar of token usage
    - Token counts
    - Warning when approaching limit
    """

    DEFAULT_CSS = """
    ContextBar {
        height: auto;
        padding: 0 1;
    }
    
    .context-label {
        text-align: right;
    }
    
    .context-warning {
        color: $warning;
    }
    
    .context-danger {
        color: $error;
    }
    
    .context-ok {
        color: $success;
    }
    """

    WARNING_THRESHOLD = 0.6  # 60%
    DANGER_THRESHOLD = 0.8  # 80%

    def __init__(
        self,
        tokens_used: int = 0,
        token_limit: int = 128000,
        show_details: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._tokens_used = tokens_used
        self._token_limit = token_limit
        self._show_details = show_details

    @property
    def usage_ratio(self) -> float:
        """Get usage as a ratio (0-1)."""
        if self._token_limit <= 0:
            return 0.0
        return min(1.0, self._tokens_used / self._token_limit)

    @property
    def status_class(self) -> str:
        """Get CSS class based on usage level."""
        if self.usage_ratio >= self.DANGER_THRESHOLD:
            return "context-danger"
        if self.usage_ratio >= self.WARNING_THRESHOLD:
            return "context-warning"
        return "context-ok"

    def compose(self) -> ComposeResult:
        yield ProgressBar(total=100, show_eta=False)

        if self._show_details:
            yield Static(
                self._format_usage(), classes=f"context-label {self.status_class}"
            )

    def on_mount(self) -> None:
        """Initialize the progress bar."""
        self._update_bar()

    def _format_usage(self) -> str:
        """Format usage text."""
        used_k = self._tokens_used / 1000
        limit_k = self._token_limit / 1000
        pct = int(self.usage_ratio * 100)
        return f"{used_k:.1f}k / {limit_k:.0f}k ({pct}%)"

    def _update_bar(self) -> None:
        """Update the progress bar."""
        bar = self.query_one(ProgressBar)
        bar.update(progress=self.usage_ratio * 100)

        if self._show_details:
            label = self.query_one(".context-label", Static)
            label.update(self._format_usage())

            # Update class
            label.remove_class("context-ok", "context-warning", "context-danger")
            label.add_class(self.status_class)

    def update(self, tokens_used: int, token_limit: int | None = None) -> None:
        """Update token counts."""
        self._tokens_used = tokens_used
        if token_limit is not None:
            self._token_limit = token_limit
        self._update_bar()
