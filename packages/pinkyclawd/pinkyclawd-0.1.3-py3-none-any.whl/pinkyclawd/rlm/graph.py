"""
RLM-Graph: Knowledge graph-based context storage and retrieval.

Extends the RLM system with graph-structured storage where:
- Nodes represent documents, sections, chunks, and entities
- Edges capture relationships (has_section, has_chunk, mentions, related_to)
- Graph traversal enables finding structurally related context
"""

from __future__ import annotations

import hashlib
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pinkyclawd.config.storage import ContextBlock, Message, PartType, get_storage

logger = logging.getLogger(__name__)


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
            # Need to search across all sessions for JSON storage
            # This is less efficient but maintains compatibility
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
        direction: Literal["outgoing", "incoming", "both"] = "both",
        relationship: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get edges connected to a node."""
        if self._get_storage_type() == "json":
            if self._session_id:
                storage = self._get_json_storage(self._session_id)
                return storage.get_edges(node_id, direction, relationship)
            return []
        else:
            return self._get_sqlite_storage().get_graph_edges(node_id, direction, relationship)

    def get_neighbors(
        self,
        node_id: str,
        relationship: str | None = None,
        direction: Literal["outgoing", "incoming", "both"] = "outgoing",
        node_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get neighboring nodes connected by edges."""
        if self._get_storage_type() == "json":
            if self._session_id:
                storage = self._get_json_storage(self._session_id)
                return storage.get_neighbors(node_id, relationship, direction, node_type)
            return []
        else:
            return self._get_sqlite_storage().get_neighbors(
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


class EntityExtractor:
    """
    Extracts entities from text content.

    Identifies:
    - Capitalized terms (potential proper nouns)
    - Code elements (function names, classes, variables)
    - Markdown links and references
    - Frequent keywords
    """

    # Common words to ignore
    STOPWORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "as", "into", "through",
        "during", "before", "after", "above", "below", "between", "this",
        "that", "these", "those", "then", "than", "when", "where", "which",
        "who", "what", "how", "why", "all", "any", "both", "each", "few",
        "more", "most", "other", "some", "such", "no", "not", "only", "same",
        "so", "than", "too", "very", "just", "also", "now", "here", "there",
        "user", "assistant", "tool", "result", "error", "success",
    }

    # Code-related patterns
    CODE_PATTERNS = [
        r"\b([A-Z][a-zA-Z0-9]*(?:Error|Exception|Handler|Manager|Service|Controller|Factory|Builder))\b",  # Classes
        r"\b(def\s+)?([a-z_][a-z0-9_]*)\s*\(",  # Functions
        r"\b([A-Z_][A-Z0-9_]{2,})\b",  # Constants
        r"`([^`]+)`",  # Inline code
        r"(?:class|interface|type|struct)\s+([A-Z][a-zA-Z0-9]*)",  # Type definitions
    ]

    def __init__(self) -> None:
        self._compiled_patterns = [re.compile(p) for p in self.CODE_PATTERNS]

    def extract(self, text: str) -> list[tuple[str, str]]:
        """
        Extract entities from text.

        Returns:
            List of (entity_name, entity_type) tuples
        """
        entities: dict[str, str] = {}

        # Extract capitalized terms (potential proper nouns)
        capitalized = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", text)
        for term in capitalized:
            if term.lower() not in self.STOPWORDS and len(term) > 2:
                entities[term] = "proper_noun"

        # Extract code elements
        for pattern in self._compiled_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    # Take the last non-empty group
                    term = next((m for m in reversed(match) if m), None)
                else:
                    term = match

                if term and term.lower() not in self.STOPWORDS and len(term) > 1:
                    entities[term] = "code_element"

        # Extract markdown links
        links = re.findall(r"\[([^\]]+)\]\([^)]+\)", text)
        for link_text in links:
            if link_text.lower() not in self.STOPWORDS:
                entities[link_text] = "reference"

        # Extract file paths
        paths = re.findall(r"(?:^|\s)([./]?(?:[a-zA-Z0-9_-]+/)+[a-zA-Z0-9_.-]+)", text)
        for path in paths:
            entities[path] = "file_path"

        return list(entities.items())

    def extract_keywords(self, text: str, top_n: int = 10) -> list[str]:
        """Extract top keywords based on frequency."""
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        word_counts: dict[str, int] = {}

        for word in words:
            if word not in self.STOPWORDS:
                word_counts[word] = word_counts.get(word, 0) + 1

        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:top_n]]


