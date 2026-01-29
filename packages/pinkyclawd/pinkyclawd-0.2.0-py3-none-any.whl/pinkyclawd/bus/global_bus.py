"""
Global event bus with typed event support.

Provides a type-safe event system that works with both the new
Pydantic-based events and legacy EventType-based events.

Usage:
    from pinkyclawd.bus import emit, on, subscribe

    # Emit a typed event
    emit(SessionCreatedEvent(session_id="abc123", title="New Session"))

    # Subscribe with decorator
    @on(SessionCreatedEvent)
    def handle_session_created(event: SessionCreatedEvent):
        print(f"Session created: {event.title}")

    # Subscribe with function
    unsubscribe = subscribe(SessionCreatedEvent, handle_session_created)
"""

from __future__ import annotations

import asyncio
import logging
from typing import (
    TypeVar,
    Generic,
    Callable,
    Coroutine,
    Any,
    Type,
    Union,
    overload,
)
from collections import defaultdict
from threading import Lock

from pinkyclawd.bus.event_types import EventDefinition

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=EventDefinition)

# Handler types
SyncHandler = Callable[[T], None]
AsyncHandler = Callable[[T], Coroutine[Any, Any, None]]
Handler = Union[SyncHandler[T], AsyncHandler[T]]


class TypedEventBus:
    """
    Event bus with typed event support.

    Supports both synchronous and asynchronous handlers,
    with type-safe subscriptions based on event class.
    """

    def __init__(self) -> None:
        self._handlers: dict[Type[EventDefinition], list[Handler]] = defaultdict(list)
        self._global_handlers: list[Handler[EventDefinition]] = []
        self._lock = Lock()
        self._history: list[EventDefinition] = []
        self._max_history = 1000

    def subscribe(
        self,
        event_type: Type[T],
        handler: Handler[T],
    ) -> Callable[[], None]:
        """
        Subscribe to events of a specific type.

        Args:
            event_type: The event class to subscribe to
            handler: Callback function (sync or async)

        Returns:
            Unsubscribe function
        """
        with self._lock:
            self._handlers[event_type].append(handler)

        def unsubscribe() -> None:
            with self._lock:
                if handler in self._handlers[event_type]:
                    self._handlers[event_type].remove(handler)

        return unsubscribe

    def subscribe_all(
        self,
        handler: Handler[EventDefinition],
    ) -> Callable[[], None]:
        """
        Subscribe to all events.

        Args:
            handler: Callback that receives all events

        Returns:
            Unsubscribe function
        """
        with self._lock:
            self._global_handlers.append(handler)

        def unsubscribe() -> None:
            with self._lock:
                if handler in self._global_handlers:
                    self._global_handlers.remove(handler)

        return unsubscribe

    def on(self, event_type: Type[T]) -> Callable[[Handler[T]], Handler[T]]:
        """
        Decorator for subscribing to a specific event type.

        Usage:
            @bus.on(SessionCreatedEvent)
            def handle(event: SessionCreatedEvent):
                print(event.session_id)
        """
        def decorator(handler: Handler[T]) -> Handler[T]:
            self.subscribe(event_type, handler)
            return handler
        return decorator

    async def emit(self, event: EventDefinition) -> None:
        """
        Emit an event to all subscribers (async).

        Args:
            event: The event to emit
        """
        # Record in history
        with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

        # Get handlers for this event type
        event_type = type(event)
        handlers = list(self._handlers.get(event_type, [])) + list(self._global_handlers)

        # Call each handler
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(
                    f"Error in event handler for {event_type.__name__}: {e}",
                    exc_info=True
                )

    def emit_sync(self, event: EventDefinition) -> None:
        """
        Emit an event synchronously.

        Creates a task if running in an async context,
        otherwise runs in the event loop.
        """
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.emit(event))
        except RuntimeError:
            # No running loop, run synchronously
            asyncio.run(self.emit(event))

    def get_history(
        self,
        event_type: Type[T] | None = None,
        limit: int = 100,
    ) -> list[EventDefinition]:
        """Get recent events, optionally filtered by type."""
        events = self._history.copy()
        if event_type:
            events = [e for e in events if isinstance(e, event_type)]
        return events[-limit:]

    def clear(self) -> None:
        """Clear all handlers and history."""
        with self._lock:
            self._handlers.clear()
            self._global_handlers.clear()
            self._history.clear()

    def clear_history(self) -> None:
        """Clear event history only."""
        with self._lock:
            self._history.clear()


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_typed_bus: TypedEventBus | None = None
_bus_lock = Lock()


def get_typed_bus() -> TypedEventBus:
    """Get the global typed event bus."""
    global _typed_bus
    if _typed_bus is None:
        with _bus_lock:
            if _typed_bus is None:
                _typed_bus = TypedEventBus()
    return _typed_bus


def reset_typed_bus() -> None:
    """Reset the global typed event bus (for testing)."""
    global _typed_bus
    with _bus_lock:
        if _typed_bus:
            _typed_bus.clear()
        _typed_bus = None


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def emit(event: EventDefinition) -> None:
    """
    Emit a typed event to all subscribers.

    This is a synchronous function that schedules the async emit.
    Use `await emit_async(event)` for async code.
    """
    get_typed_bus().emit_sync(event)


async def emit_async(event: EventDefinition) -> None:
    """
    Emit a typed event asynchronously.

    Use in async code for proper awaiting of handlers.
    """
    await get_typed_bus().emit(event)


def subscribe(
    event_type: Type[T],
    handler: Handler[T],
) -> Callable[[], None]:
    """
    Subscribe to events of a specific type.

    Args:
        event_type: The event class to subscribe to
        handler: Callback function

    Returns:
        Unsubscribe function
    """
    return get_typed_bus().subscribe(event_type, handler)


def on(event_type: Type[T]) -> Callable[[Handler[T]], Handler[T]]:
    """
    Decorator for subscribing to a specific event type.

    Usage:
        @on(SessionCreatedEvent)
        def handle(event: SessionCreatedEvent):
            print(event.session_id)
    """
    return get_typed_bus().on(event_type)


def subscribe_all(handler: Handler[EventDefinition]) -> Callable[[], None]:
    """Subscribe to all events."""
    return get_typed_bus().subscribe_all(handler)


def get_history(
    event_type: Type[T] | None = None,
    limit: int = 100,
) -> list[EventDefinition]:
    """Get recent events from history."""
    return get_typed_bus().get_history(event_type, limit)
