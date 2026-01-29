"""
OpenAI provider implementation.
"""

from __future__ import annotations

import json
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


# OpenAI model definitions
OPENAI_MODELS: list[Model] = [
    Model(
        id="gpt-4o",
        name="GPT-4o",
        provider_id="openai",
        context_window=128000,
        max_output_tokens=16384,
        cost=ModelCost(input=2.5, output=10.0, cached_input=1.25),
        capabilities=ModelCapabilities(vision=True, function_calling=True),
    ),
    Model(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider_id="openai",
        context_window=128000,
        max_output_tokens=16384,
        cost=ModelCost(input=0.15, output=0.6, cached_input=0.075),
        capabilities=ModelCapabilities(vision=True, function_calling=True),
    ),
    Model(
        id="gpt-4-turbo",
        name="GPT-4 Turbo",
        provider_id="openai",
        context_window=128000,
        max_output_tokens=4096,
        cost=ModelCost(input=10.0, output=30.0),
        capabilities=ModelCapabilities(vision=True, function_calling=True),
    ),
    Model(
        id="o1",
        name="o1",
        provider_id="openai",
        context_window=200000,
        max_output_tokens=100000,
        cost=ModelCost(input=15.0, output=60.0, cached_input=7.5),
        capabilities=ModelCapabilities(vision=True, function_calling=True),
    ),
    Model(
        id="o1-mini",
        name="o1 Mini",
        provider_id="openai",
        context_window=128000,
        max_output_tokens=65536,
        cost=ModelCost(input=3.0, output=12.0, cached_input=1.5),
        capabilities=ModelCapabilities(vision=False, function_calling=True),
    ),
    Model(
        id="o3-mini",
        name="o3 Mini",
        provider_id="openai",
        context_window=200000,
        max_output_tokens=100000,
        cost=ModelCost(input=1.1, output=4.4, cached_input=0.55),
        capabilities=ModelCapabilities(vision=False, function_calling=True),
    ),
]


class OpenAIProvider(Provider):
    """OpenAI GPT provider."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        organization: str | None = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._base_url = base_url
        self._organization = organization
        self._client: Any = None

    @property
    def id(self) -> str:
        return "openai"

    @property
    def name(self) -> str:
        return "OpenAI"

    def _get_client(self) -> Any:
        """Get or create OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(
                    api_key=self._api_key,
                    base_url=self._base_url,
                    organization=self._organization,
                )
            except ImportError:
                raise ImportError("openai package required: pip install openai")
        return self._client

    async def list_models(self) -> list[Model]:
        """List available GPT models."""
        return OPENAI_MODELS.copy()

    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """Convert messages to OpenAI format."""
        converted = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                if isinstance(msg.content, str):
                    converted.append({"role": "system", "content": msg.content})

            elif msg.role == MessageRole.USER:
                if isinstance(msg.content, str):
                    converted.append({"role": "user", "content": msg.content})
                else:
                    content_list = []
                    for c in msg.content:
                        if c.type == "text" and c.text:
                            content_list.append({"type": "text", "text": c.text})
                        elif c.type == "image":
                            if c.image_url:
                                content_list.append(
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": c.image_url},
                                    }
                                )
                            elif c.image_base64:
                                content_list.append(
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{c.image_base64}"
                                        },
                                    }
                                )
                    converted.append({"role": "user", "content": content_list})

            elif msg.role == MessageRole.ASSISTANT:
                message_dict: dict[str, Any] = {"role": "assistant"}

                if isinstance(msg.content, str) and msg.content:
                    message_dict["content"] = msg.content

                if msg.tool_calls:
                    message_dict["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in msg.tool_calls
                    ]

                converted.append(message_dict)

            elif msg.role == MessageRole.TOOL:
                if isinstance(msg.content, list):
                    for c in msg.content:
                        if c.type == "tool_result" and c.tool_result:
                            converted.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": c.tool_result.tool_call_id,
                                    "content": c.tool_result.content,
                                }
                            )

        return converted

    def _convert_tools(self, tools: list[ToolDefinition] | None) -> list[dict] | None:
        """Convert tools to OpenAI format."""
        if not tools:
            return None

        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
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
        converted_messages = self._convert_messages(messages)
        converted_tools = self._convert_tools(tools)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": converted_messages,
            "temperature": temperature,
        }

        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        if converted_tools:
            kwargs["tools"] = converted_tools
        if stop:
            kwargs["stop"] = stop

        response = await client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        # Parse response
        text_content = choice.message.content or ""
        tool_calls = []

        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments),
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
        converted_messages = self._convert_messages(messages)
        converted_tools = self._convert_tools(tools)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": converted_messages,
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        if converted_tools:
            kwargs["tools"] = converted_tools
        if stop:
            kwargs["stop"] = stop

        current_tool_calls: dict[int, dict] = {}

        async for chunk in await client.chat.completions.create(**kwargs):
            if not chunk.choices:
                # Usage info
                if hasattr(chunk, "usage") and chunk.usage:
                    yield StreamChunk(
                        type="done",
                        input_tokens=chunk.usage.prompt_tokens,
                        output_tokens=chunk.usage.completion_tokens,
                    )
                continue

            delta = chunk.choices[0].delta

            # Text content
            if delta.content:
                yield StreamChunk(type="text", text=delta.content)

            # Tool calls
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index

                    if idx not in current_tool_calls:
                        current_tool_calls[idx] = {
                            "id": tc.id or "",
                            "name": tc.function.name if tc.function else "",
                            "arguments": "",
                        }
                        if tc.id and tc.function and tc.function.name:
                            yield StreamChunk(
                                type="tool_call_start",
                                tool_call_id=tc.id,
                                tool_name=tc.function.name,
                            )

                    if tc.function and tc.function.arguments:
                        current_tool_calls[idx]["arguments"] += tc.function.arguments
                        yield StreamChunk(
                            type="tool_call_delta",
                            tool_call_id=current_tool_calls[idx]["id"],
                            arguments_delta=tc.function.arguments,
                        )

            # Check for finish
            if chunk.choices[0].finish_reason == "tool_calls":
                for idx, tc_data in current_tool_calls.items():
                    yield StreamChunk(
                        type="tool_call_end",
                        tool_call_id=tc_data["id"],
                        tool_call=ToolCall(
                            id=tc_data["id"],
                            name=tc_data["name"],
                            arguments=json.loads(tc_data["arguments"])
                            if tc_data["arguments"]
                            else {},
                        ),
                    )

    async def count_tokens(self, messages: list[Message], model: str) -> int:
        """Count tokens using tiktoken."""
        try:
            import tiktoken

            # Get encoding for model
            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                encoding = tiktoken.get_encoding("cl100k_base")

            # Count tokens
            total = 0
            for msg in messages:
                total += 4  # Message overhead
                content = (
                    msg.content if isinstance(msg.content, str) else str(msg.content)
                )
                total += len(encoding.encode(content))

            return total
        except ImportError:
            # Fallback: estimate ~4 chars per token
            total_chars = sum(len(str(msg.content)) for msg in messages)
            return total_chars // 4