class ContentChunker:
    """
    Splits content into hierarchical chunks.

    Creates sections based on natural breaks and chunks
    suitable for retrieval.
    """

    def __init__(
        self,
        section_min_chars: int = 500,
        chunk_target_chars: int = 300,
        chunk_overlap: int = 50,
    ) -> None:
        self.section_min_chars = section_min_chars
        self.chunk_target_chars = chunk_target_chars
        self.chunk_overlap = chunk_overlap

    def split_into_sections(self, content: str) -> list[tuple[str, str]]:
        """
        Split content into sections.

        Returns:
            List of (section_title, section_content) tuples
        """
        sections: list[tuple[str, str]] = []

        # Try to split by markdown headers
        header_pattern = r"(?:^|\n)(#{1,3})\s+(.+?)(?:\n|$)"
        matches = list(re.finditer(header_pattern, content))

        if matches:
            for i, match in enumerate(matches):
                title = match.group(2).strip()
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
                section_content = content[start:end].strip()

                if section_content:
                    sections.append((title, section_content))
        else:
            # Fall back to paragraph-based splitting
            paragraphs = content.split("\n\n")
            current_section = []
            current_length = 0

            for para in paragraphs:
                current_section.append(para)
                current_length += len(para)

                if current_length >= self.section_min_chars:
                    section_text = "\n\n".join(current_section)
                    # Generate title from first line
                    first_line = section_text.split("\n")[0][:50]
                    sections.append((first_line, section_text))
                    current_section = []
                    current_length = 0

            if current_section:
                section_text = "\n\n".join(current_section)
                first_line = section_text.split("\n")[0][:50]
                sections.append((first_line, section_text))

        return sections

    def split_into_chunks(self, content: str) -> list[str]:
        """
        Split content into overlapping chunks.

        Returns:
            List of chunk texts
        """
        if len(content) <= self.chunk_target_chars:
            return [content]

        chunks: list[str] = []
        sentences = re.split(r"(?<=[.!?])\s+", content)
        current_chunk: list[str] = []
        current_length = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            if current_length + sentence_len > self.chunk_target_chars and current_chunk:
                chunks.append(" ".join(current_chunk))

                # Keep overlap
                overlap_chunk: list[str] = []
                overlap_len = 0
                for s in reversed(current_chunk):
                    if overlap_len + len(s) <= self.chunk_overlap:
                        overlap_chunk.insert(0, s)
                        overlap_len += len(s)
                    else:
                        break

                current_chunk = overlap_chunk
                current_length = overlap_len

            current_chunk.append(sentence)
            current_length += sentence_len

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks


