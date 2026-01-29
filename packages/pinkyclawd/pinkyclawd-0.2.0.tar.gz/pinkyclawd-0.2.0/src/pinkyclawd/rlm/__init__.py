"""
Recursive Language Model (RLM) system for unlimited context.

Provides automatic context archival, retrieval, and management
to enable Claude to maintain coherent conversations beyond its
context window limits.

Features:
- Automatic context archival at configurable thresholds
- Pattern-based reference detection for auto-injection
- Semantic search using embeddings (OpenAI, Voyage, local)
- Hybrid search (keyword + semantic + recency) across archived context
- LLM-generated summaries for archived content
- Task-based archival on todo completion
- Session-end archival for context preservation
- RLM-Graph: Knowledge graph storage for structural context retrieval
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Type-only imports for static analysis
if TYPE_CHECKING:
    from pinkyclawd.rlm.context import ContextManager, TokenCounter
    from pinkyclawd.rlm.archive import ContextArchiver
    from pinkyclawd.rlm.search import ContextSearcher, SearchResult
    from pinkyclawd.rlm.retrieve import ContextRetriever, RetrievalContext
    from pinkyclawd.rlm.embedding import (
        Embedding,
        EmbeddingManager,
        EmbeddingProvider,
    )
    from pinkyclawd.rlm.handler import RLMHandler, RLMContext
    from pinkyclawd.rlm.auto_inject import AutoInjectResult
    from pinkyclawd.rlm.graph import (
        NodeType,
        RelationType,
        GraphNode,
        GraphEdge,
        EntityExtractor,
        ContentChunker,
        GraphIngester,
        GraphTraverser,
        GraphSearcher,
        GraphStorageAdapter,
    )
    from pinkyclawd.rlm.graph_json import JSONGraphStorage


# =============================================================================
# LAZY ACCESSOR FUNCTIONS
# =============================================================================

# Context management
def get_context_manager() -> "ContextManager":
    """Get the global context manager instance."""
    from pinkyclawd.core.state import get_state_factory
    return get_state_factory().context_manager


# Archival
def get_archiver() -> "ContextArchiver":
    """Get the global context archiver instance."""
    from pinkyclawd.core.state import get_state_factory
    return get_state_factory().archiver


def create_archive_block(*args, **kwargs):
    """Create an archive block."""
    from pinkyclawd.rlm.archive import create_archive_block as _create_archive_block
    return _create_archive_block(*args, **kwargs)


# Search
def get_searcher() -> "ContextSearcher":
    """Get the global context searcher instance."""
    from pinkyclawd.core.state import get_state_factory
    return get_state_factory().searcher


# Retrieval
def get_retriever() -> "ContextRetriever":
    """Get the global context retriever instance."""
    from pinkyclawd.core.state import get_state_factory
    return get_state_factory().retriever


# Embeddings
def get_embedding_manager() -> "EmbeddingManager":
    """Get the global embedding manager instance."""
    from pinkyclawd.core.state import get_state_factory
    return get_state_factory().embedding_manager


def generate_embedding(text: str):
    """Generate embedding for text."""
    from pinkyclawd.rlm.embedding import generate_embedding as _generate_embedding
    return _generate_embedding(text)


def generate_embeddings(texts: list[str]):
    """Generate embeddings for multiple texts."""
    from pinkyclawd.rlm.embedding import generate_embeddings as _generate_embeddings
    return _generate_embeddings(texts)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    from pinkyclawd.rlm.embedding import cosine_similarity as _cosine_similarity
    return _cosine_similarity(a, b)


# Handler
def get_rlm_handler() -> "RLMHandler":
    """Get the global RLM handler instance."""
    from pinkyclawd.core.state import get_state_factory
    return get_state_factory().rlm_handler


def prepare_messages_with_rlm(*args, **kwargs):
    """Prepare messages with RLM context injection."""
    from pinkyclawd.rlm.handler import prepare_messages_with_rlm as _prepare
    return _prepare(*args, **kwargs)


def update_after_response(*args, **kwargs):
    """Update RLM state after receiving a response."""
    from pinkyclawd.rlm.handler import update_after_response as _update
    return _update(*args, **kwargs)


def detect_task_completion(*args, **kwargs):
    """Detect task completion patterns in messages."""
    from pinkyclawd.rlm.handler import detect_task_completion as _detect
    return _detect(*args, **kwargs)


# Display
def configure_display(*args, **kwargs):
    """Configure display settings."""
    from pinkyclawd.rlm.display import configure_display as _configure
    return _configure(*args, **kwargs)


def display_retrieval_start(*args, **kwargs):
    """Display retrieval start indicator."""
    from pinkyclawd.rlm.display import display_retrieval_start as _display
    return _display(*args, **kwargs)


def display_retrieval_result(*args, **kwargs):
    """Display retrieval result."""
    from pinkyclawd.rlm.display import display_retrieval_result as _display
    return _display(*args, **kwargs)


def display_injection(*args, **kwargs):
    """Display context injection."""
    from pinkyclawd.rlm.display import display_injection as _display
    return _display(*args, **kwargs)


def display_archival_start(*args, **kwargs):
    """Display archival start indicator."""
    from pinkyclawd.rlm.display import display_archival_start as _display
    return _display(*args, **kwargs)


def display_archival_complete(*args, **kwargs):
    """Display archival completion."""
    from pinkyclawd.rlm.display import display_archival_complete as _display
    return _display(*args, **kwargs)


def display_context_status(*args, **kwargs):
    """Display context status."""
    from pinkyclawd.rlm.display import display_context_status as _display
    return _display(*args, **kwargs)


def register_event_handlers(*args, **kwargs):
    """Register RLM event handlers."""
    from pinkyclawd.rlm.display import register_event_handlers as _register
    return _register(*args, **kwargs)


# Auto-injection
def detects_reference(*args, **kwargs):
    """Detect references in text."""
    from pinkyclawd.rlm.auto_inject import detects_reference as _detect
    return _detect(*args, **kwargs)


def extract_keywords(*args, **kwargs):
    """Extract keywords from text."""
    from pinkyclawd.rlm.auto_inject import extract_keywords as _extract
    return _extract(*args, **kwargs)


def analyze(*args, **kwargs):
    """Analyze text for auto-injection."""
    from pinkyclawd.rlm.auto_inject import analyze as _analyze
    return _analyze(*args, **kwargs)


def analyze_with_threshold(*args, **kwargs):
    """Analyze text with custom threshold."""
    from pinkyclawd.rlm.auto_inject import analyze_with_threshold as _analyze
    return _analyze(*args, **kwargs)


def should_auto_inject(*args, **kwargs):
    """Check if auto-injection should be triggered."""
    from pinkyclawd.rlm.auto_inject import should_auto_inject as _should
    return _should(*args, **kwargs)


def format_for_injection(*args, **kwargs):
    """Format context for injection."""
    from pinkyclawd.rlm.auto_inject import format_for_injection as _format
    return _format(*args, **kwargs)


# Summarization
def generate_summary(*args, **kwargs):
    """Generate summary for archived content."""
    from pinkyclawd.rlm.summarize import generate_summary as _generate
    return _generate(*args, **kwargs)


def generate_task_summary(*args, **kwargs):
    """Generate task summary."""
    from pinkyclawd.rlm.summarize import generate_task_summary as _generate
    return _generate(*args, **kwargs)


# Graph (RLM-Graph)
def get_graph_ingester() -> "GraphIngester":
    """Get the global graph ingester instance."""
    from pinkyclawd.core.state import get_state_factory
    return get_state_factory().graph_ingester


def get_graph_traverser() -> "GraphTraverser":
    """Get the global graph traverser instance."""
    from pinkyclawd.core.state import get_state_factory
    return get_state_factory().graph_traverser


def get_graph_searcher() -> "GraphSearcher":
    """Get the global graph searcher instance."""
    from pinkyclawd.core.state import get_state_factory
    return get_state_factory().graph_searcher


def get_graph_storage(*args, **kwargs):
    """Get graph storage adapter."""
    from pinkyclawd.rlm.graph import get_graph_storage as _get
    return _get(*args, **kwargs)


# JSON Graph Storage
def get_json_graph_storage(*args, **kwargs):
    """Get JSON graph storage for a session."""
    from pinkyclawd.rlm.graph_json import get_json_graph_storage as _get
    return _get(*args, **kwargs)


def clear_storage_cache():
    """Clear the JSON graph storage cache."""
    from pinkyclawd.rlm.graph_json import clear_storage_cache as _clear
    return _clear()


# =============================================================================
# CLASS IMPORTS (Lazy via __getattr__)
# =============================================================================

# Classes that need to be importable from the module
_CLASS_MAPPING = {
    # Context
    "ContextManager": "pinkyclawd.rlm.context",
    "TokenCounter": "pinkyclawd.rlm.context",
    # Archive
    "ContextArchiver": "pinkyclawd.rlm.archive",
    # Search
    "ContextSearcher": "pinkyclawd.rlm.search",
    "SearchResult": "pinkyclawd.rlm.search",
    # Retrieve
    "ContextRetriever": "pinkyclawd.rlm.retrieve",
    "RetrievalContext": "pinkyclawd.rlm.retrieve",
    # Embedding
    "Embedding": "pinkyclawd.rlm.embedding",
    "EmbeddingManager": "pinkyclawd.rlm.embedding",
    "EmbeddingProvider": "pinkyclawd.rlm.embedding",
    # Handler
    "RLMHandler": "pinkyclawd.rlm.handler",
    "RLMContext": "pinkyclawd.rlm.handler",
    # Auto-inject
    "AutoInjectResult": "pinkyclawd.rlm.auto_inject",
    # Graph
    "NodeType": "pinkyclawd.rlm.graph",
    "RelationType": "pinkyclawd.rlm.graph",
    "GraphNode": "pinkyclawd.rlm.graph",
    "GraphEdge": "pinkyclawd.rlm.graph",
    "EntityExtractor": "pinkyclawd.rlm.extraction",
    "ContentChunker": "pinkyclawd.rlm.extraction",
    "GraphIngester": "pinkyclawd.rlm.ingestion",
    "GraphTraverser": "pinkyclawd.rlm.traversal",
    "GraphSearcher": "pinkyclawd.rlm.traversal",
    "GraphStorageAdapter": "pinkyclawd.rlm.graph",
    # JSON Storage
    "JSONGraphStorage": "pinkyclawd.rlm.graph_json",
}


def __getattr__(name: str):
    """Lazy import for classes."""
    if name in _CLASS_MAPPING:
        import importlib
        module = importlib.import_module(_CLASS_MAPPING[name])
        return getattr(module, name)
    raise AttributeError(f"module 'pinkyclawd.rlm' has no attribute {name!r}")


__all__ = [
    # Context management
    "ContextManager",
    "TokenCounter",
    "get_context_manager",
    # Archival
    "ContextArchiver",
    "create_archive_block",
    "get_archiver",
    # Search
    "ContextSearcher",
    "SearchResult",
    "get_searcher",
    # Retrieval
    "ContextRetriever",
    "RetrievalContext",
    "get_retriever",
    # Embeddings (for semantic search)
    "Embedding",
    "EmbeddingManager",
    "EmbeddingProvider",
    "get_embedding_manager",
    "generate_embedding",
    "generate_embeddings",
    "cosine_similarity",
    # Handler (main integration point)
    "RLMHandler",
    "RLMContext",
    "get_rlm_handler",
    "prepare_messages_with_rlm",
    "update_after_response",
    "detect_task_completion",
    # Display
    "configure_display",
    "display_retrieval_start",
    "display_retrieval_result",
    "display_injection",
    "display_archival_start",
    "display_archival_complete",
    "display_context_status",
    "register_event_handlers",
    # Auto-injection
    "AutoInjectResult",
    "detects_reference",
    "extract_keywords",
    "analyze",
    "analyze_with_threshold",
    "should_auto_inject",
    "format_for_injection",
    # Summarization
    "generate_summary",
    "generate_task_summary",
    # Graph (RLM-Graph knowledge graph)
    "NodeType",
    "RelationType",
    "GraphNode",
    "GraphEdge",
    "EntityExtractor",
    "ContentChunker",
    "GraphIngester",
    "GraphTraverser",
    "GraphSearcher",
    "GraphStorageAdapter",
    "get_graph_ingester",
    "get_graph_traverser",
    "get_graph_searcher",
    "get_graph_storage",
    # JSON Storage (file-based graph storage)
    "JSONGraphStorage",
    "get_json_graph_storage",
    "clear_storage_cache",
]
