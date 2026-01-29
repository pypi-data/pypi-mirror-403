"""
Base provider interface for AI models.

Defines the abstract interface that all providers must implement,
plus common data structures for messages, tools, and streaming.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Literal


class MessageRole(str, Enum):
    """Message roles in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ToolCall:
    """A tool call from the model."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolResult:
    """Result of a tool execution."""

    tool_call_id: str
    content: str
    is_error: bool = False


@dataclass
class MessageContent:
    """Content of a message (text, image, etc.)."""

    type: Literal["text", "image", "tool_use", "tool_result"]
    text: str | None = None
    image_url: str | None = None
    image_base64: str | None = None
    tool_call: ToolCall | None = None
    tool_result: ToolResult | None = None


@dataclass
class Message:
    """A message in a conversation."""

    role: MessageRole
    content: list[MessageContent] | str
    name: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)

    @classmethod
    def user(cls, text: str) -> Message:
        """Create a user message."""
        return cls(role=MessageRole.USER, content=text)

    @classmethod
    def assistant(cls, text: str, tool_calls: list[ToolCall] | None = None) -> Message:
        """Create an assistant message."""
        return cls(
            role=MessageRole.ASSISTANT,
            content=text,
            tool_calls=tool_calls or [],
        )

    @classmethod
    def system(cls, text: str) -> Message:
        """Create a system message."""
        return cls(role=MessageRole.SYSTEM, content=text)

    @classmethod
    def tool(cls, tool_call_id: str, content: str, is_error: bool = False) -> Message:
        """Create a tool result message."""
        return cls(
            role=MessageRole.TOOL,
            content=[
                MessageContent(
                    type="tool_result",
                    tool_result=ToolResult(
                        tool_call_id=tool_call_id,
                        content=content,
                        is_error=is_error,
                    ),
                )
            ],
        )


@dataclass
class StreamChunk:
    """A chunk of streaming response."""

    type: Literal["text", "tool_call_start", "tool_call_delta", "tool_call_end", "done"]
    text: str | None = None
    tool_call: ToolCall | None = None
    tool_call_id: str | None = None
    tool_name: str | None = None
    arguments_delta: str | None = None

    # Usage info (only in final chunk)
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass
class ModelCost:
    """Cost per million tokens."""

    input: float = 0.0
    output: float = 0.0
    cached_input: float | None = None


@dataclass
class ModelCapabilities:
    """Model capabilities."""

    vision: bool = False
    function_calling: bool = True
    streaming: bool = True
    json_mode: bool = False
    system_message: bool = True


@dataclass
class Model:
    """An AI model definition."""

    id: str
    name: str
    provider_id: str
    context_window: int = 128000
    max_output_tokens: int = 4096
    cost: ModelCost = field(default_factory=ModelCost)
    capabilities: ModelCapabilities = field(default_factory=ModelCapabilities)
    default_temperature: float = 0.7

    @property
    def full_id(self) -> str:
        """Get full model ID (provider/model)."""
        return f"{self.provider_id}/{self.id}"


@dataclass
class ToolDefinition:
    """Tool definition for function calling."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema


class Provider(ABC):
    """
    Abstract base class for AI providers.

    Each provider (Anthropic, OpenAI, etc.) implements this interface
    to provide a consistent API for the application.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Provider identifier (e.g., 'anthropic', 'openai')."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...

    @abstractmethod
    async def list_models(self) -> list[Model]:
        """List available models from this provider."""
        ...

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[ToolDefinition] | None = None,
        stop: list[str] | None = None,
    ) -> Message:
        """
        Generate a completion (non-streaming).

        Args:
            messages: Conversation history
            model: Model ID to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Available tools for function calling
            stop: Stop sequences

        Returns:
            Assistant message with response
        """
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[ToolDefinition] | None = None,
        stop: list[str] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """
        Generate a streaming completion.

        Args:
            messages: Conversation history
            model: Model ID to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Available tools for function calling
            stop: Stop sequences

        Yields:
            Stream chunks as they arrive
        """
        ...

    @abstractmethod
    async def count_tokens(self, messages: list[Message], model: str) -> int:
        """
        Count tokens in messages.

        Args:
            messages: Messages to count
            model: Model to use for tokenization

        Returns:
            Token count
        """
        ...

    async def validate_api_key(self) -> bool:
        """
        Validate the API key is working.

        Returns:
            True if API key is valid
        """
        try:
            await self.list_models()
            return True
        except Exception:
            return False
