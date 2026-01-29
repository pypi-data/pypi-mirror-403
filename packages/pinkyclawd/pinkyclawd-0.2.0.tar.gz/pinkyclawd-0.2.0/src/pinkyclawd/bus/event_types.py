"""
Typed event definitions for PinkyClawd.

Provides Pydantic-based event types for type-safe event handling,
replacing string-keyed dictionaries with structured objects.

Usage:
    from pinkyclawd.bus import SessionCreatedEvent, emit

    # Emit a typed event
    emit(SessionCreatedEvent(session_id="abc123", title="New Session"))

    # Subscribe to a typed event
    @on(SessionCreatedEvent)
    def handle_session_created(event: SessionCreatedEvent):
        print(f"Session created: {event.title}")
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, TypeVar, Generic, Literal
from pydantic import BaseModel, Field
from enum import Enum


# =============================================================================
# BASE EVENT
# =============================================================================

class EventDefinition(BaseModel):
    """Base class for all typed events."""

    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = ""

    class Config:
        frozen = True

    @classmethod
    def event_name(cls) -> str:
        """Get the canonical event name."""
        # Convert CamelCase to dot.notation
        # e.g., SessionCreatedEvent -> session.created
        name = cls.__name__
        if name.endswith("Event"):
            name = name[:-5]
        # Insert dots before capitals
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append(".")
            result.append(char.lower())
        return "".join(result)


def define_event(name: str):
    """Decorator to set a custom event name."""
    def decorator(cls):
        cls._event_name = name
        original_event_name = cls.event_name

        @classmethod
        def event_name(cls) -> str:
            return getattr(cls, "_event_name", original_event_name())

        cls.event_name = event_name
        return cls
    return decorator


# =============================================================================
# SESSION EVENTS
# =============================================================================

@define_event("session.created")
class SessionCreatedEvent(EventDefinition):
    """Emitted when a new session is created."""
    session_id: str
    title: str = ""
    directory: str = ""
    parent_id: str | None = None


@define_event("session.updated")
class SessionUpdatedEvent(EventDefinition):
    """Emitted when a session is updated."""
    session_id: str
    changes: dict[str, Any] = Field(default_factory=dict)


@define_event("session.deleted")
class SessionDeletedEvent(EventDefinition):
    """Emitted when a session is deleted."""
    session_id: str


@define_event("session.activated")
class SessionActivatedEvent(EventDefinition):
    """Emitted when a session becomes active."""
    session_id: str
    previous_session_id: str | None = None


@define_event("session.compacted")
class SessionCompactedEvent(EventDefinition):
    """Emitted when a session is compacted."""
    session_id: str
    messages_removed: int
    tokens_removed: int


@define_event("session.forked")
class SessionForkedEvent(EventDefinition):
    """Emitted when a session is forked."""
    session_id: str
    parent_id: str
    fork_point_message_id: str


# =============================================================================
# MESSAGE EVENTS
# =============================================================================

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@define_event("message.created")
class MessageCreatedEvent(EventDefinition):
    """Emitted when a new message is created."""
    session_id: str
    message_id: str
    role: MessageRole


@define_event("message.updated")
class MessageUpdatedEvent(EventDefinition):
    """Emitted when a message is updated."""
    session_id: str
    message_id: str
    part_id: str | None = None


@define_event("message.completed")
class MessageCompletedEvent(EventDefinition):
    """Emitted when a message is fully complete (streaming finished)."""
    session_id: str
    message_id: str
    tokens_used: int = 0


@define_event("message.streaming")
class MessageStreamingEvent(EventDefinition):
    """Emitted during message streaming with partial content."""
    session_id: str
    message_id: str
    content_delta: str = ""
    is_final: bool = False


# =============================================================================
# TOOL EVENTS
# =============================================================================

@define_event("tool.started")
class ToolStartedEvent(EventDefinition):
    """Emitted when a tool starts executing."""
    session_id: str
    message_id: str
    tool_name: str
    tool_id: str
    arguments: dict[str, Any] = Field(default_factory=dict)


@define_event("tool.completed")
class ToolCompletedEvent(EventDefinition):
    """Emitted when a tool completes successfully."""
    session_id: str
    message_id: str
    tool_name: str
    tool_id: str
    result_preview: str = ""
    duration_ms: int = 0


@define_event("tool.error")
class ToolErrorEvent(EventDefinition):
    """Emitted when a tool fails."""
    session_id: str
    message_id: str
    tool_name: str
    tool_id: str
    error: str
    error_type: str = ""


@define_event("tool.progress")
class ToolProgressEvent(EventDefinition):
    """Emitted during long-running tool execution."""
    session_id: str
    tool_id: str
    progress: float  # 0.0 to 1.0
    status: str = ""


# =============================================================================
# RLM EVENTS
# =============================================================================

@define_event("rlm.archive.started")
class RLMArchiveStartedEvent(EventDefinition):
    """Emitted when context archival begins."""
    session_id: str
    messages_count: int
    tokens_count: int


@define_event("rlm.archive.completed")
class RLMArchiveCompletedEvent(EventDefinition):
    """Emitted when context archival completes."""
    session_id: str
    block_id: str
    messages_archived: int
    tokens_archived: int
    summary: str = ""


@define_event("rlm.context.retrieved")
class RLMContextRetrievedEvent(EventDefinition):
    """Emitted when context is retrieved from archives."""
    session_id: str
    blocks_count: int
    tokens_count: int
    trigger: str = ""  # What triggered the retrieval


@define_event("rlm.context.injected")
class RLMContextInjectedEvent(EventDefinition):
    """Emitted when archived context is injected into conversation."""
    session_id: str
    blocks: list[str] = Field(default_factory=list)
    total_tokens: int = 0


@define_event("rlm.threshold.reached")
class RLMThresholdReachedEvent(EventDefinition):
    """Emitted when context usage reaches archival threshold."""
    session_id: str
    usage_ratio: float
    tokens_used: int
    tokens_limit: int


# =============================================================================
# PERMISSION EVENTS
# =============================================================================

class PermissionDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


@define_event("permission.requested")
class PermissionRequestedEvent(EventDefinition):
    """Emitted when a permission is requested."""
    session_id: str
    tool_name: str
    action: str
    path: str = ""
    command: str = ""


@define_event("permission.decided")
class PermissionDecidedEvent(EventDefinition):
    """Emitted when a permission decision is made."""
    session_id: str
    tool_name: str
    decision: PermissionDecision
    remember: bool = False


# =============================================================================
# PROVIDER EVENTS
# =============================================================================

@define_event("provider.connected")
class ProviderConnectedEvent(EventDefinition):
    """Emitted when a provider is connected."""
    provider_name: str
    model: str = ""


@define_event("provider.disconnected")
class ProviderDisconnectedEvent(EventDefinition):
    """Emitted when a provider is disconnected."""
    provider_name: str
    reason: str = ""


@define_event("provider.error")
class ProviderErrorEvent(EventDefinition):
    """Emitted when a provider encounters an error."""
    provider_name: str
    error: str
    error_type: str = ""
    is_retryable: bool = False


@define_event("provider.rate_limited")
class ProviderRateLimitedEvent(EventDefinition):
    """Emitted when rate limited by a provider."""
    provider_name: str
    retry_after_seconds: int = 0


# =============================================================================
# UI EVENTS
# =============================================================================

@define_event("ui.theme.changed")
class ThemeChangedEvent(EventDefinition):
    """Emitted when the UI theme changes."""
    theme_name: str
    previous_theme: str = ""


@define_event("ui.dialog.opened")
class DialogOpenedEvent(EventDefinition):
    """Emitted when a dialog is opened."""
    dialog_type: str
    dialog_id: str = ""


@define_event("ui.dialog.closed")
class DialogClosedEvent(EventDefinition):
    """Emitted when a dialog is closed."""
    dialog_type: str
    dialog_id: str = ""
    result: str = ""


@define_event("ui.toast.shown")
class ToastShownEvent(EventDefinition):
    """Emitted when a toast notification is shown."""
    message: str
    level: Literal["info", "warning", "error", "success"] = "info"
    duration_ms: int = 3000


@define_event("ui.keybind.triggered")
class KeybindTriggeredEvent(EventDefinition):
    """Emitted when a keybind is triggered."""
    key: str
    action: str


# =============================================================================
# SYSTEM EVENTS
# =============================================================================

@define_event("system.config.changed")
class ConfigChangedEvent(EventDefinition):
    """Emitted when configuration changes."""
    key: str
    old_value: Any = None
    new_value: Any = None


@define_event("system.shutdown")
class ShutdownEvent(EventDefinition):
    """Emitted when the application is shutting down."""
    reason: str = ""
    force: bool = False


@define_event("system.startup")
class StartupEvent(EventDefinition):
    """Emitted when the application starts up."""
    version: str = ""


# =============================================================================
# TODO EVENTS
# =============================================================================

class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@define_event("todo.updated")
class TodoUpdatedEvent(EventDefinition):
    """Emitted when a todo item is updated."""
    session_id: str
    todo_id: str
    content: str
    status: TodoStatus
    previous_status: TodoStatus | None = None


@define_event("todo.list.changed")
class TodoListChangedEvent(EventDefinition):
    """Emitted when the todo list changes."""
    session_id: str
    total_count: int
    completed_count: int
    in_progress_count: int


# =============================================================================
# TYPE EXPORTS
# =============================================================================

T = TypeVar("T", bound=EventDefinition)

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
]
