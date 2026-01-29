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

from pinkyclawd.rlm.context import ContextManager, TokenCounter, get_context_manager
from pinkyclawd.rlm.archive import ContextArchiver, create_archive_block, get_archiver
from pinkyclawd.rlm.search import ContextSearcher, SearchResult, get_searcher
from pinkyclawd.rlm.retrieve import ContextRetriever, RetrievalContext, get_retriever
from pinkyclawd.rlm.embedding import (
    Embedding,
    EmbeddingManager,
    EmbeddingProvider,
    get_embedding_manager,
    generate_embedding,
    generate_embeddings,
    cosine_similarity,
)
from pinkyclawd.rlm.handler import (
    RLMHandler,
    RLMContext,
    get_rlm_handler,
    prepare_messages_with_rlm,
    update_after_response,
    detect_task_completion,
)
from pinkyclawd.rlm.display import (
    configure_display,
    display_retrieval_start,
    display_retrieval_result,
    display_injection,
    display_archival_start,
    display_archival_complete,
    display_context_status,
    register_event_handlers,
)
from pinkyclawd.rlm.auto_inject import (
    AutoInjectResult,
    detects_reference,
    extract_keywords,
    analyze,
    analyze_with_threshold,
    should_auto_inject,
    format_for_injection,
)
from pinkyclawd.rlm.summarize import (
    generate_summary,
    generate_task_summary,
)
from pinkyclawd.rlm.graph import (
    # Types
    NodeType,
    RelationType,
    GraphNode,
    GraphEdge,
    # Components
    EntityExtractor,
    ContentChunker,
    GraphIngester,
    GraphTraverser,
    GraphSearcher,
    GraphStorageAdapter,
    # Accessors
    get_graph_ingester,
    get_graph_traverser,
    get_graph_searcher,
    get_graph_storage,
)
from pinkyclawd.rlm.graph_json import (
    JSONGraphStorage,
    get_json_graph_storage,
    clear_storage_cache,
)

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
