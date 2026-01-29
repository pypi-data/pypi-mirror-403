"""
Embedding generation for semantic search in RLM.

Supports multiple embedding providers:
- OpenAI: text-embedding-3-small (1536 dims), text-embedding-3-large (3072 dims)
- Google: text-embedding-004 (768 dims)
- Mistral: mistral-embed (1024 dims)
- Voyage AI: voyage-3 (1024 dims) - recommended for Anthropic users
- Local: sentence-transformers fallback (384 dims)

Provider selection priority (auto mode):
1. OpenAI (if OPENAI_API_KEY set)
2. Google (if GOOGLE_API_KEY set)
3. Mistral (if MISTRAL_API_KEY set)
4. Voyage (if VOYAGE_API_KEY set)
5. Local (always available)

The embedding system generates vector representations of archived context
blocks to enable semantic similarity search.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from pinkyclawd.config.settings import get_config

logger = logging.getLogger(__name__)


# Embedding dimensions by model
EMBEDDING_DIMENSIONS = {
    # OpenAI
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
    # Voyage AI (for Anthropic users)
    "voyage-3": 1024,
    "voyage-3-lite": 512,
    "voyage-code-3": 1024,
    # Google
    "text-embedding-004": 768,
    # Mistral
    "mistral-embed": 1024,
    # Local fallback
    "local": 384,
}

# Default models by provider
DEFAULT_EMBEDDING_MODELS = {
    "openai": "text-embedding-3-small",
    "anthropic": "voyage-3",  # Via Voyage AI
    "google": "text-embedding-004",
    "mistral": "mistral-embed",
    "local": "local",
}


@dataclass
class Embedding:
    """A vector embedding for a context block."""

    block_id: str
    vector: list[float]
    model: str
    dimensions: int
    content_hash: str  # To detect if re-embedding is needed
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_id": self.block_id,
            "vector": self.vector,
            "model": self.model,
            "dimensions": self.dimensions,
            "content_hash": self.content_hash,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Embedding:
        return cls(
            block_id=data["block_id"],
            vector=data["vector"],
            model=data["model"],
            dimensions=data["dimensions"],
            content_hash=data["content_hash"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )


def compute_content_hash(content: str) -> str:
    """Compute a hash of content to detect changes."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score between -1 and 1
    """
    if len(vec1) != len(vec2):
        logger.warning(f"Vector dimension mismatch: {len(vec1)} vs {len(vec2)}")
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Model identifier."""
        pass

    @property
    def dimensions(self) -> int:
        """Embedding dimensions for this model."""
        return EMBEDDING_DIMENSIONS.get(self.model, 1536)

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    def is_available(self) -> bool:
        """Check if this provider is available (has API key, etc.)."""
        return True


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider using text-embedding-3-small."""

    def __init__(self, model: str = "text-embedding-3-small") -> None:
        self._model = model
        self._client: Any = None

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model(self) -> str:
        return self._model

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI()
            except ImportError:
                raise RuntimeError("openai package not installed")
        return self._client

    def is_available(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))

    async def embed(self, text: str) -> list[float]:
        client = self._get_client()
        response = await client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        client = self._get_client()

        # OpenAI supports batching up to 2048 texts
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = await client.embeddings.create(
                model=self._model,
                input=batch,
            )
            # Sort by index to maintain order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            all_embeddings.extend([d.embedding for d in sorted_data])

        return all_embeddings


class VoyageEmbeddingProvider(EmbeddingProvider):
    """
    Voyage AI embedding provider for Anthropic users.

    Voyage AI provides high-quality embeddings optimized for retrieval.
    """

    def __init__(self, model: str = "voyage-3") -> None:
        self._model = model
        self._client: Any = None

    @property
    def name(self) -> str:
        return "voyage"

    @property
    def model(self) -> str:
        return self._model

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                import voyageai

                self._client = voyageai.AsyncClient()
            except ImportError:
                raise RuntimeError("voyageai package not installed. Install with: pip install voyageai")
        return self._client

    def is_available(self) -> bool:
        return bool(os.environ.get("VOYAGE_API_KEY"))

    async def embed(self, text: str) -> list[float]:
        client = self._get_client()
        result = await client.embed(
            texts=[text],
            model=self._model,
            input_type="document",
        )
        return result.embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        client = self._get_client()

        # Voyage supports up to 128 texts per batch
        batch_size = 128
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            result = await client.embed(
                texts=batch,
                model=self._model,
                input_type="document",
            )
            all_embeddings.extend(result.embeddings)

        return all_embeddings


class GoogleEmbeddingProvider(EmbeddingProvider):
    """
    Google embedding provider using text-embedding-004.

    Requires the google-generativeai package and GOOGLE_API_KEY environment variable.
    """

    def __init__(self, model: str = "text-embedding-004") -> None:
        self._model = model
        self._client: Any = None

    @property
    def name(self) -> str:
        return "google"

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return EMBEDDING_DIMENSIONS.get(self._model, 768)

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                import google.generativeai as genai

                api_key = os.environ.get("GOOGLE_API_KEY")
                if not api_key:
                    raise RuntimeError("GOOGLE_API_KEY not set")
                genai.configure(api_key=api_key)
                self._client = genai
            except ImportError:
                raise RuntimeError(
                    "google-generativeai package not installed. "
                    "Install with: pip install google-generativeai"
                )
        return self._client

    def is_available(self) -> bool:
        return bool(os.environ.get("GOOGLE_API_KEY"))

    async def embed(self, text: str) -> list[float]:
        import asyncio

        client = self._get_client()

        # google-generativeai is synchronous, run in executor
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: client.embed_content(
                model=f"models/{self._model}",
                content=text,
                task_type="retrieval_document",
            ),
        )
        return result["embedding"]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        import asyncio

        client = self._get_client()
        loop = asyncio.get_event_loop()

        # Google supports batching
        result = await loop.run_in_executor(
            None,
            lambda: client.embed_content(
                model=f"models/{self._model}",
                content=texts,
                task_type="retrieval_document",
            ),
        )
        return result["embedding"]


class MistralEmbeddingProvider(EmbeddingProvider):
    """
    Mistral embedding provider using mistral-embed.

    Requires the mistralai package and MISTRAL_API_KEY environment variable.
    """

    def __init__(self, model: str = "mistral-embed") -> None:
        self._model = model
        self._client: Any = None

    @property
    def name(self) -> str:
        return "mistral"

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return EMBEDDING_DIMENSIONS.get(self._model, 1024)

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from mistralai import Mistral

                api_key = os.environ.get("MISTRAL_API_KEY")
                if not api_key:
                    raise RuntimeError("MISTRAL_API_KEY not set")
                self._client = Mistral(api_key=api_key)
            except ImportError:
                raise RuntimeError(
                    "mistralai package not installed. "
                    "Install with: pip install mistralai"
                )
        return self._client

    def is_available(self) -> bool:
        return bool(os.environ.get("MISTRAL_API_KEY"))

    async def embed(self, text: str) -> list[float]:
        client = self._get_client()
        response = await client.embeddings.create_async(
            model=self._model,
            inputs=[text],
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        client = self._get_client()

        # Mistral supports batching
        all_embeddings = []
        batch_size = 100  # Reasonable batch size

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = await client.embeddings.create_async(
                model=self._model,
                inputs=batch,
            )
            # Sort by index to maintain order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            all_embeddings.extend([d.embedding for d in sorted_data])

        return all_embeddings


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Local embedding provider using sentence-transformers.

    Falls back to a simple TF-IDF based approach if sentence-transformers
    is not available.
    """

    def __init__(self, model: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model
        self._model: Any = None
        self._use_sentence_transformers = True

    @property
    def name(self) -> str:
        return "local"

    @property
    def model(self) -> str:
        return "local"

    @property
    def dimensions(self) -> int:
        return 384  # all-MiniLM-L6-v2 dimension

    def _get_model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self._model_name)
                self._use_sentence_transformers = True
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed, using simple fallback. "
                    "Install with: pip install sentence-transformers"
                )
                self._use_sentence_transformers = False
                self._model = "fallback"
        return self._model

    def is_available(self) -> bool:
        return True  # Always available with fallback

    def _simple_embed(self, text: str) -> list[float]:
        """Simple hash-based embedding fallback."""
        # Create a deterministic but simple embedding
        # This is NOT semantic but provides consistent vectors for exact matching
        import hashlib

        # Normalize and hash
        text = text.lower().strip()
        hash_bytes = hashlib.sha384(text.encode()).digest()

        # Convert to float vector
        vector = []
        for i in range(0, len(hash_bytes), 4):
            chunk = hash_bytes[i : i + 4]
            value = int.from_bytes(chunk, "big") / (2**32) - 0.5
            vector.append(value)

        # Pad to 384 dimensions
        while len(vector) < 384:
            vector.append(0.0)

        # Normalize
        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]

        return vector[:384]

    async def embed(self, text: str) -> list[float]:
        model = self._get_model()

        if self._use_sentence_transformers:
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        else:
            return self._simple_embed(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        model = self._get_model()

        if self._use_sentence_transformers:
            embeddings = model.encode(texts, convert_to_numpy=True)
            return [e.tolist() for e in embeddings]
        else:
            return [self._simple_embed(text) for text in texts]


class EmbeddingManager:
    """
    Manages embedding generation and caching.

    Automatically selects the best available provider and handles
    embedding generation for context blocks.
    """

    _instance: EmbeddingManager | None = None

    def __new__(cls) -> EmbeddingManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._providers: dict[str, EmbeddingProvider] = {}
        self._current_provider: EmbeddingProvider | None = None
        self._cache: dict[str, Embedding] = {}
        self._initialized = True
        self._register_providers()

    def _register_providers(self) -> None:
        """Register available embedding providers."""
        # OpenAI
        openai_provider = OpenAIEmbeddingProvider()
        if openai_provider.is_available():
            self._providers["openai"] = openai_provider
            logger.info("OpenAI embedding provider available")

        # Google
        google_provider = GoogleEmbeddingProvider()
        if google_provider.is_available():
            self._providers["google"] = google_provider
            logger.info("Google embedding provider available")

        # Mistral
        mistral_provider = MistralEmbeddingProvider()
        if mistral_provider.is_available():
            self._providers["mistral"] = mistral_provider
            logger.info("Mistral embedding provider available")

        # Voyage AI
        voyage_provider = VoyageEmbeddingProvider()
        if voyage_provider.is_available():
            self._providers["voyage"] = voyage_provider
            logger.info("Voyage AI embedding provider available")

        # Local fallback (always available)
        self._providers["local"] = LocalEmbeddingProvider()

        # Select default provider
        self._select_default_provider()

    def _select_default_provider(self) -> None:
        """Select the best available provider as default."""
        config = get_config()

        # Check config preference
        preferred = config.rlm.semantic_search.get("embedding_provider", "auto")

        if preferred != "auto" and preferred in self._providers:
            self._current_provider = self._providers[preferred]
            logger.info(f"Using configured embedding provider: {preferred}")
            return

        # Auto-select: prefer OpenAI > Google > Mistral > Voyage > Local
        for provider_name in ["openai", "google", "mistral", "voyage", "local"]:
            if provider_name in self._providers:
                self._current_provider = self._providers[provider_name]
                logger.info(f"Auto-selected embedding provider: {provider_name}")
                return

    @property
    def provider(self) -> EmbeddingProvider:
        """Get the current embedding provider."""
        if self._current_provider is None:
            self._current_provider = self._providers.get("local", LocalEmbeddingProvider())
        return self._current_provider

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions for current provider."""
        return self.provider.dimensions

    def set_provider(self, name: str) -> bool:
        """
        Set the embedding provider by name.

        Args:
            name: Provider name ('openai', 'voyage', 'local')

        Returns:
            True if provider was set successfully
        """
        if name in self._providers:
            self._current_provider = self._providers[name]
            return True
        return False

    def list_providers(self) -> list[str]:
        """List available provider names."""
        return list(self._providers.keys())

    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        return await self.provider.embed(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: Texts to embed

        Returns:
            List of embedding vectors
        """
        return await self.provider.embed_batch(texts)

    async def embed_block(
        self,
        block_id: str,
        content: str,
        force: bool = False,
    ) -> Embedding:
        """
        Generate embedding for a context block.

        Args:
            block_id: Block identifier
            content: Block content to embed
            force: Force re-embedding even if cached

        Returns:
            Embedding object
        """
        content_hash = compute_content_hash(content)

        # Check cache
        if not force and block_id in self._cache:
            cached = self._cache[block_id]
            if cached.content_hash == content_hash:
                return cached

        # Generate embedding
        vector = await self.embed(content)

        embedding = Embedding(
            block_id=block_id,
            vector=vector,
            model=self.provider.model,
            dimensions=len(vector),
            content_hash=content_hash,
        )

        # Cache
        self._cache[block_id] = embedding

        return embedding

    async def embed_blocks(
        self,
        blocks: list[tuple[str, str]],  # (block_id, content)
        force: bool = False,
    ) -> list[Embedding]:
        """
        Generate embeddings for multiple context blocks.

        Args:
            blocks: List of (block_id, content) tuples
            force: Force re-embedding

        Returns:
            List of Embedding objects
        """
        if not blocks:
            return []

        # Check cache and filter
        to_embed: list[tuple[int, str, str, str]] = []  # (index, block_id, content, hash)
        results: list[Embedding | None] = [None] * len(blocks)

        for i, (block_id, content) in enumerate(blocks):
            content_hash = compute_content_hash(content)

            if not force and block_id in self._cache:
                cached = self._cache[block_id]
                if cached.content_hash == content_hash:
                    results[i] = cached
                    continue

            to_embed.append((i, block_id, content, content_hash))

        # Batch embed uncached blocks
        if to_embed:
            texts = [content for _, _, content, _ in to_embed]
            vectors = await self.embed_batch(texts)

            for j, (i, block_id, content, content_hash) in enumerate(to_embed):
                embedding = Embedding(
                    block_id=block_id,
                    vector=vectors[j],
                    model=self.provider.model,
                    dimensions=len(vectors[j]),
                    content_hash=content_hash,
                )
                self._cache[block_id] = embedding
                results[i] = embedding

        return [e for e in results if e is not None]

    def get_cached(self, block_id: str) -> Embedding | None:
        """Get cached embedding for a block."""
        return self._cache.get(block_id)

    def cache_embedding(self, embedding: Embedding) -> None:
        """Add embedding to cache."""
        self._cache[embedding.block_id] = embedding

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None


# Global manager instance
def get_embedding_manager() -> EmbeddingManager:
    """Get the global embedding manager."""
    return EmbeddingManager()


# Convenience functions


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding for text using the default provider."""
    return await get_embedding_manager().embed(text)


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts."""
    return await get_embedding_manager().embed_batch(texts)


def similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate similarity between two embeddings."""
    return cosine_similarity(vec1, vec2)
