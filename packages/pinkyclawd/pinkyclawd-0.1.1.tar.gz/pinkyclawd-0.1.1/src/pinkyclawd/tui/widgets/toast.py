"""
Toast notification system.

Provides non-intrusive notifications that appear temporarily
and dismiss automatically.
"""

from __future__ import annotations

import asyncio
from typing import Any, Literal

from textual.widgets import Static
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.reactive import reactive
from rich.text import Text


ToastLevel = Literal["info", "success", "warning", "error"]


class Toast(Static):
    """A single toast notification."""

    DEFAULT_CSS = """
    Toast {
        width: auto;
        min-width: 30;
        max-width: 60;
        height: auto;
        padding: 1 2;
        margin-bottom: 1;
        background: $surface;
        border: solid $border;
    }

    Toast.info {
        border-left: thick $info;
    }

    Toast.success {
        border-left: thick $success;
    }

    Toast.warning {
        border-left: thick $warning;
    }

    Toast.error {
        border-left: thick $error;
    }

    .toast-icon {
        width: 3;
    }

    .toast-message {
        width: 1fr;
    }
    """

    ICONS = {
        "info": "ℹ",
        "success": "✓",
        "warning": "⚠",
        "error": "✗",
    }

    def __init__(
        self,
        message: str,
        level: ToastLevel = "info",
        duration: float = 3.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.message = message
        self.level = level
        self.duration = duration
        self.add_class(level)

    def compose(self) -> ComposeResult:
        icon = self.ICONS.get(self.level, "•")
        style = {
            "info": "cyan",
            "success": "green",
            "warning": "yellow",
            "error": "red",
        }.get(self.level, "white")

        text = Text()
        text.append(f"{icon} ", style=style)
        text.append(self.message)
        yield Static(text)


class ToastContainer(Vertical):
    """Container for toast notifications."""

    DEFAULT_CSS = """
    ToastContainer {
        dock: bottom;
        align: right bottom;
        width: auto;
        height: auto;
        max-height: 30%;
        padding: 1;
        layer: notification;
    }
    """

    def show_toast(
        self,
        message: str,
        level: ToastLevel = "info",
        duration: float = 3.0,
    ) -> None:
        """Show a toast notification."""
        toast = Toast(message, level=level, duration=duration)
        self.mount(toast)

        # Schedule removal
        if duration > 0:
            asyncio.create_task(self._remove_after(toast, duration))

    async def _remove_after(self, toast: Toast, duration: float) -> None:
        """Remove toast after duration."""
        await asyncio.sleep(duration)
        if toast.is_mounted:
            toast.remove()

    def clear_all(self) -> None:
        """Clear all toasts."""
        self.remove_children()


# Mixin for apps that want toast support
class ToastMixin:
    """Mixin to add toast notification support to an app."""

    def compose(self) -> ComposeResult:
        """Override to add toast container."""
        yield from super().compose()  # type: ignore
        yield ToastContainer(id="toast-container")

    def show_toast(
        self,
        message: str,
        level: ToastLevel = "info",
        duration: float = 3.0,
    ) -> None:
        """Show a toast notification."""
        try:
            container = self.query_one("#toast-container", ToastContainer)  # type: ignore
            container.show_toast(message, level=level, duration=duration)
        except Exception:
            # Fallback to regular notify
            self.notify(message)  # type: ignore

    def toast_info(self, message: str, duration: float = 3.0) -> None:
        """Show an info toast."""
        self.show_toast(message, "info", duration)

    def toast_success(self, message: str, duration: float = 3.0) -> None:
        """Show a success toast."""
        self.show_toast(message, "success", duration)

    def toast_warning(self, message: str, duration: float = 3.0) -> None:
        """Show a warning toast."""
        self.show_toast(message, "warning", duration)

    def toast_error(self, message: str, duration: float = 3.0) -> None:
        """Show an error toast."""
        self.show_toast(message, "error", duration)
