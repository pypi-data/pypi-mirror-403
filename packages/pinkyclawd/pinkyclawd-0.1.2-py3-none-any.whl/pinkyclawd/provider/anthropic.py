"""
Anthropic Claude provider implementation.
"""

from __future__ import annotations

import os
from typing import Any, AsyncIterator

from pinkyclawd.provider.base import (
    Provider,
    Model,
    ModelCost,
    ModelCapabilities,
    Message,
    MessageRole,
    MessageContent,
    StreamChunk,
    ToolCall,
    ToolDefinition,
)


# Anthropic model definitions
ANTHROPIC_MODELS: list[Model] = [
    Model(
        id="claude-sonnet-4-20250514",
        name="Claude Sonnet 4",
        provider_id="anthropic",
        context_window=200000,
        max_output_tokens=16384,
        cost=ModelCost(input=3.0, output=15.0, cached_input=0.3),
        capabilities=ModelCapabilities(vision=True, function_calling=True),
    ),
    Model(
        id="claude-opus-4-20250514",
        name="Claude Opus 4",
        provider_id="anthropic",
        context_window=200000,
        max_output_tokens=16384,
        cost=ModelCost(input=15.0, output=75.0, cached_input=1.5),
        capabilities=ModelCapabilities(vision=True, function_calling=True),
    ),
    Model(
        id="claude-3-5-sonnet-20241022",
        name="Claude 3.5 Sonnet",
        provider_id="anthropic",
        context_window=200000,
        max_output_tokens=8192,
        cost=ModelCost(input=3.0, output=15.0, cached_input=0.3),
        capabilities=ModelCapabilities(vision=True, function_calling=True),
    ),
    Model(
        id="claude-3-5-haiku-20241022",
        name="Claude 3.5 Haiku",
        provider_id="anthropic",
        context_window=200000,
        max_output_tokens=8192,
        cost=ModelCost(input=0.8, output=4.0, cached_input=0.08),
        capabilities=ModelCapabilities(vision=True, function_calling=True),
    ),
    Model(
        id="claude-3-opus-20240229",
        name="Claude 3 Opus",
        provider_id="anthropic",
        context_window=200000,
        max_output_tokens=4096,
        cost=ModelCost(input=15.0, output=75.0, cached_input=1.5),
        capabilities=ModelCapabilities(vision=True, function_calling=True),
    ),
]


