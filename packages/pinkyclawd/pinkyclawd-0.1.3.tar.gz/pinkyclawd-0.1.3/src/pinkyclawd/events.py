"""
Event system for reactive updates across the application.

Provides a typed event bus for communication between components
without tight coupling. Matches pinkyclawd's event-driven architecture.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Coroutine, TypeVar, Generic
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class EventType(Enum):
    """All event types in the system."""

    # Session events
    SESSION_CREATED = auto()
    SESSION_UPDATED = auto()
    SESSION_DELETED = auto()
    SESSION_ERROR = auto()
    SESSION_IDLE = auto()
    SESSION_COMPACTING = auto()

    # Message events
    MESSAGE_CREATED = auto()
    MESSAGE_UPDATED = auto()
    MESSAGE_PART_UPDATED = auto()
    MESSAGE_COMPLETED = auto()

    # Tool events
    TOOL_STARTED = auto()
    TOOL_COMPLETED = auto()
    TOOL_ERROR = auto()

    # Permission events
    PERMISSION_ASKED = auto()
    PERMISSION_REPLIED = auto()

    # Question events
    QUESTION_ASKED = auto()
    QUESTION_REPLIED = auto()

    # Todo events
    TODO_UPDATED = auto()

    # Provider events
    PROVIDER_CONNECTED = auto()
    PROVIDER_DISCONNECTED = auto()
    PROVIDER_ERROR = auto()

    # RLM events
    RLM_ARCHIVE_STARTED = auto()
    RLM_ARCHIVE_COMPLETED = auto()
    RLM_CONTEXT_RETRIEVED = auto()

    # UI events
    THEME_CHANGED = auto()
    KEYBIND_TRIGGERED = auto()
    DIALOG_OPENED = auto()
    DIALOG_CLOSED = auto()
    TOAST_SHOWN = auto()

    # System events
    CONFIG_CHANGED = auto()
    SHUTDOWN = auto()


@dataclass
class Event:
    """Base event with metadata."""

    type: EventType
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now()


@dataclass
class SessionEvent(Event):
    """Session-related event."""

    session_id: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        if "session_id" in self.data:
            self.session_id = self.data["session_id"]


@dataclass
class MessageEvent(Event):
    """Message-related event."""

    session_id: str = ""
    message_id: str = ""
    part_id: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self.session_id = self.data.get("session_id", "")
        self.message_id = self.data.get("message_id", "")
        self.part_id = self.data.get("part_id")


@dataclass
class ToolEvent(Event):
    """Tool execution event."""

    tool_name: str = ""
    session_id: str = ""
    message_id: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        self.tool_name = self.data.get("tool_name", "")
        self.session_id = self.data.get("session_id", "")
        self.message_id = self.data.get("message_id", "")


EventHandler = Callable[[Event], None] | Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """
    Central event bus for application-wide communication.

    Supports both sync and async handlers, with optional filtering
    by event type. Thread-safe for concurrent access.
    """

    _instance: EventBus | None = None

    def __new__(cls) -> EventBus:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._handlers: dict[EventType | None, list[EventHandler]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._history: list[Event] = []
        self._max_history = 1000
        self._initialized = True

    def subscribe(
        self,
        handler: EventHandler,
        event_type: EventType | None = None,
    ) -> Callable[[], None]:
        """
        Subscribe to events.

        Args:
            handler: Callback function (sync or async)
            event_type: Optional filter for specific event type

        Returns:
            Unsubscribe function
        """
        self._handlers[event_type].append(handler)

        def unsubscribe() -> None:
            self._handlers[event_type].remove(handler)

        return unsubscribe

    def on(self, event_type: EventType) -> Callable[[EventHandler], EventHandler]:
        """Decorator for subscribing to specific event type."""

        def decorator(handler: EventHandler) -> EventHandler:
            self.subscribe(handler, event_type)
            return handler

        return decorator

    async def emit(self, event: Event) -> None:
        """
        Emit an event to all subscribers.

        Calls handlers for the specific event type and global handlers.
        """
        async with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history :]

        handlers = self._handlers[event.type] + self._handlers[None]

        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error in event handler: {e}", exc_info=True)

    def emit_sync(self, event: Event) -> None:
        """Synchronous emit for non-async contexts."""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(self.emit(event))
        else:
            loop.run_until_complete(self.emit(event))

    def get_history(
        self,
        event_type: EventType | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """Get recent events, optionally filtered by type."""
        events = self._history
        if event_type:
            events = [e for e in events if e.type == event_type]
        return events[-limit:]

    def clear_history(self) -> None:
        """Clear event history."""
        self._history.clear()

    @classmethod
    def reset(cls) -> None:
        """Reset singleton instance (for testing)."""
        cls._instance = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    return EventBus()


# Convenience functions for common events
def emit_session_created(session_id: str, **kwargs: Any) -> None:
    """Emit session created event."""
    get_event_bus().emit_sync(
        SessionEvent(
            type=EventType.SESSION_CREATED,
            data={"session_id": session_id, **kwargs},
        )
    )


def emit_message_updated(
    session_id: str,
    message_id: str,
    part_id: str | None = None,
    **kwargs: Any,
) -> None:
    """Emit message updated event."""
    get_event_bus().emit_sync(
        MessageEvent(
            type=EventType.MESSAGE_UPDATED,
            data={
                "session_id": session_id,
                "message_id": message_id,
                "part_id": part_id,
                **kwargs,
            },
        )
    )


def emit_tool_completed(
    tool_name: str,
    session_id: str,
    message_id: str,
    result: Any,
    **kwargs: Any,
) -> None:
    """Emit tool completed event."""
    get_event_bus().emit_sync(
        ToolEvent(
            type=EventType.TOOL_COMPLETED,
            data={
                "tool_name": tool_name,
                "session_id": session_id,
                "message_id": message_id,
                "result": result,
                **kwargs,
            },
        )
    )
