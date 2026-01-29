"""
Session header widget showing current model, agent, and status.
"""

from __future__ import annotations

from typing import Any

from textual.widgets import Static
from textual.containers import Horizontal
from textual.app import ComposeResult


class SessionHeader(Horizontal):
    """
    Header bar showing session info.

    Displays:
    - Current model (with cycle indicator)
    - Current agent
    - Session title
    - Status indicators (LSP, MCP, etc.)
    """

    DEFAULT_CSS = """
    SessionHeader {
        height: 3;
        background: $panel;
        border-bottom: solid $primary;
        padding: 0 1;
    }
    
    .header-left {
        width: 1fr;
    }
    
    .header-center {
        width: auto;
        text-align: center;
    }
    
    .header-right {
        width: 1fr;
        text-align: right;
    }
    
    .model-indicator {
        background: $primary 30%;
        padding: 0 1;
        margin-right: 1;
    }
    
    .agent-indicator {
        background: $secondary 30%;
        padding: 0 1;
    }
    
    .session-title {
        text-style: bold;
    }
    
    .status-indicator {
        margin-left: 1;
    }
    
    .status-ok {
        color: $success;
    }
    
    .status-warning {
        color: $warning;
    }
    
    .status-error {
        color: $error;
    }
    """

    def __init__(
        self,
        model: str = "",
        agent: str = "build",
        title: str = "New Session",
        mcp_status: str = "ok",
        lsp_count: int = 0,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._model = model
        self._agent = agent
        self._title = title
        self._mcp_status = mcp_status
        self._lsp_count = lsp_count

    def compose(self) -> ComposeResult:
        # Left side: model and agent
        with Horizontal(classes="header-left"):
            yield Static(self._format_model(), classes="model-indicator")
            yield Static(f"@{self._agent}", classes="agent-indicator")

        # Center: session title
        yield Static(self._title, classes="header-center session-title")

        # Right side: status indicators
        with Horizontal(classes="header-right"):
            if self._lsp_count > 0:
                yield Static(
                    f"LSP:{self._lsp_count}", classes="status-indicator status-ok"
                )
            yield Static(self._format_mcp_status(), classes="status-indicator")

    def _format_model(self) -> str:
        """Format model name for display."""
        if "/" in self._model:
            return self._model.split("/")[1]
        return self._model or "No model"

    def _format_mcp_status(self) -> str:
        """Format MCP status indicator."""
        if self._mcp_status == "ok":
            return "MCP"
        if self._mcp_status == "error":
            return "MCP!"
        return ""

    def update_model(self, model: str) -> None:
        """Update the displayed model."""
        self._model = model
        self.refresh()

    def update_agent(self, agent: str) -> None:
        """Update the displayed agent."""
        self._agent = agent
        self.refresh()

    def update_title(self, title: str) -> None:
        """Update the session title."""
        self._title = title
        self.refresh()
