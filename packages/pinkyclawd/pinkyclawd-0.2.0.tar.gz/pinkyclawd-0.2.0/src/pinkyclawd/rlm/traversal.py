"""
Graph traversal and search for RLM-Graph.

Provides utilities for navigating and searching the knowledge graph:
- GraphTraverser: Breadth-first and path-based traversal
- GraphSearcher: Combined keyword and semantic search
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from pinkyclawd.rlm.graph import (
    GraphStorageAdapter,
    GraphNode,
    NodeType,
    RelationType,
    get_graph_storage,
)

logger = logging.getLogger(__name__)


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
_traverser: GraphTraverser | None = None
_searcher: GraphSearcher | None = None


def get_graph_traverser() -> GraphTraverser:
    """
    Get the global graph traverser instance.

    Prefer using pinkyclawd.core.get_graph_traverser() for consistency.
    """
    from pinkyclawd.core.state import get_state_factory
    return get_state_factory().graph_traverser


def get_graph_searcher() -> GraphSearcher:
    """
    Get the global graph searcher instance.

    Prefer using pinkyclawd.core.get_graph_searcher() for consistency.
    """
    from pinkyclawd.core.state import get_state_factory
    return get_state_factory().graph_searcher