class GraphIngester:
    """
    Ingests content into the knowledge graph.

    Converts documents into a hierarchical graph structure:
    Document -> Sections -> Chunks -> Entities
    """

    def __init__(self, session_id: str | None = None) -> None:
        self._session_id = session_id
        self._storage = get_graph_storage(session_id)
        self._chunker = ContentChunker()
        self._extractor = EntityExtractor()
        self._embedding_manager = None

    def set_session_id(self, session_id: str) -> None:
        """Set the session ID and update storage."""
        self._session_id = session_id
        self._storage = get_graph_storage(session_id)

    def _get_embedding_manager(self):
        """Lazy load embedding manager."""
        if self._embedding_manager is None:
            try:
                from pinkyclawd.rlm.embedding import get_embedding_manager
                self._embedding_manager = get_embedding_manager()
            except ImportError:
                logger.warning("Embedding module not available")
        return self._embedding_manager

    def _generate_node_id(self, node_type: str, content: str) -> str:
        """Generate a unique node ID based on content hash."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{node_type}_{uuid.uuid4().hex[:8]}_{content_hash}"

    def ingest_context_block(
        self,
        block: ContextBlock,
        generate_embeddings: bool = True,
    ) -> GraphNode:
        """
        Ingest a context block into the graph.

        Creates a document node and recursively creates
        sections, chunks, and entities.

        Returns:
            The root document node
        """
        # Ensure storage is set for this session
        if self._session_id != block.session_id:
            self.set_session_id(block.session_id)

        # Create document node
        doc_node = GraphNode(
            id=self._generate_node_id("doc", block.id),
            session_id=block.session_id,
            type=NodeType.DOCUMENT,
            content=block.summary or block.content[:200],
            metadata={
                "block_id": block.id,
                "task_id": block.task_id,
                "task_description": block.task_description,
                "tokens": block.tokens,
            },
        )

        self._storage.add_graph_node(
            node_id=doc_node.id,
            session_id=doc_node.session_id,
            node_type=doc_node.type.value,
            content=doc_node.content,
            metadata=doc_node.metadata,
        )

        # Split into sections
        sections = self._chunker.split_into_sections(block.content)

        for section_title, section_content in sections:
            section_node = self._ingest_section(
                doc_node.id,
                block.session_id,
                section_title,
                section_content,
                generate_embeddings,
            )

            # Link document -> section
            self._storage.add_graph_edge(
                source_id=doc_node.id,
                target_id=section_node.id,
                relationship=RelationType.HAS_SECTION.value,
            )

        logger.info(f"Ingested context block {block.id} as graph node {doc_node.id}")
        return doc_node

    def _ingest_section(
        self,
        parent_id: str,
        session_id: str,
        title: str,
        content: str,
        generate_embeddings: bool,
    ) -> GraphNode:
        """Ingest a section and its chunks."""
        section_node = GraphNode(
            id=self._generate_node_id("sec", content),
            session_id=session_id,
            type=NodeType.SECTION,
            content=title,
            metadata={"full_content": content[:500]},
        )

        self._storage.add_graph_node(
            node_id=section_node.id,
            session_id=session_id,
            node_type=section_node.type.value,
            content=section_node.content,
            metadata=section_node.metadata,
        )

        # Split into chunks
        chunks = self._chunker.split_into_chunks(content)
        prev_chunk_id: str | None = None

        for chunk_content in chunks:
            chunk_node = self._ingest_chunk(
                section_node.id,
                session_id,
                chunk_content,
                generate_embeddings,
            )

            # Link section -> chunk
            self._storage.add_graph_edge(
                source_id=section_node.id,
                target_id=chunk_node.id,
                relationship=RelationType.HAS_CHUNK.value,
            )

            # Link previous chunk -> current chunk (temporal order)
            if prev_chunk_id:
                self._storage.add_graph_edge(
                    source_id=prev_chunk_id,
                    target_id=chunk_node.id,
                    relationship=RelationType.FOLLOWS.value,
                )

            prev_chunk_id = chunk_node.id

        return section_node

    def _ingest_chunk(
        self,
        parent_id: str,
        session_id: str,
        content: str,
        generate_embeddings: bool,
    ) -> GraphNode:
        """Ingest a chunk and extract entities."""
        # Generate embedding if enabled
        embedding = None
        if generate_embeddings:
            embedding_manager = self._get_embedding_manager()
            if embedding_manager:
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Schedule for later
                        pass
                    else:
                        embedding = loop.run_until_complete(
                            embedding_manager.embed(content)
                        )
                except Exception as e:
                    logger.debug(f"Failed to generate embedding: {e}")

        chunk_node = GraphNode(
            id=self._generate_node_id("chunk", content),
            session_id=session_id,
            type=NodeType.CHUNK,
            content=content,
            embedding=embedding,
        )

        self._storage.add_graph_node(
            node_id=chunk_node.id,
            session_id=session_id,
            node_type=chunk_node.type.value,
            content=chunk_node.content,
            metadata=chunk_node.metadata,
            embedding=embedding,
        )

        # Extract and link entities
        entities = self._extractor.extract(content)
        entity_cache: dict[str, str] = {}  # entity_name -> entity_id

        for entity_name, entity_type in entities:
            # Check if entity already exists
            if entity_name in entity_cache:
                entity_id = entity_cache[entity_name]
            else:
                # Create or reuse entity node
                entity_id = self._get_or_create_entity(
                    session_id, entity_name, entity_type
                )
                entity_cache[entity_name] = entity_id

            # Link chunk -> entity
            self._storage.add_graph_edge(
                source_id=chunk_node.id,
                target_id=entity_id,
                relationship=RelationType.MENTIONS.value,
            )

        return chunk_node

    def _get_or_create_entity(
        self,
        session_id: str,
        name: str,
        entity_type: str,
    ) -> str:
        """Get existing entity or create new one."""
        # Search for existing entity with same name in session
        existing = self._storage.search_graph_nodes(
            query=name,
            session_id=session_id,
            node_type=NodeType.ENTITY.value,
            limit=1,
        )

        if existing and existing[0]["content"] == name:
            return existing[0]["id"]

        # Create new entity
        entity_id = self._generate_node_id("ent", name)
        self._storage.add_graph_node(
            node_id=entity_id,
            session_id=session_id,
            node_type=NodeType.ENTITY.value,
            content=name,
            metadata={"entity_type": entity_type},
        )

        return entity_id

    def ingest_messages(
        self,
        session_id: str,
        messages: list[Message],
        generate_embeddings: bool = True,
    ) -> GraphNode | None:
        """
        Ingest messages directly into the graph.

        Creates a document node from the messages.
        """
        if not messages:
            return None

        # Ensure storage is set for this session
        if self._session_id != session_id:
            self.set_session_id(session_id)

        # Build content from messages
        content_parts = []
        for msg in messages:
            role = msg.role.value.upper()
            text_parts = []

            for part in msg.parts:
                if part.type == PartType.TEXT:
                    text_parts.append(part.content.get("text", ""))
                elif part.type == PartType.TOOL_USE:
                    tool_name = part.content.get("name", "unknown")
                    text_parts.append(f"[Tool: {tool_name}]")
                elif part.type == PartType.TOOL_RESULT:
                    result = part.content.get("result", "")
                    if len(result) > 300:
                        result = result[:300] + "..."
                    text_parts.append(f"[Result: {result}]")

            if text_parts:
                content_parts.append(f"{role}: {' '.join(text_parts)}")

        content = "\n\n".join(content_parts)

        # Create a temporary context block
        block = ContextBlock(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            summary=content[:200],
            content=content,
            tokens=len(content.split()),  # Rough estimate
        )

        return self.ingest_context_block(block, generate_embeddings)


class GraphTraverser:
    """
    Traverses the knowledge graph to find related context.

    Implements various traversal strategies:
    - Breadth-first exploration
    - Semantic similarity expansion
    - Entity-based linking
    """

    def __init__(self, session_id: str | None = None) -> None:
        self._session_id = session_id
        self._storage = get_graph_storage(session_id)

    def set_session_id(self, session_id: str) -> None:
        """Set the session ID and update storage."""
        self._session_id = session_id
        self._storage = get_graph_storage(session_id)

    def get_neighbors(
        self,
        node_id: str,
        relationship: RelationType | str | None = None,
        direction: Literal["outgoing", "incoming", "both"] = "outgoing",
        node_type: NodeType | str | None = None,
    ) -> list[GraphNode]:
        """Get neighboring nodes."""
        rel_str = relationship.value if isinstance(relationship, RelationType) else relationship
        type_str = node_type.value if isinstance(node_type, NodeType) else node_type

        neighbors = self._storage.get_neighbors(
            node_id=node_id,
            relationship=rel_str,
            direction=direction,
            node_type=type_str,
        )

        return [GraphNode.from_dict(n) for n in neighbors]

    def expand_context(
        self,
        node_ids: list[str],
        max_depth: int = 2,
        max_nodes: int = 20,
    ) -> list[GraphNode]:
        """
        Expand context by traversing from given nodes.

        Uses breadth-first search to find related nodes.
        """
        visited: set[str] = set()
        result: list[GraphNode] = []
        queue: list[tuple[str, int]] = [(nid, 0) for nid in node_ids]

        while queue and len(result) < max_nodes:
            node_id, depth = queue.pop(0)

            if node_id in visited:
                continue

            visited.add(node_id)

            node_data = self._storage.get_graph_node(node_id)
            if node_data:
                result.append(GraphNode.from_dict(node_data))

            if depth < max_depth:
                # Get neighbors
                edges = self._storage.get_graph_edges(node_id, "both")
                for edge in edges:
                    neighbor_id = (
                        edge["target_id"]
                        if edge["source_id"] == node_id
                        else edge["source_id"]
                    )
                    if neighbor_id not in visited:
                        queue.append((neighbor_id, depth + 1))

        return result

    def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5,
    ) -> list[GraphNode] | None:
        """
        Find a path between two nodes.

        Returns the path as a list of nodes, or None if no path exists.
        """
        visited: set[str] = set()
        queue: list[tuple[str, list[str]]] = [(start_id, [start_id])]

        while queue:
            current_id, path = queue.pop(0)

            if current_id == end_id:
                # Build node list from path
                nodes = []
                for node_id in path:
                    node_data = self._storage.get_graph_node(node_id)
                    if node_data:
                        nodes.append(GraphNode.from_dict(node_data))
                return nodes

            if len(path) >= max_depth:
                continue

            visited.add(current_id)

            edges = self._storage.get_graph_edges(current_id, "both")
            for edge in edges:
                neighbor_id = (
                    edge["target_id"]
                    if edge["source_id"] == current_id
                    else edge["source_id"]
                )
                if neighbor_id not in visited:
                    queue.append((neighbor_id, path + [neighbor_id]))

        return None

    def get_entity_context(
        self,
        entity_name: str,
        session_id: str | None = None,
        max_chunks: int = 10,
    ) -> list[GraphNode]:
        """
        Get all chunks that mention a specific entity.
        """
        # Update session if specified
        if session_id and session_id != self._session_id:
            self.set_session_id(session_id)

        # Find entity nodes matching the name
        entities = self._storage.search_graph_nodes(
            query=entity_name,
            session_id=session_id,
            node_type=NodeType.ENTITY.value,
            limit=5,
        )

        chunk_ids: set[str] = set()
        for entity in entities:
            # Find chunks that mention this entity
            edges = self._storage.get_graph_edges(
                entity["id"],
                direction="incoming",
                relationship=RelationType.MENTIONS.value,
            )
            for edge in edges:
                chunk_ids.add(edge["source_id"])

        # Get chunk nodes
        chunks: list[GraphNode] = []
        for chunk_id in list(chunk_ids)[:max_chunks]:
            node_data = self._storage.get_graph_node(chunk_id)
            if node_data:
                chunks.append(GraphNode.from_dict(node_data))

        return chunks


class GraphSearcher:
    """
    Search the knowledge graph using combined strategies.

    Combines:
    - Semantic similarity search (vector-based)
    - Keyword matching
    - Graph traversal for structural context
    """

    def __init__(self, session_id: str | None = None) -> None:
        self._session_id = session_id
        self._storage = get_graph_storage(session_id)
        self._traverser = GraphTraverser(session_id)
        self._embedding_manager = None

    def set_session_id(self, session_id: str) -> None:
        """Set the session ID and update storage."""
        self._session_id = session_id
        self._storage = get_graph_storage(session_id)
        self._traverser.set_session_id(session_id)

    def _get_embedding_manager(self):
        """Lazy load embedding manager."""
        if self._embedding_manager is None:
            try:
                from pinkyclawd.rlm.embedding import get_embedding_manager
                self._embedding_manager = get_embedding_manager()
            except ImportError:
                logger.warning("Embedding module not available")
        return self._embedding_manager

    async def search(
        self,
        query: str,
        session_id: str | None = None,
        limit: int = 10,
        expand_context: bool = True,
    ) -> list[tuple[GraphNode, float]]:
        """
        Search the graph for relevant nodes.

        Returns:
            List of (node, score) tuples sorted by relevance
        """
        # Update session if specified
        if session_id and session_id != self._session_id:
            self.set_session_id(session_id)

        results: dict[str, tuple[GraphNode, float]] = {}

        # 1. Keyword search
        keyword_matches = self._storage.search_graph_nodes(
            query=query,
            session_id=session_id,
            node_type=NodeType.CHUNK.value,
            limit=limit * 2,
        )

        for match in keyword_matches:
            node = GraphNode.from_dict(match)
            # Score based on content match (simple heuristic)
            query_terms = set(query.lower().split())
            content_terms = set(match["content"].lower().split())
            overlap = len(query_terms & content_terms)
            score = overlap / max(len(query_terms), 1)
            results[node.id] = (node, score * 0.4)  # Keyword weight: 0.4

        # 2. Semantic search
        embedding_manager = self._get_embedding_manager()
        if embedding_manager:
            try:
                from pinkyclawd.rlm.embedding import cosine_similarity

                query_embedding = await embedding_manager.embed(query)

                # Get chunks with embeddings
                chunks = self._storage.get_graph_nodes(
                    session_id=session_id,
                    node_type=NodeType.CHUNK.value,
                    limit=100,
                )

                for chunk in chunks:
                    if chunk.get("embedding"):
                        similarity = cosine_similarity(
                            query_embedding, chunk["embedding"]
                        )
                        if similarity > 0.3:  # Threshold
                            node = GraphNode.from_dict(chunk)
                            if node.id in results:
                                # Add to existing score
                                existing = results[node.id]
                                results[node.id] = (
                                    existing[0],
                                    existing[1] + similarity * 0.6,
                                )
                            else:
                                results[node.id] = (node, similarity * 0.6)

            except Exception as e:
                logger.warning(f"Semantic search failed: {e}")

        # 3. Expand context via graph traversal
        if expand_context and results:
            top_ids = [
                node.id
                for node, _ in sorted(
                    results.values(), key=lambda x: x[1], reverse=True
                )[:3]
            ]

            expanded = self._traverser.expand_context(
                node_ids=top_ids,
                max_depth=1,
                max_nodes=5,
            )

            for node in expanded:
                if node.id not in results:
                    # Add with reduced score
                    results[node.id] = (node, 0.2)

        # Sort by score and return
        sorted_results = sorted(
            results.values(), key=lambda x: x[1], reverse=True
        )
        return sorted_results[:limit]

    def search_sync(
        self,
        query: str,
        session_id: str | None = None,
        limit: int = 10,
    ) -> list[tuple[GraphNode, float]]:
        """
        Synchronous search using keyword matching only.
        """
        # Update session if specified
        if session_id and session_id != self._session_id:
            self.set_session_id(session_id)

        results: list[tuple[GraphNode, float]] = []

        # Keyword search
        matches = self._storage.search_graph_nodes(
            query=query,
            session_id=session_id,
            node_type=NodeType.CHUNK.value,
            limit=limit,
        )

        for match in matches:
            node = GraphNode.from_dict(match)
            query_terms = set(query.lower().split())
            content_terms = set(match["content"].lower().split())
            overlap = len(query_terms & content_terms)
            score = overlap / max(len(query_terms), 1)
            results.append((node, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results


# Global instances
_ingester: GraphIngester | None = None
_traverser: GraphTraverser | None = None
_searcher: GraphSearcher | None = None


def get_graph_ingester() -> GraphIngester:
    """Get the global graph ingester instance."""
    global _ingester
    if _ingester is None:
        _ingester = GraphIngester()
    return _ingester


def get_graph_traverser() -> GraphTraverser:
    """Get the global graph traverser instance."""
    global _traverser
    if _traverser is None:
        _traverser = GraphTraverser()
    return _traverser


def get_graph_searcher() -> GraphSearcher:
    """Get the global graph searcher instance."""
    global _searcher
    if _searcher is None:
        _searcher = GraphSearcher()
    return _searcher