class AnthropicProvider(Provider):
    """Anthropic Claude provider."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._base_url = base_url or "https://api.anthropic.com"
        self._client: Any = None

    @property
    def id(self) -> str:
        return "anthropic"

    @property
    def name(self) -> str:
        return "Anthropic"

    def _get_client(self) -> Any:
        """Get or create Anthropic client."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic

                self._client = AsyncAnthropic(
                    api_key=self._api_key,
                    base_url=self._base_url
                    if self._base_url != "https://api.anthropic.com"
                    else None,
                )
            except ImportError:
                raise ImportError("anthropic package required: pip install anthropic")
        return self._client

    async def list_models(self) -> list[Model]:
        """List available Claude models."""
        return ANTHROPIC_MODELS.copy()

    def _convert_messages(
        self, messages: list[Message]
    ) -> tuple[str | None, list[dict]]:
        """Convert messages to Anthropic format."""
        system_message = None
        converted = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                if isinstance(msg.content, str):
                    system_message = msg.content
                continue

            if msg.role == MessageRole.USER:
                if isinstance(msg.content, str):
                    converted.append({"role": "user", "content": msg.content})
                else:
                    content_list = []
                    for c in msg.content:
                        if c.type == "text" and c.text:
                            content_list.append({"type": "text", "text": c.text})
                        elif c.type == "image" and c.image_base64:
                            content_list.append(
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": c.image_base64,
                                    },
                                }
                            )
                    converted.append({"role": "user", "content": content_list})

            elif msg.role == MessageRole.ASSISTANT:
                content_list = []
                if isinstance(msg.content, str) and msg.content:
                    content_list.append({"type": "text", "text": msg.content})

                for tc in msg.tool_calls:
                    content_list.append(
                        {
                            "type": "tool_use",
                            "id": tc.id,
                            "name": tc.name,
                            "input": tc.arguments,
                        }
                    )

                if content_list:
                    converted.append({"role": "assistant", "content": content_list})

            elif msg.role == MessageRole.TOOL:
                if isinstance(msg.content, list):
                    for c in msg.content:
                        if c.type == "tool_result" and c.tool_result:
                            converted.append(
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "tool_result",
                                            "tool_use_id": c.tool_result.tool_call_id,
                                            "content": c.tool_result.content,
                                            "is_error": c.tool_result.is_error,
                                        }
                                    ],
                                }
                            )

        return system_message, converted

    def _convert_tools(self, tools: list[ToolDefinition] | None) -> list[dict] | None:
        """Convert tools to Anthropic format."""
        if not tools:
            return None

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            }
            for tool in tools
        ]

    async def complete(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[ToolDefinition] | None = None,
        stop: list[str] | None = None,
    ) -> Message:
        """Generate a completion."""
        client = self._get_client()
        system, converted_messages = self._convert_messages(messages)
        converted_tools = self._convert_tools(tools)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": converted_messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
        }

        if system:
            kwargs["system"] = system
        if converted_tools:
            kwargs["tools"] = converted_tools
        if stop:
            kwargs["stop_sequences"] = stop

        response = await client.messages.create(**kwargs)

        # Parse response
        text_content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                text_content += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input,
                    )
                )

        return Message.assistant(text_content, tool_calls)

    async def stream(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[ToolDefinition] | None = None,
        stop: list[str] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Generate a streaming completion."""
        client = self._get_client()
        system, converted_messages = self._convert_messages(messages)
        converted_tools = self._convert_tools(tools)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": converted_messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
        }

        if system:
            kwargs["system"] = system
        if converted_tools:
            kwargs["tools"] = converted_tools
        if stop:
            kwargs["stop_sequences"] = stop

        async with client.messages.stream(**kwargs) as stream:
            current_tool_id = None
            current_tool_name = None

            async for event in stream:
                if event.type == "content_block_start":
                    if hasattr(event.content_block, "type"):
                        if event.content_block.type == "tool_use":
                            current_tool_id = event.content_block.id
                            current_tool_name = event.content_block.name
                            yield StreamChunk(
                                type="tool_call_start",
                                tool_call_id=current_tool_id,
                                tool_name=current_tool_name,
                            )

                elif event.type == "content_block_delta":
                    if hasattr(event.delta, "text"):
                        yield StreamChunk(type="text", text=event.delta.text)
                    elif hasattr(event.delta, "partial_json"):
                        yield StreamChunk(
                            type="tool_call_delta",
                            tool_call_id=current_tool_id,
                            arguments_delta=event.delta.partial_json,
                        )

                elif event.type == "content_block_stop":
                    if current_tool_id:
                        yield StreamChunk(
                            type="tool_call_end",
                            tool_call_id=current_tool_id,
                        )
                        current_tool_id = None
                        current_tool_name = None

                elif event.type == "message_delta":
                    if hasattr(event, "usage"):
                        yield StreamChunk(
                            type="done",
                            input_tokens=getattr(event.usage, "input_tokens", None),
                            output_tokens=getattr(event.usage, "output_tokens", None),
                        )

    async def count_tokens(self, messages: list[Message], model: str) -> int:
        """Count tokens using Anthropic's tokenizer."""
        client = self._get_client()
        system, converted_messages = self._convert_messages(messages)

        try:
            result = await client.messages.count_tokens(
                model=model,
                messages=converted_messages,
                system=system or "",
            )
            return result.input_tokens
        except Exception:
            # Fallback: estimate ~4 chars per token
            total_chars = sum(len(str(msg.content)) for msg in messages)
            return total_chars // 4
