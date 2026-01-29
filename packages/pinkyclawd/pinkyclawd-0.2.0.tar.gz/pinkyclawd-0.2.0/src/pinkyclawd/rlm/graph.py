"""
RLM-Graph: Knowledge graph-based context storage and retrieval.

Extends the RLM system with graph-structured storage where:
- Nodes represent documents, sections, chunks, and entities
- Edges capture relationships (has_section, has_chunk, mentions, related_to)
- Graph traversal enables finding structurally related context

This module contains shared types and the storage adapter.
For specific functionality, see:
- extraction.py: EntityExtractor, ContentChunker
- ingestion.py: GraphIngester
- traversal.py: GraphTraverser, GraphSearcher
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pinkyclawd.config.storage import get_storage

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class NodeType(str, Enum):
    """Types of nodes in the knowledge graph."""

    DOCUMENT = "document"  # Top-level document/conversation
    SECTION = "section"  # Major section or topic
    CHUNK = "chunk"  # Smaller retrievable unit
    ENTITY = "entity"  # Extracted entity (person, concept, code element)


class RelationType(str, Enum):
    """Types of relationships between nodes."""

    HAS_SECTION = "has_section"  # Document -> Section
    HAS_CHUNK = "has_chunk"  # Section -> Chunk, or Document -> Chunk
    MENTIONS = "mentions"  # Chunk -> Entity
    RELATED_TO = "related_to"  # Entity -> Entity, or Chunk -> Chunk
    FOLLOWS = "follows"  # Temporal ordering between chunks
    PARENT_OF = "parent_of"  # Hierarchical relationship


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class GraphNode:
    """A node in the knowledge graph."""

    id: str
    session_id: str
    type: NodeType
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphNode:
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            type=NodeType(data["type"]),
            content=data["content"],
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding"),
            created_at=datetime.fromisoformat(data["created_at"])
            if isinstance(data["created_at"], str)
            else data["created_at"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class GraphEdge:
    """An edge connecting two nodes."""

    source_id: str
    target_id: str
    relationship: RelationType
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship": self.relationship.value,
            "weight": self.weight,
            "metadata": self.metadata,
        }


# =============================================================================
# STORAGE ADAPTER
# =============================================================================

class GraphStorageAdapter:
    """
    Adapter that provides a unified interface for graph storage operations.

    Supports both JSON-based and SQLite storage backends with the same interface.
    Uses the method names expected by GraphIngester/Traverser/Searcher.
    """

    def __init__(self, session_id: str | None = None) -> None:
        """
        Initialize the storage adapter.

        Args:
            session_id: Session ID for JSON storage (required for JSON backend)
        """
        self._session_id = session_id
        self._storage_type: str | None = None
        self._json_storage: Any = None
        self._sqlite_storage: Any = None

    def _get_storage_type(self) -> str:
        """Get the configured storage type."""
        if self._storage_type is None:
            try:
                from pinkyclawd.config.settings import get_config
                config = get_config()
                self._storage_type = config.rlm.graph_storage
            except Exception:
                self._storage_type = "json"  # Default to JSON
        return self._storage_type

    def _get_json_storage(self, session_id: str):
        """Get or create JSON storage for a session."""
        from pinkyclawd.rlm.graph_json import get_json_graph_storage
        return get_json_graph_storage(session_id)

    def _get_sqlite_storage(self):
        """Get the SQLite storage instance."""
        if self._sqlite_storage is None:
            self._sqlite_storage = get_storage()
        return self._sqlite_storage

    def add_graph_node(
        self,
        node_id: str,
        session_id: str,
        node_type: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        embedding: list[float] | None = None,
    ) -> None:
        """Add a node to the knowledge graph."""
        if self._get_storage_type() == "json":
            storage = self._get_json_storage(session_id)
            storage.add_node(node_id, session_id, node_type, content, metadata, embedding)
        else:
            self._get_sqlite_storage().add_graph_node(
                node_id, session_id, node_type, content, metadata, embedding
            )

    def get_graph_node(self, node_id: str) -> dict[str, Any] | None:
        """Get a node from the knowledge graph."""
        if self._get_storage_type() == "json":
            if self._session_id:
                storage = self._get_json_storage(self._session_id)
                return storage.get_node(node_id)
            return None
        else:
            return self._get_sqlite_storage().get_graph_node(node_id)

    def get_graph_nodes(
        self,
        session_id: str | None = None,
        node_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get nodes from the knowledge graph with optional filters."""
        if self._get_storage_type() == "json":
            if session_id:
                storage = self._get_json_storage(session_id)
                return storage.get_nodes(session_id, node_type, limit)
            elif self._session_id:
                storage = self._get_json_storage(self._session_id)
                return storage.get_nodes(self._session_id, node_type, limit)
            return []
        else:
            return self._get_sqlite_storage().get_graph_nodes(session_id, node_type, limit)

    def search_graph_nodes(
        self,
        query: str,
        session_id: str | None = None,
        node_type: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search nodes by content."""
        if self._get_storage_type() == "json":
            sid = session_id or self._session_id
            if sid:
                storage = self._get_json_storage(sid)
                return storage.search_nodes(query, session_id, node_type, limit)
            return []
        else:
            return self._get_sqlite_storage().search_graph_nodes(
                query, session_id, node_type, limit
            )

    def delete_graph_node(self, node_id: str) -> bool:
        """Delete a node and its edges."""
        if self._get_storage_type() == "json":
            if self._session_id:
                storage = self._get_json_storage(self._session_id)
                return storage.delete_node(node_id)
            return False
        else:
            return self._get_sqlite_storage().delete_graph_node(node_id)

    def add_graph_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add an edge to the knowledge graph."""
        if self._get_storage_type() == "json":
            if self._session_id:
                storage = self._get_json_storage(self._session_id)
                storage.add_edge(source_id, target_id, relationship, weight, metadata)
        else:
            self._get_sqlite_storage().add_graph_edge(
                source_id, target_id, relationship, weight, metadata
            )

    def get_graph_edges(
        self,
        node_id: str,
        direction: Literal["outgoing", "incoming", "both"] = "outgoing",
        relationship: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get edges for a node."""
        if self._get_storage_type() == "json":
            if self._session_id:
                storage = self._get_json_storage(self._session_id)
                return storage.get_edges(node_id, direction, relationship)
            return []
        else:
            return self._get_sqlite_storage().get_graph_edges(
                node_id, direction, relationship
            )

    def get_neighbors(
        self,
        node_id: str,
        relationship: str | None = None,
        direction: Literal["outgoing", "incoming", "both"] = "outgoing",
        node_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get neighboring nodes."""
        if self._get_storage_type() == "json":
            if self._session_id:
                storage = self._get_json_storage(self._session_id)
                return storage.get_neighbors(node_id, relationship, direction, node_type)
            return []
        else:
            return self._get_sqlite_storage().get_graph_neighbors(
                node_id, relationship, direction, node_type
            )

    def delete_graph_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
    ) -> bool:
        """Delete an edge from the knowledge graph."""
        if self._get_storage_type() == "json":
            if self._session_id:
                storage = self._get_json_storage(self._session_id)
                return storage.delete_edge(source_id, target_id, relationship)
            return False
        else:
            return self._get_sqlite_storage().delete_graph_edge(
                source_id, target_id, relationship
            )

    def clear_session_graph(self, session_id: str) -> None:
        """Clear all graph data for a session."""
        if self._get_storage_type() == "json":
            storage = self._get_json_storage(session_id)
            storage.clear_session()
        else:
            self._get_sqlite_storage().clear_session_graph(session_id)

    def close(self) -> None:
        """Close any open resources."""
        # JSON storage doesn't need explicit closing
        pass


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

# Global storage adapter instance cache
_storage_adapters: dict[str, GraphStorageAdapter] = {}


def get_graph_storage(session_id: str | None = None) -> GraphStorageAdapter:
    """
    Get a graph storage adapter for the given session.

    Args:
        session_id: Session ID (required for JSON storage)

    Returns:
        GraphStorageAdapter instance
    """
    global _storage_adapters

    key = session_id or "_default"
    if key not in _storage_adapters:
        _storage_adapters[key] = GraphStorageAdapter(session_id)
    return _storage_adapters[key]


# =============================================================================
# RE-EXPORTS FOR BACKWARD COMPATIBILITY
# =============================================================================

# Import and re-export from new modules for backward compatibility
from pinkyclawd.rlm.extraction import EntityExtractor, ContentChunker
from pinkyclawd.rlm.ingestion import GraphIngester, get_graph_ingester
from pinkyclawd.rlm.traversal import (
    GraphTraverser,
    GraphSearcher,
    get_graph_traverser,
    get_graph_searcher,
)

__all__ = [
    # Types
    "NodeType",
    "RelationType",
    "GraphNode",
    "GraphEdge",
    # Storage
    "GraphStorageAdapter",
    "get_graph_storage",
    # Extraction
    "EntityExtractor",
    "ContentChunker",
    # Ingestion
    "GraphIngester",
    "get_graph_ingester",
    # Traversal
    "GraphTraverser",
    "GraphSearcher",
    "get_graph_traverser",
    "get_graph_searcher",
]
