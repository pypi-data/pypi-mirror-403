"""
Typed event bus system for PinkyClawd.

Provides a type-safe event system with Pydantic-based event definitions.

Usage:
    from pinkyclawd.bus import emit, on, SessionCreatedEvent

    # Emit a typed event
    emit(SessionCreatedEvent(session_id="abc123", title="New Session"))

    # Subscribe with decorator
    @on(SessionCreatedEvent)
    def handle_session_created(event: SessionCreatedEvent):
        print(f"Session created: {event.title}")
"""

from __future__ import annotations

# Event types
from pinkyclawd.bus.event_types import (
    # Base
    EventDefinition,
    define_event,
    # Session
    SessionCreatedEvent,
    SessionUpdatedEvent,
    SessionDeletedEvent,
    SessionActivatedEvent,
    SessionCompactedEvent,
    SessionForkedEvent,
    # Message
    MessageRole,
    MessageCreatedEvent,
    MessageUpdatedEvent,
    MessageCompletedEvent,
    MessageStreamingEvent,
    # Tool
    ToolStartedEvent,
    ToolCompletedEvent,
    ToolErrorEvent,
    ToolProgressEvent,
    # RLM
    RLMArchiveStartedEvent,
    RLMArchiveCompletedEvent,
    RLMContextRetrievedEvent,
    RLMContextInjectedEvent,
    RLMThresholdReachedEvent,
    # Permission
    PermissionDecision,
    PermissionRequestedEvent,
    PermissionDecidedEvent,
    # Provider
    ProviderConnectedEvent,
    ProviderDisconnectedEvent,
    ProviderErrorEvent,
    ProviderRateLimitedEvent,
    # UI
    ThemeChangedEvent,
    DialogOpenedEvent,
    DialogClosedEvent,
    ToastShownEvent,
    KeybindTriggeredEvent,
    # System
    ConfigChangedEvent,
    ShutdownEvent,
    StartupEvent,
    # Todo
    TodoStatus,
    TodoUpdatedEvent,
    TodoListChangedEvent,
)

# Global bus
from pinkyclawd.bus.global_bus import (
    TypedEventBus,
    get_typed_bus,
    reset_typed_bus,
    emit,
    emit_async,
    subscribe,
    on,
    subscribe_all,
    get_history,
)

__all__ = [
    # Base
    "EventDefinition",
    "define_event",
    # Session
    "SessionCreatedEvent",
    "SessionUpdatedEvent",
    "SessionDeletedEvent",
    "SessionActivatedEvent",
    "SessionCompactedEvent",
    "SessionForkedEvent",
    # Message
    "MessageRole",
    "MessageCreatedEvent",
    "MessageUpdatedEvent",
    "MessageCompletedEvent",
    "MessageStreamingEvent",
    # Tool
    "ToolStartedEvent",
    "ToolCompletedEvent",
    "ToolErrorEvent",
    "ToolProgressEvent",
    # RLM
    "RLMArchiveStartedEvent",
    "RLMArchiveCompletedEvent",
    "RLMContextRetrievedEvent",
    "RLMContextInjectedEvent",
    "RLMThresholdReachedEvent",
    # Permission
    "PermissionDecision",
    "PermissionRequestedEvent",
    "PermissionDecidedEvent",
    # Provider
    "ProviderConnectedEvent",
    "ProviderDisconnectedEvent",
    "ProviderErrorEvent",
    "ProviderRateLimitedEvent",
    # UI
    "ThemeChangedEvent",
    "DialogOpenedEvent",
    "DialogClosedEvent",
    "ToastShownEvent",
    "KeybindTriggeredEvent",
    # System
    "ConfigChangedEvent",
    "ShutdownEvent",
    "StartupEvent",
    # Todo
    "TodoStatus",
    "TodoUpdatedEvent",
    "TodoListChangedEvent",
    # Bus
    "TypedEventBus",
    "get_typed_bus",
    "reset_typed_bus",
    "emit",
    "emit_async",
    "subscribe",
    "on",
    "subscribe_all",
    "get_history",
]
