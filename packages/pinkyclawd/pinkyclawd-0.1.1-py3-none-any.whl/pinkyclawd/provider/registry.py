"""
Provider registry for managing AI providers and models.
"""

from __future__ import annotations

import os
from typing import Any

from pinkyclawd.provider.base import Provider, Model
from pinkyclawd.provider.anthropic import AnthropicProvider
from pinkyclawd.provider.openai import OpenAIProvider


class ProviderRegistry:
    """
    Registry for AI providers.

    Manages provider instances and provides unified access to models
    across all registered providers.
    """

    def __init__(self) -> None:
        self._providers: dict[str, Provider] = {}
        self._models_cache: dict[str, Model] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all available providers."""
        if self._initialized:
            return

        # Register Anthropic if API key available
        if os.environ.get("ANTHROPIC_API_KEY"):
            try:
                provider = AnthropicProvider()
                self.register(provider)
            except Exception:
                pass

        # Register OpenAI if API key available
        if os.environ.get("OPENAI_API_KEY"):
            try:
                provider = OpenAIProvider()
                self.register(provider)
            except Exception:
                pass

        # Build models cache
        await self._build_models_cache()
        self._initialized = True

    async def _build_models_cache(self) -> None:
        """Build cache of all available models."""
        self._models_cache.clear()

        for provider in self._providers.values():
            try:
                models = await provider.list_models()
                for model in models:
                    self._models_cache[model.full_id] = model
            except Exception:
                continue

    def register(self, provider: Provider) -> None:
        """Register a provider."""
        self._providers[provider.id] = provider

    def unregister(self, provider_id: str) -> None:
        """Unregister a provider."""
        self._providers.pop(provider_id, None)

    def get_provider(self, provider_id: str) -> Provider | None:
        """Get a provider by ID."""
        return self._providers.get(provider_id)

    def list_providers(self) -> list[Provider]:
        """List all registered providers."""
        return list(self._providers.values())

    def get_model(self, model_id: str) -> Model | None:
        """
        Get a model by full ID (provider/model).

        Args:
            model_id: Full model ID like 'anthropic/claude-sonnet-4-20250514'

        Returns:
            Model if found, None otherwise
        """
        return self._models_cache.get(model_id)

    def list_models(self, provider_id: str | None = None) -> list[Model]:
        """
        List all available models.

        Args:
            provider_id: Optional filter by provider

        Returns:
            List of models
        """
        models = list(self._models_cache.values())

        if provider_id:
            models = [m for m in models if m.provider_id == provider_id]

        return sorted(models, key=lambda m: m.name)

    def parse_model_id(self, model_id: str) -> tuple[str, str] | None:
        """
        Parse a model ID into provider and model parts.

        Args:
            model_id: Full model ID like 'anthropic/claude-sonnet-4-20250514'

        Returns:
            Tuple of (provider_id, model_id) or None if invalid
        """
        parts = model_id.split("/", 1)
        if len(parts) != 2:
            return None
        return parts[0], parts[1]

    async def complete(
        self,
        model_id: str,
        messages: list[Any],
        **kwargs: Any,
    ) -> Any:
        """
        Generate a completion using the specified model.

        Args:
            model_id: Full model ID
            messages: Conversation messages
            **kwargs: Additional arguments for the provider

        Returns:
            Assistant message
        """
        parsed = self.parse_model_id(model_id)
        if not parsed:
            raise ValueError(f"Invalid model ID: {model_id}")

        provider_id, model = parsed
        provider = self.get_provider(provider_id)
        if not provider:
            raise ValueError(f"Provider not found: {provider_id}")

        return await provider.complete(messages, model, **kwargs)

    async def stream(
        self,
        model_id: str,
        messages: list[Any],
        **kwargs: Any,
    ) -> Any:
        """
        Generate a streaming completion.

        Args:
            model_id: Full model ID
            messages: Conversation messages
            **kwargs: Additional arguments for the provider

        Returns:
            Async iterator of stream chunks
        """
        parsed = self.parse_model_id(model_id)
        if not parsed:
            raise ValueError(f"Invalid model ID: {model_id}")

        provider_id, model = parsed
        provider = self.get_provider(provider_id)
        if not provider:
            raise ValueError(f"Provider not found: {provider_id}")

        return provider.stream(messages, model, **kwargs)

    async def count_tokens(self, model_id: str, messages: list[Any]) -> int:
        """
        Count tokens for messages.

        Args:
            model_id: Full model ID
            messages: Messages to count

        Returns:
            Token count
        """
        parsed = self.parse_model_id(model_id)
        if not parsed:
            raise ValueError(f"Invalid model ID: {model_id}")

        provider_id, model = parsed
        provider = self.get_provider(provider_id)
        if not provider:
            raise ValueError(f"Provider not found: {provider_id}")

        return await provider.count_tokens(messages, model)


# Global registry instance
_registry: ProviderRegistry | None = None


async def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry, initializing if needed."""
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
        await _registry.initialize()
    return _registry


def get_provider(provider_id: str) -> Provider | None:
    """Get a provider by ID (sync version, requires prior initialization)."""
    if _registry is None:
        return None
    return _registry.get_provider(provider_id)


def get_model(model_id: str) -> Model | None:
    """Get a model by ID (sync version, requires prior initialization)."""
    if _registry is None:
        return None
    return _registry.get_model(model_id)
