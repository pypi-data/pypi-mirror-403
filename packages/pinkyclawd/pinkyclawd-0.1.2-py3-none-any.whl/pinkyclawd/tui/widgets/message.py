"""
Message display widget for conversation history.

Renders messages with proper formatting, syntax highlighting
for code blocks, tool output display, and metadata.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from textual.widgets import Static, Markdown, Collapsible
from textual.containers import Vertical, Horizontal, Container
from textual.app import ComposeResult
from textual.reactive import reactive
from rich.text import Text

from pinkyclawd.config.storage import Message, MessagePart, MessageRole, PartType
from pinkyclawd.tui.widgets.tool_view import get_tool_view


class MessageMetadata(Static):
    """Display message metadata (timestamp, model, cost)."""

    DEFAULT_CSS = """
    MessageMetadata {
        color: $text-muted;
        text-align: right;
        padding: 0 1;
        height: 1;
    }
    """

    def __init__(
        self,
        timestamp: datetime | None = None,
        model: str | None = None,
        tokens: int | None = None,
        cost: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.timestamp = timestamp
        self.model = model
        self.tokens = tokens
        self.cost = cost

    def compose(self) -> ComposeResult:
        text = Text()

        if self.timestamp:
            text.append(self.timestamp.strftime("%H:%M"), style="dim")

        if self.model:
            if text:
                text.append(" | ", style="dim")
            text.append(self.model, style="dim cyan")

        if self.tokens:
            if text:
                text.append(" | ", style="dim")
            text.append(f"{self.tokens:,} tokens", style="dim")

        if self.cost:
            if text:
                text.append(" | ", style="dim")
            text.append(f"${self.cost:.4f}", style="dim green")

        yield Static(text)


class ThinkingBlock(Collapsible):
    """Collapsible thinking/reasoning block."""

    DEFAULT_CSS = """
    ThinkingBlock {
        margin: 1 0;
        border-left: thick $secondary;
    }

    ThinkingBlock > Contents {
        padding: 1;
        background: $surface;
    }

    ThinkingBlock .thinking-content {
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(
        self,
        thinking_text: str,
        collapsed: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(title="Thinking...", collapsed=collapsed, **kwargs)
        self.thinking_text = thinking_text

    def compose(self) -> ComposeResult:
        # Limit display to first 500 chars
        display = self.thinking_text[:500]
        if len(self.thinking_text) > 500:
            display += "..."
        yield Static(display, classes="thinking-content")


class MessageView(Vertical):
    """
    Display a single message in the conversation.

    Handles:
    - User messages (simple text with left border)
    - Assistant messages (markdown with code, tool calls)
    - Thinking blocks (collapsible)
    - Timestamps and metadata
    - Tool calls and results
    - Streaming updates
    """

    DEFAULT_CSS = """
    MessageView {
        padding: 1;
        margin-bottom: 1;
    }

    MessageView.user {
        background: $primary 10%;
        border-left: thick $primary;
    }

    MessageView.assistant {
        background: $secondary 5%;
        border-left: thick $secondary;
    }

    MessageView.system {
        background: $surface;
        border-left: thick $primary;
    }

    MessageView.tool {
        background: $surface;
        border-left: thick $warning;
    }

    .message-header {
        height: 1;
    }

    .message-role {
        text-style: bold;
    }

    .message-role.user {
        color: $primary;
    }

    .message-role.assistant {
        color: $secondary;
    }

    .message-content {
        padding: 1 0;
    }

    .message-error {
        color: $error;
        text-style: bold;
    }

    .file-badge {
        background: $primary 30%;
        padding: 0 1;
        margin-right: 1;
    }
    """

    show_timestamps: reactive[bool] = reactive(True)
    show_metadata: reactive[bool] = reactive(True)
    show_thinking: reactive[bool] = reactive(True)
    show_tool_details: reactive[bool] = reactive(False)

    def __init__(
        self,
        message: Message,
        show_timestamps: bool = True,
        show_metadata: bool = True,
        show_thinking: bool = True,
        show_tool_details: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.message = message
        self.show_timestamps = show_timestamps
        self.show_metadata = show_metadata
        self.show_thinking = show_thinking
        self.show_tool_details = show_tool_details
        self.add_class(message.role.value)

    def compose(self) -> ComposeResult:
        # Header with role and timestamp
        with Horizontal(classes="message-header"):
            role_display = {
                MessageRole.USER: "You",
                MessageRole.ASSISTANT: "Assistant",
                MessageRole.SYSTEM: "System",
                MessageRole.TOOL: "Tool",
            }
            yield Static(
                role_display.get(self.message.role, "Unknown"),
                classes=f"message-role {self.message.role.value}",
            )

            # Timestamp
            if self.show_timestamps and self.message.created_at:
                yield Static(
                    self.message.created_at.strftime(" %H:%M"),
                    classes="message-timestamp",
                )

        # File badges for user messages
        if self.message.role == MessageRole.USER:
            yield from self._render_file_badges()

        # Message content
        yield from self._render_content()

        # Metadata for assistant messages
        if self.message.role == MessageRole.ASSISTANT and self.show_metadata:
            metadata = self.message.metadata or {}
            yield MessageMetadata(
                timestamp=self.message.created_at,
                model=metadata.get("model"),
                tokens=metadata.get("tokens"),
                cost=metadata.get("cost"),
            )

    def _render_file_badges(self) -> ComposeResult:
        """Render file attachment badges."""
        for part in self.message.parts:
            if part.type == PartType.IMAGE:
                path = part.content.get("path", "image")
                yield Static(f"[img] {path}", classes="file-badge")
            elif part.type == PartType.FILE:
                path = part.content.get("path", "file")
                yield Static(f"[file] {path}", classes="file-badge")

    def _render_content(self) -> ComposeResult:
        """Render message content parts."""
        for part in self.message.parts:
            yield from self._render_part(part)

        # Handle tool calls separately
        for tool_call in self.message.tool_calls:
            yield from self._render_tool_call(tool_call)

    def _render_part(self, part: MessagePart) -> ComposeResult:
        """Render a single message part."""
        if part.type == PartType.TEXT:
            text = part.content.get("text", "")
            if text.strip():
                yield Markdown(text, classes="message-content")

        elif part.type == PartType.THINKING:
            if self.show_thinking:
                thinking = part.content.get("thinking", "")
                yield ThinkingBlock(thinking, collapsed=True)

        elif part.type == PartType.TOOL_USE:
            tool_name = part.content.get("name", "unknown")
            tool_input = part.content.get("input", {})
            yield get_tool_view(
                tool_name=tool_name,
                tool_input=tool_input,
                is_running=True,
                show_details=self.show_tool_details,
            )

        elif part.type == PartType.TOOL_RESULT:
            tool_name = part.content.get("tool_name", "tool")
            output = part.content.get("content", "")
            is_error = part.content.get("is_error", False)
            yield get_tool_view(
                tool_name=tool_name,
                tool_output=output,
                is_error=is_error,
                show_details=self.show_tool_details,
            )

        elif part.type == PartType.ERROR:
            error = part.content.get("error", "Unknown error")
            yield Static(f"Error: {error}", classes="message-error")

    def _render_tool_call(self, tool_call: Any) -> ComposeResult:
        """Render a tool call."""
        name = getattr(tool_call, "name", str(tool_call))
        args = getattr(tool_call, "arguments", {})
        result = getattr(tool_call, "result", None)

        yield get_tool_view(
            tool_name=name,
            tool_input=args if isinstance(args, dict) else {},
            tool_output=result,
            show_details=self.show_tool_details,
        )

    def update_content(self, content: str) -> None:
        """Update the message content (for streaming)."""
        # Find and update the text content
        for part in self.message.parts:
            if part.type == PartType.TEXT:
                part.content["text"] = content
                break
        self.refresh(recompose=True)


class MessageList(Vertical):
    """
    Scrollable list of messages.

    Supports:
    - Automatic scrolling to bottom
    - Streaming message updates
    - Toggle display options
    - Keyboard navigation
    """

    DEFAULT_CSS = """
    MessageList {
        height: 1fr;
        overflow-y: scroll;
        padding: 1;
    }

    .empty-message {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }
    """

    show_timestamps: reactive[bool] = reactive(True)
    show_metadata: reactive[bool] = reactive(True)
    show_thinking: reactive[bool] = reactive(True)
    show_tool_details: reactive[bool] = reactive(False)

    def __init__(
        self,
        messages: list[Message] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.messages = messages or []

    def compose(self) -> ComposeResult:
        """Compose the message list."""
        if not self.messages:
            yield Static("Start a conversation...", classes="empty-message")
        else:
            for message in self.messages:
                yield MessageView(
                    message,
                    show_timestamps=self.show_timestamps,
                    show_metadata=self.show_metadata,
                    show_thinking=self.show_thinking,
                    show_tool_details=self.show_tool_details,
                )

    def add_message(self, message: Message) -> None:
        """Add a new message to the list."""
        self.messages.append(message)

        # Remove empty message placeholder if present
        empty = self.query(".empty-message")
        for e in empty:
            e.remove()

        # Add new message view
        self.mount(
            MessageView(
                message,
                show_timestamps=self.show_timestamps,
                show_metadata=self.show_metadata,
                show_thinking=self.show_thinking,
                show_tool_details=self.show_tool_details,
            )
        )
        self.scroll_end()

    def update_last_message(self, content: str) -> None:
        """Update the last message content (for streaming)."""
        if self.messages:
            # Update the message data
            last_msg = self.messages[-1]
            for part in last_msg.parts:
                if part.type == PartType.TEXT:
                    part.content["text"] = content
                    break

            # Update the view
            children = list(self.children)
            if children:
                last_view = children[-1]
                if isinstance(last_view, MessageView):
                    last_view.update_content(content)

    def clear_messages(self) -> None:
        """Clear all messages."""
        self.messages.clear()
        self.remove_children()
        self.mount(Static("Start a conversation...", classes="empty-message"))

    def toggle_timestamps(self) -> None:
        """Toggle timestamp visibility."""
        self.show_timestamps = not self.show_timestamps
        self.refresh(recompose=True)

    def toggle_thinking(self) -> None:
        """Toggle thinking block visibility."""
        self.show_thinking = not self.show_thinking
        self.refresh(recompose=True)

    def toggle_tool_details(self) -> None:
        """Toggle tool detail visibility."""
        self.show_tool_details = not self.show_tool_details
        self.refresh(recompose=True)
