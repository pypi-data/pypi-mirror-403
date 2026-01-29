"""
File-based JSON storage for RLM-Graph.

Provides a human-readable, debuggable storage format matching OpenCode's
simpler storage approach. Each node and edge is stored as a separate JSON file.

File structure:
    ~/.pinkyclawd/rlm/graph/
    └── {sessionID}/
        ├── nodes/
        │   └── {nodeID}.json           # Node content + metadata
        ├── edges/
        │   └── {nodeID}.edges.json     # Adjacency list per node
        ├── embeddings/
        │   └── {nodeID}.embedding.json # Vector embeddings (optional)
        └── indexes/
            ├── types.json              # { "chunk": [ids], "entity": [ids] }
            └── entities.json           # { "EntityName": [chunk_ids] }
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from threading import Lock, RLock
from typing import Any, Literal

logger = logging.getLogger(__name__)


class JSONGraphStorage:
    """
    File-based JSON storage for RLM-Graph.

    Implements the same interface as the SQLite storage methods
    for drop-in replacement.
    """

    def __init__(self, session_id: str, base_path: Path | None = None) -> None:
        """
        Initialize JSON graph storage for a session.

        Args:
            session_id: The session ID to store graph data for
            base_path: Base path for storage (defaults to get_graph_path())
        """
        self.session_id = session_id

        if base_path is None:
            from pinkyclawd.config.paths import get_graph_path
            base_path = get_graph_path()

        self.base_path = base_path / session_id
        self._lock = RLock()  # Reentrant lock for nested calls
        self._node_cache: dict[str, dict[str, Any]] = {}
        self._index_cache: dict[str, dict[str, list[str]]] = {}
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Ensure all required directories exist."""
        for subdir in ["nodes", "edges", "embeddings", "indexes"]:
            (self.base_path / subdir).mkdir(parents=True, exist_ok=True)

    def _node_path(self, node_id: str) -> Path:
        """Get the path for a node file."""
        return self.base_path / "nodes" / f"{node_id}.json"

    def _edge_path(self, node_id: str) -> Path:
        """Get the path for an edge file (adjacency list)."""
        return self.base_path / "edges" / f"{node_id}.edges.json"

    def _embedding_path(self, node_id: str) -> Path:
        """Get the path for an embedding file."""
        return self.base_path / "embeddings" / f"{node_id}.embedding.json"

    def _index_path(self, index_name: str) -> Path:
        """Get the path for an index file."""
        return self.base_path / "indexes" / f"{index_name}.json"

    def _read_json(self, path: Path) -> dict[str, Any] | None:
        """Read and parse a JSON file."""
        if not path.exists():
            return None
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read JSON from {path}: {e}")
            return None

    def _write_json(self, path: Path, data: dict[str, Any]) -> None:
        """Write data to a JSON file."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except OSError as e:
            logger.error(f"Failed to write JSON to {path}: {e}")
            raise

    def _load_index(self, index_name: str) -> dict[str, list[str]]:
        """Load an index file, using cache if available."""
        if index_name in self._index_cache:
            return self._index_cache[index_name]

        path = self._index_path(index_name)
        data = self._read_json(path) or {}
        self._index_cache[index_name] = data
        return data

    def _save_index(self, index_name: str, data: dict[str, list[str]]) -> None:
        """Save an index file and update cache."""
        self._index_cache[index_name] = data
        self._write_json(self._index_path(index_name), data)

    # Node operations

    def add_node(
        self,
        node_id: str,
        session_id: str,
        node_type: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        embedding: list[float] | None = None,
    ) -> None:
        """
        Add a node to the knowledge graph.

        Args:
            node_id: Unique node identifier
            session_id: Session ID (should match self.session_id)
            node_type: Type of node (document, section, chunk, entity)
            content: Text content of the node
            metadata: Optional metadata dictionary
            embedding: Optional vector embedding
        """
        with self._lock:
            node_data = {
                "id": node_id,
                "session_id": session_id,
                "type": node_type,
                "content": content,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
            }

            # Write node file
            self._write_json(self._node_path(node_id), node_data)

            # Write embedding separately if provided
            if embedding:
                self._write_json(self._embedding_path(node_id), {
                    "node_id": node_id,
                    "embedding": embedding,
                    "created_at": datetime.now().isoformat(),
                })

            # Update cache
            self._node_cache[node_id] = node_data

            # Update type index
            self._update_type_index(node_id, node_type)

            # Initialize empty adjacency list if not exists
            edge_path = self._edge_path(node_id)
            if not edge_path.exists():
                self._write_json(edge_path, {"outgoing": [], "incoming": []})

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        """
        Get a node from the knowledge graph.

        Args:
            node_id: The node ID to retrieve

        Returns:
            Node data dictionary or None if not found
        """
        # Check cache first
        if node_id in self._node_cache:
            node = self._node_cache[node_id].copy()
            # Load embedding if available
            embedding_data = self._read_json(self._embedding_path(node_id))
            node["embedding"] = embedding_data.get("embedding") if embedding_data else None
            return node

        # Read from file
        node_data = self._read_json(self._node_path(node_id))
        if node_data:
            # Cache the node
            self._node_cache[node_id] = node_data
            # Load embedding if available
            embedding_data = self._read_json(self._embedding_path(node_id))
            node_data["embedding"] = embedding_data.get("embedding") if embedding_data else None
            return node_data

        return None

    def get_nodes(
        self,
        session_id: str | None = None,  # noqa: ARG002 - interface compatibility
        node_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get nodes from the knowledge graph with optional filters.

        Args:
            session_id: Filter by session ID (ignored - we're already scoped to session)
            node_type: Filter by node type
            limit: Maximum number of nodes to return

        Returns:
            List of node data dictionaries
        """
        nodes: list[dict[str, Any]] = []

        if node_type:
            # Use type index for faster lookup
            type_index = self._load_index("types")
            node_ids = type_index.get(node_type, [])

            for node_id in node_ids[:limit]:
                node = self.get_node(node_id)
                if node:
                    nodes.append(node)
        else:
            # Scan all nodes directory
            nodes_dir = self.base_path / "nodes"
            if nodes_dir.exists():
                files = sorted(
                    nodes_dir.glob("*.json"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )

                for node_file in files[:limit]:
                    node_id = node_file.stem
                    node = self.get_node(node_id)
                    if node:
                        nodes.append(node)

        return nodes

    def search_nodes(
        self,
        query: str,
        session_id: str | None = None,  # noqa: ARG002 - interface compatibility
        node_type: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Search nodes by content.

        Args:
            query: Search query string
            session_id: Filter by session ID (ignored - scoped to session)
            node_type: Filter by node type
            limit: Maximum results

        Returns:
            List of matching node dictionaries
        """
        results: list[dict[str, Any]] = []
        query_lower = query.lower()

        # Get candidate nodes
        candidates = self.get_nodes(node_type=node_type, limit=500)

        for node in candidates:
            content = node.get("content", "").lower()
            if query_lower in content:
                results.append(node)
                if len(results) >= limit:
                    break

        return results

    def delete_node(self, node_id: str) -> bool:
        """
        Delete a node and its associated edges.

        Args:
            node_id: The node ID to delete

        Returns:
            True if node was deleted, False if not found
        """
        with self._lock:
            node_path = self._node_path(node_id)

            if not node_path.exists():
                return False

            # Get node type for index update
            node_data = self._read_json(node_path)
            node_type = node_data.get("type") if node_data else None

            # Delete node file
            try:
                node_path.unlink()
            except OSError:
                return False

            # Delete edge file
            edge_path = self._edge_path(node_id)
            if edge_path.exists():
                edge_path.unlink(missing_ok=True)

            # Delete embedding file
            embedding_path = self._embedding_path(node_id)
            if embedding_path.exists():
                embedding_path.unlink(missing_ok=True)

            # Remove from cache
            self._node_cache.pop(node_id, None)

            # Update type index
            if node_type:
                type_index = self._load_index("types")
                if node_type in type_index and node_id in type_index[node_type]:
                    type_index[node_type].remove(node_id)
                    self._save_index("types", type_index)

            # Clean up edges referencing this node in other nodes
            self._remove_node_from_edges(node_id)

            return True

    def _remove_node_from_edges(self, node_id: str) -> None:
        """Remove all edges referencing a deleted node."""
        edges_dir = self.base_path / "edges"
        if not edges_dir.exists():
            return

        for edge_file in edges_dir.glob("*.edges.json"):
            edges = self._read_json(edge_file)
            if not edges:
                continue

            modified = False

            # Filter outgoing edges
            outgoing = edges.get("outgoing", [])
            new_outgoing = [e for e in outgoing if e.get("target_id") != node_id]
            if len(new_outgoing) != len(outgoing):
                edges["outgoing"] = new_outgoing
                modified = True

            # Filter incoming edges
            incoming = edges.get("incoming", [])
            new_incoming = [e for e in incoming if e.get("source_id") != node_id]
            if len(new_incoming) != len(incoming):
                edges["incoming"] = new_incoming
                modified = True

            if modified:
                self._write_json(edge_file, edges)

    def _update_type_index(self, node_id: str, node_type: str) -> None:
        """Update the type index with a new node."""
        type_index = self._load_index("types")

        if node_type not in type_index:
            type_index[node_type] = []

        if node_id not in type_index[node_type]:
            type_index[node_type].append(node_id)
            self._save_index("types", type_index)

    # Edge operations

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add an edge to the knowledge graph.

        Maintains bidirectional adjacency lists for efficient traversal.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            relationship: Relationship type
            weight: Edge weight (default 1.0)
            metadata: Optional edge metadata
        """
        with self._lock:
            edge_data = {
                "relationship": relationship,
                "weight": weight,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
            }

            # Add to source's outgoing edges
            source_edges = self._read_json(self._edge_path(source_id)) or {
                "outgoing": [], "incoming": []
            }

            # Check for existing edge (avoid duplicates)
            existing = next(
                (e for e in source_edges["outgoing"]
                 if e.get("target_id") == target_id and e.get("relationship") == relationship),
                None
            )

            if existing:
                # Update existing edge
                existing.update(edge_data)
            else:
                # Add new outgoing edge
                source_edges["outgoing"].append({
                    "target_id": target_id,
                    **edge_data,
                })

            self._write_json(self._edge_path(source_id), source_edges)

            # Add to target's incoming edges
            target_edges = self._read_json(self._edge_path(target_id)) or {
                "outgoing": [], "incoming": []
            }

            # Check for existing incoming edge
            existing_incoming = next(
                (e for e in target_edges["incoming"]
                 if e.get("source_id") == source_id and e.get("relationship") == relationship),
                None
            )

            if existing_incoming:
                existing_incoming.update(edge_data)
            else:
                target_edges["incoming"].append({
                    "source_id": source_id,
                    **edge_data,
                })

            self._write_json(self._edge_path(target_id), target_edges)

    def get_edges(
        self,
        node_id: str,
        direction: Literal["outgoing", "incoming", "both"] = "both",
        relationship: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get edges connected to a node.

        Args:
            node_id: The node ID to get edges for
            direction: Edge direction to include
            relationship: Optional filter by relationship type

        Returns:
            List of edge dictionaries
        """
        edges_data = self._read_json(self._edge_path(node_id))
        if not edges_data:
            return []

        result: list[dict[str, Any]] = []

        if direction in ("outgoing", "both"):
            for edge in edges_data.get("outgoing", []):
                if relationship is None or edge.get("relationship") == relationship:
                    result.append({
                        "source_id": node_id,
                        "target_id": edge["target_id"],
                        "relationship": edge["relationship"],
                        "weight": edge.get("weight", 1.0),
                        "metadata": edge.get("metadata", {}),
                        "direction": "outgoing",
                    })

        if direction in ("incoming", "both"):
            for edge in edges_data.get("incoming", []):
                if relationship is None or edge.get("relationship") == relationship:
                    result.append({
                        "source_id": edge["source_id"],
                        "target_id": node_id,
                        "relationship": edge["relationship"],
                        "weight": edge.get("weight", 1.0),
                        "metadata": edge.get("metadata", {}),
                        "direction": "incoming",
                    })

        return result

    def get_neighbors(
        self,
        node_id: str,
        relationship: str | None = None,
        direction: Literal["outgoing", "incoming", "both"] = "outgoing",
        node_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get neighboring nodes connected by edges.

        Args:
            node_id: The source node ID
            relationship: Optional relationship type filter
            direction: Edge direction to traverse
            node_type: Optional filter by neighbor type

        Returns:
            List of neighbor node dictionaries
        """
        edges = self.get_edges(node_id, direction, relationship)
        neighbor_ids: set[str] = set()

        for edge in edges:
            if edge["direction"] == "outgoing":
                neighbor_ids.add(edge["target_id"])
            else:
                neighbor_ids.add(edge["source_id"])

        neighbors: list[dict[str, Any]] = []
        for nid in neighbor_ids:
            node = self.get_node(nid)
            if node and (node_type is None or node.get("type") == node_type):
                neighbors.append(node)

        return neighbors

    def delete_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
    ) -> bool:
        """
        Delete an edge from the knowledge graph.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            relationship: Relationship type

        Returns:
            True if edge was deleted, False if not found
        """
        with self._lock:
            deleted = False

            # Remove from source's outgoing
            source_edges = self._read_json(self._edge_path(source_id))
            if source_edges:
                original_count = len(source_edges.get("outgoing", []))
                source_edges["outgoing"] = [
                    e for e in source_edges.get("outgoing", [])
                    if not (e.get("target_id") == target_id and e.get("relationship") == relationship)
                ]
                if len(source_edges["outgoing"]) < original_count:
                    deleted = True
                    self._write_json(self._edge_path(source_id), source_edges)

            # Remove from target's incoming
            target_edges = self._read_json(self._edge_path(target_id))
            if target_edges:
                target_edges["incoming"] = [
                    e for e in target_edges.get("incoming", [])
                    if not (e.get("source_id") == source_id and e.get("relationship") == relationship)
                ]
                self._write_json(self._edge_path(target_id), target_edges)

            return deleted

    # Bulk operations

    def clear_session(self) -> None:
        """Clear all graph data for this session."""
        import shutil

        with self._lock:
            if self.base_path.exists():
                shutil.rmtree(self.base_path)

            # Clear caches
            self._node_cache.clear()
            self._index_cache.clear()

            # Recreate directories
            self._ensure_dirs()

    def export_all(self) -> dict[str, Any]:
        """
        Export all graph data as a single dictionary.

        Returns:
            Dictionary with all nodes, edges, and indexes
        """
        result = {
            "session_id": self.session_id,
            "nodes": [],
            "edges": [],
            "indexes": {},
            "exported_at": datetime.now().isoformat(),
        }

        # Export all nodes
        nodes_dir = self.base_path / "nodes"
        if nodes_dir.exists():
            for node_file in nodes_dir.glob("*.json"):
                node_data = self._read_json(node_file)
                if node_data:
                    # Include embedding if available
                    node_id = node_file.stem
                    embedding_data = self._read_json(self._embedding_path(node_id))
                    if embedding_data:
                        node_data["embedding"] = embedding_data.get("embedding")
                    result["nodes"].append(node_data)

        # Export all edges
        edges_dir = self.base_path / "edges"
        if edges_dir.exists():
            for edge_file in edges_dir.glob("*.edges.json"):
                edge_data = self._read_json(edge_file)
                if edge_data:
                    for out_edge in edge_data.get("outgoing", []):
                        result["edges"].append({
                            "source_id": edge_file.stem.replace(".edges", ""),
                            "target_id": out_edge.get("target_id"),
                            "relationship": out_edge.get("relationship"),
                            "weight": out_edge.get("weight", 1.0),
                            "metadata": out_edge.get("metadata", {}),
                        })

        # Export indexes
        indexes_dir = self.base_path / "indexes"
        if indexes_dir.exists():
            for index_file in indexes_dir.glob("*.json"):
                index_name = index_file.stem
                index_data = self._read_json(index_file)
                if index_data:
                    result["indexes"][index_name] = index_data

        return result

    def import_data(self, data: dict[str, Any]) -> None:
        """
        Import graph data from an exported dictionary.

        Args:
            data: Dictionary with nodes, edges, and indexes
        """
        with self._lock:
            # Clear existing data
            self.clear_session()

            # Import nodes
            for node in data.get("nodes", []):
                self.add_node(
                    node_id=node["id"],
                    session_id=node["session_id"],
                    node_type=node["type"],
                    content=node["content"],
                    metadata=node.get("metadata"),
                    embedding=node.get("embedding"),
                )

            # Import edges
            for edge in data.get("edges", []):
                self.add_edge(
                    source_id=edge["source_id"],
                    target_id=edge["target_id"],
                    relationship=edge["relationship"],
                    weight=edge.get("weight", 1.0),
                    metadata=edge.get("metadata"),
                )


# Storage instance cache per session
_storage_cache: dict[str, JSONGraphStorage] = {}
_cache_lock = Lock()


def get_json_graph_storage(session_id: str, base_path: Path | None = None) -> JSONGraphStorage:
    """
    Get or create a JSONGraphStorage instance for a session.

    Args:
        session_id: The session ID
        base_path: Optional custom base path

    Returns:
        JSONGraphStorage instance
    """
    global _storage_cache

    cache_key = f"{base_path}:{session_id}" if base_path else session_id

    with _cache_lock:
        if cache_key not in _storage_cache:
            _storage_cache[cache_key] = JSONGraphStorage(session_id, base_path)
        return _storage_cache[cache_key]


def clear_storage_cache() -> None:
    """Clear the storage instance cache."""
    global _storage_cache
    with _cache_lock:
        _storage_cache.clear()
