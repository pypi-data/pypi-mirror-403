"""
Graph ingestion for RLM-Graph.

Ingests content into the knowledge graph, converting documents
into a hierarchical structure of nodes and edges.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import uuid
from typing import Any

from pinkyclawd.config.storage import ContextBlock, Message, PartType
from pinkyclawd.rlm.extraction import EntityExtractor, ContentChunker
from pinkyclawd.rlm.graph import (
    GraphStorageAdapter,
    GraphNode,
    NodeType,
    RelationType,
    get_graph_storage,
)

logger = logging.getLogger(__name__)


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


# Global ingester instance
_ingester: GraphIngester | None = None


def get_graph_ingester() -> GraphIngester:
    """
    Get the global graph ingester instance.

    Prefer using pinkyclawd.core.get_graph_ingester() for consistency.
    """
    from pinkyclawd.core.state import get_state_factory
    return get_state_factory().graph_ingester
