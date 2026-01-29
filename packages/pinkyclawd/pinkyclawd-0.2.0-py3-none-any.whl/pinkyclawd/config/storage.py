"""
SQLite storage for sessions, messages, and RLM context.

Provides persistent storage matching pinkyclawd's data model.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Literal
from enum import Enum

from pinkyclawd.config.paths import get_database_path


class MessageRole(str, Enum):
    """Message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class PartType(str, Enum):
    """Message part types."""

    TEXT = "text"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    IMAGE = "image"
    FILE = "file"


@dataclass
class MessagePart:
    """A part of a message (text, tool call, etc.)."""

    id: str
    message_id: str
    type: PartType
    content: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "message_id": self.message_id,
            "type": self.type.value,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> MessagePart:
        return cls(
            id=data["id"],
            message_id=data["message_id"],
            type=PartType(data["type"]),
            content=data["content"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )


@dataclass
class Message:
    """A message in a session."""

    id: str
    session_id: str
    role: MessageRole
    parts: list[MessagePart] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role.value,
            "parts": [p.to_dict() for p in self.parts],
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Message:
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            role=MessageRole(data["role"]),
            parts=[MessagePart.from_dict(p) for p in data.get("parts", [])],
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {}),
        )


class SessionStatus(str, Enum):
    """Session status states."""

    IDLE = "idle"
    ACTIVE = "active"
    ABORTED = "aborted"


@dataclass
class Session:
    """A conversation session."""

    id: str
    title: str = "New Session"
    directory: str = ""
    parent_id: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    archived_at: datetime | None = None
    share_token: str | None = None
    status: SessionStatus = SessionStatus.IDLE
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "directory": self.directory,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "share_token": self.share_token,
            "status": self.status.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Session:
        return cls(
            id=data["id"],
            title=data.get("title", "New Session"),
            directory=data.get("directory", ""),
            parent_id=data.get("parent_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            archived_at=datetime.fromisoformat(data["archived_at"])
            if data.get("archived_at")
            else None,
            share_token=data.get("share_token"),
            status=SessionStatus(data.get("status", "idle")),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ContextBlock:
    """An archived context block for RLM."""

    id: str
    session_id: str
    task_id: str | None = None
    task_description: str = ""
    summary: str = ""
    content: str = ""
    tokens: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "task_description": self.task_description,
            "summary": self.summary,
            "content": self.content,
            "tokens": self.tokens,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> ContextBlock:
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            task_id=data.get("task_id"),
            task_description=data.get("task_description", ""),
            summary=data.get("summary", ""),
            content=data.get("content", ""),
            tokens=data.get("tokens", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
        )


class Storage:
    """SQLite-based storage for PinkyClawd data."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or get_database_path()
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT 'New Session',
                    directory TEXT DEFAULT '',
                    parent_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    archived_at TEXT,
                    share_token TEXT,
                    status TEXT DEFAULT 'idle',
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (parent_id) REFERENCES sessions(id)
                );
                
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS message_parts (
                    id TEXT PRIMARY KEY,
                    message_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS context_blocks (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    task_id TEXT,
                    task_description TEXT DEFAULT '',
                    summary TEXT DEFAULT '',
                    content TEXT NOT NULL,
                    tokens INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS todos (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    priority TEXT DEFAULT 'medium',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                
                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
                CREATE INDEX IF NOT EXISTS idx_parts_message ON message_parts(message_id);
                CREATE INDEX IF NOT EXISTS idx_context_session ON context_blocks(session_id);
                CREATE INDEX IF NOT EXISTS idx_todos_session ON todos(session_id);

                CREATE TABLE IF NOT EXISTS embeddings (
                    block_id TEXT PRIMARY KEY,
                    vector TEXT NOT NULL,
                    model TEXT NOT NULL,
                    dimensions INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (block_id) REFERENCES context_blocks(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_embeddings_block ON embeddings(block_id);

                -- RLM-Graph tables for knowledge graph storage
                CREATE TABLE IF NOT EXISTS graph_nodes (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    type TEXT NOT NULL,  -- 'document', 'section', 'chunk', 'entity'
                    content TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    embedding BLOB,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS graph_edges (
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relationship TEXT NOT NULL,  -- 'has_section', 'has_chunk', 'mentions', 'related_to'
                    weight REAL DEFAULT 1.0,
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (source_id, target_id, relationship),
                    FOREIGN KEY (source_id) REFERENCES graph_nodes(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_id) REFERENCES graph_nodes(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_graph_nodes_session ON graph_nodes(session_id);
                CREATE INDEX IF NOT EXISTS idx_graph_nodes_type ON graph_nodes(type);
                CREATE INDEX IF NOT EXISTS idx_graph_edges_source ON graph_edges(source_id);
                CREATE INDEX IF NOT EXISTS idx_graph_edges_target ON graph_edges(target_id);
                CREATE INDEX IF NOT EXISTS idx_graph_edges_rel ON graph_edges(relationship);
            """)

            # Run migrations for schema updates
            self._run_migrations(conn)

    def _run_migrations(self, conn: sqlite3.Connection) -> None:
        """Run database migrations for schema updates."""
        # Migration: Add share_token column to sessions if missing
        try:
            conn.execute("SELECT share_token FROM sessions LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute("ALTER TABLE sessions ADD COLUMN share_token TEXT")

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # Session operations

    def create_session(self, session: Session) -> Session:
        """Create a new session."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (id, title, directory, parent_id, created_at, updated_at, share_token, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session.id,
                    session.title,
                    session.directory,
                    session.parent_id,
                    session.created_at.isoformat(),
                    session.updated_at.isoformat(),
                    session.share_token,
                    session.status.value,
                    json.dumps(session.metadata),
                ),
            )
        return session

    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
            if row:
                return self._row_to_session(row)
        return None

    def _row_to_session(self, row: sqlite3.Row) -> Session:
        """Convert a database row to a Session object."""
        return Session(
            id=row["id"],
            title=row["title"],
            directory=row["directory"],
            parent_id=row["parent_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            archived_at=datetime.fromisoformat(row["archived_at"])
            if row["archived_at"]
            else None,
            share_token=row["share_token"] if "share_token" in row.keys() else None,
            status=SessionStatus(row["status"]) if "status" in row.keys() and row["status"] else SessionStatus.IDLE,
            metadata=json.loads(row["metadata"]),
        )

    def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
        directory: str | None = None,
    ) -> list[Session]:
        """List sessions with optional filtering."""
        with self._connect() as conn:
            query = "SELECT * FROM sessions"
            params: list[Any] = []

            if directory:
                query += " WHERE directory = ?"
                params.append(directory)

            query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = conn.execute(query, params).fetchall()
            return [self._row_to_session(row) for row in rows]

    def update_session(self, session: Session) -> None:
        """Update a session."""
        session.updated_at = datetime.now()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE sessions
                SET title = ?, directory = ?, parent_id = ?, updated_at = ?,
                    archived_at = ?, share_token = ?, status = ?, metadata = ?
                WHERE id = ?
                """,
                (
                    session.title,
                    session.directory,
                    session.parent_id,
                    session.updated_at.isoformat(),
                    session.archived_at.isoformat() if session.archived_at else None,
                    session.share_token,
                    session.status.value,
                    json.dumps(session.metadata),
                    session.id,
                ),
            )

    def delete_session(self, session_id: str) -> None:
        """Delete a session and all its data."""
        with self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    # Message operations

    def add_message(self, message: Message) -> Message:
        """Add a message to a session."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO messages (id, session_id, role, created_at, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    message.id,
                    message.session_id,
                    message.role.value,
                    message.created_at.isoformat(),
                    json.dumps(message.metadata),
                ),
            )

            for part in message.parts:
                conn.execute(
                    """
                    INSERT INTO message_parts (id, message_id, type, content, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        part.id,
                        part.message_id,
                        part.type.value,
                        json.dumps(part.content),
                        part.created_at.isoformat(),
                    ),
                )
        return message

    def get_messages(self, session_id: str) -> list[Message]:
        """Get all messages for a session."""
        with self._connect() as conn:
            msg_rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at",
                (session_id,),
            ).fetchall()

            messages = []
            for msg_row in msg_rows:
                part_rows = conn.execute(
                    "SELECT * FROM message_parts WHERE message_id = ? ORDER BY created_at",
                    (msg_row["id"],),
                ).fetchall()

                parts = [
                    MessagePart(
                        id=p["id"],
                        message_id=p["message_id"],
                        type=PartType(p["type"]),
                        content=json.loads(p["content"]),
                        created_at=datetime.fromisoformat(p["created_at"]),
                    )
                    for p in part_rows
                ]

                messages.append(
                    Message(
                        id=msg_row["id"],
                        session_id=msg_row["session_id"],
                        role=MessageRole(msg_row["role"]),
                        parts=parts,
                        created_at=datetime.fromisoformat(msg_row["created_at"]),
                        metadata=json.loads(msg_row["metadata"]),
                    )
                )

            return messages

    def add_message_part(self, part: MessagePart) -> None:
        """Add a part to an existing message."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO message_parts (id, message_id, type, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    part.id,
                    part.message_id,
                    part.type.value,
                    json.dumps(part.content),
                    part.created_at.isoformat(),
                ),
            )

    def get_message(self, message_id: str) -> Message | None:
        """Get a message by ID."""
        with self._connect() as conn:
            msg_row = conn.execute(
                "SELECT * FROM messages WHERE id = ?",
                (message_id,),
            ).fetchone()

            if not msg_row:
                return None

            part_rows = conn.execute(
                "SELECT * FROM message_parts WHERE message_id = ? ORDER BY created_at",
                (message_id,),
            ).fetchall()

            parts = [
                MessagePart(
                    id=p["id"],
                    message_id=p["message_id"],
                    type=PartType(p["type"]),
                    content=json.loads(p["content"]),
                    created_at=datetime.fromisoformat(p["created_at"]),
                )
                for p in part_rows
            ]

            return Message(
                id=msg_row["id"],
                session_id=msg_row["session_id"],
                role=MessageRole(msg_row["role"]),
                parts=parts,
                created_at=datetime.fromisoformat(msg_row["created_at"]),
                metadata=json.loads(msg_row["metadata"]),
            )

    def get_message_part(self, part_id: str) -> MessagePart | None:
        """Get a message part by ID."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM message_parts WHERE id = ?",
                (part_id,),
            ).fetchone()

            if row:
                return MessagePart(
                    id=row["id"],
                    message_id=row["message_id"],
                    type=PartType(row["type"]),
                    content=json.loads(row["content"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
        return None

    def update_message_part(self, part: MessagePart) -> None:
        """Update a message part."""
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE message_parts SET type = ?, content = ? WHERE id = ?
                """,
                (
                    part.type.value,
                    json.dumps(part.content),
                    part.id,
                ),
            )

    def delete_message_part(self, part_id: str) -> bool:
        """Delete a message part by ID."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM message_parts WHERE id = ?",
                (part_id,),
            )
            return cursor.rowcount > 0

    def delete_message(self, message_id: str) -> bool:
        """Delete a message and its parts."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM messages WHERE id = ?",
                (message_id,),
            )
            return cursor.rowcount > 0

    def get_sessions_by_status(self, status: SessionStatus) -> list[Session]:
        """Get all sessions with a specific status."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE status = ? ORDER BY updated_at DESC",
                (status.value,),
            ).fetchall()
            return [self._row_to_session(row) for row in rows]

    def get_session_by_share_token(self, share_token: str) -> Session | None:
        """Get a session by its share token."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE share_token = ?",
                (share_token,),
            ).fetchone()
            if row:
                return self._row_to_session(row)
        return None

    def get_child_sessions(self, parent_id: str) -> list[Session]:
        """Get all child sessions of a parent."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE parent_id = ? ORDER BY created_at DESC",
                (parent_id,),
            ).fetchall()
            return [self._row_to_session(row) for row in rows]

    # Context block operations (for RLM)

    def add_context_block(self, block: ContextBlock) -> ContextBlock:
        """Add a context block."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO context_blocks 
                (id, session_id, task_id, task_description, summary, content, tokens, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    block.id,
                    block.session_id,
                    block.task_id,
                    block.task_description,
                    block.summary,
                    block.content,
                    block.tokens,
                    block.created_at.isoformat(),
                ),
            )
        return block

    def get_context_blocks(
        self,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[ContextBlock]:
        """Get context blocks, optionally filtered by session."""
        with self._connect() as conn:
            if session_id:
                rows = conn.execute(
                    "SELECT * FROM context_blocks WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                    (session_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM context_blocks ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()

            return [
                ContextBlock(
                    id=row["id"],
                    session_id=row["session_id"],
                    task_id=row["task_id"],
                    task_description=row["task_description"],
                    summary=row["summary"],
                    content=row["content"],
                    tokens=row["tokens"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in rows
            ]

    def search_context_blocks(self, query: str, limit: int = 10) -> list[ContextBlock]:
        """Search context blocks by content."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM context_blocks
                WHERE content LIKE ? OR summary LIKE ? OR task_description LIKE ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (f"%{query}%", f"%{query}%", f"%{query}%", limit),
            ).fetchall()

            return [
                ContextBlock(
                    id=row["id"],
                    session_id=row["session_id"],
                    task_id=row["task_id"],
                    task_description=row["task_description"],
                    summary=row["summary"],
                    content=row["content"],
                    tokens=row["tokens"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in rows
            ]

    # Embedding operations (for semantic search)

    def save_embedding(
        self,
        block_id: str,
        vector: list[float],
        model: str,
        dimensions: int,
        content_hash: str,
    ) -> None:
        """Save an embedding for a context block."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO embeddings
                (block_id, vector, model, dimensions, content_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    block_id,
                    json.dumps(vector),
                    model,
                    dimensions,
                    content_hash,
                    datetime.now().isoformat(),
                ),
            )

    def get_embedding(self, block_id: str) -> tuple[list[float], str, str] | None:
        """
        Get embedding for a context block.

        Returns:
            Tuple of (vector, model, content_hash) or None if not found
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT vector, model, content_hash FROM embeddings WHERE block_id = ?",
                (block_id,),
            ).fetchone()

            if row:
                return (
                    json.loads(row["vector"]),
                    row["model"],
                    row["content_hash"],
                )
        return None

    def get_all_embeddings(
        self,
        session_id: str | None = None,
    ) -> list[tuple[str, list[float], str]]:
        """
        Get all embeddings, optionally filtered by session.

        Returns:
            List of (block_id, vector, content_hash) tuples
        """
        with self._connect() as conn:
            if session_id:
                rows = conn.execute(
                    """
                    SELECT e.block_id, e.vector, e.content_hash
                    FROM embeddings e
                    JOIN context_blocks cb ON e.block_id = cb.id
                    WHERE cb.session_id = ?
                    """,
                    (session_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT block_id, vector, content_hash FROM embeddings"
                ).fetchall()

            return [
                (row["block_id"], json.loads(row["vector"]), row["content_hash"])
                for row in rows
            ]

    def delete_embedding(self, block_id: str) -> None:
        """Delete embedding for a context block."""
        with self._connect() as conn:
            conn.execute("DELETE FROM embeddings WHERE block_id = ?", (block_id,))

    def has_embedding(self, block_id: str, content_hash: str) -> bool:
        """Check if a valid embedding exists for a block."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT content_hash FROM embeddings WHERE block_id = ?",
                (block_id,),
            ).fetchone()
            return row is not None and row["content_hash"] == content_hash

    # Graph operations (for RLM-Graph)

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
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO graph_nodes
                (id, session_id, type, content, metadata, embedding, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    node_id,
                    session_id,
                    node_type,
                    content,
                    json.dumps(metadata or {}),
                    json.dumps(embedding) if embedding else None,
                    datetime.now().isoformat(),
                ),
            )

    def get_graph_node(self, node_id: str) -> dict[str, Any] | None:
        """Get a node from the knowledge graph."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM graph_nodes WHERE id = ?",
                (node_id,),
            ).fetchone()

            if row:
                return {
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "type": row["type"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"]),
                    "embedding": json.loads(row["embedding"]) if row["embedding"] else None,
                    "created_at": row["created_at"],
                }
        return None

    def get_graph_nodes(
        self,
        session_id: str | None = None,
        node_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get nodes from the knowledge graph with optional filters."""
        with self._connect() as conn:
            query = "SELECT * FROM graph_nodes WHERE 1=1"
            params: list[Any] = []

            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)

            if node_type:
                query += " AND type = ?"
                params.append(node_type)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()

            return [
                {
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "type": row["type"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"]),
                    "embedding": json.loads(row["embedding"]) if row["embedding"] else None,
                    "created_at": row["created_at"],
                }
                for row in rows
            ]

    def search_graph_nodes(
        self,
        query: str,
        session_id: str | None = None,
        node_type: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search nodes by content."""
        with self._connect() as conn:
            sql = "SELECT * FROM graph_nodes WHERE content LIKE ?"
            params: list[Any] = [f"%{query}%"]

            if session_id:
                sql += " AND session_id = ?"
                params.append(session_id)

            if node_type:
                sql += " AND type = ?"
                params.append(node_type)

            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(sql, params).fetchall()

            return [
                {
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "type": row["type"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"]),
                    "embedding": json.loads(row["embedding"]) if row["embedding"] else None,
                    "created_at": row["created_at"],
                }
                for row in rows
            ]

    def delete_graph_node(self, node_id: str) -> bool:
        """Delete a node and its edges."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM graph_nodes WHERE id = ?", (node_id,))
            return cursor.rowcount > 0

    def add_graph_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add an edge to the knowledge graph."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO graph_edges
                (source_id, target_id, relationship, weight, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    target_id,
                    relationship,
                    weight,
                    json.dumps(metadata or {}),
                    datetime.now().isoformat(),
                ),
            )

    def get_graph_edges(
        self,
        node_id: str,
        direction: Literal["outgoing", "incoming", "both"] = "both",
        relationship: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get edges connected to a node."""
        with self._connect() as conn:
            edges = []

            if direction in ("outgoing", "both"):
                query = "SELECT * FROM graph_edges WHERE source_id = ?"
                params: list[Any] = [node_id]
                if relationship:
                    query += " AND relationship = ?"
                    params.append(relationship)

                rows = conn.execute(query, params).fetchall()
                edges.extend([
                    {
                        "source_id": row["source_id"],
                        "target_id": row["target_id"],
                        "relationship": row["relationship"],
                        "weight": row["weight"],
                        "metadata": json.loads(row["metadata"]),
                        "direction": "outgoing",
                    }
                    for row in rows
                ])

            if direction in ("incoming", "both"):
                query = "SELECT * FROM graph_edges WHERE target_id = ?"
                params = [node_id]
                if relationship:
                    query += " AND relationship = ?"
                    params.append(relationship)

                rows = conn.execute(query, params).fetchall()
                edges.extend([
                    {
                        "source_id": row["source_id"],
                        "target_id": row["target_id"],
                        "relationship": row["relationship"],
                        "weight": row["weight"],
                        "metadata": json.loads(row["metadata"]),
                        "direction": "incoming",
                    }
                    for row in rows
                ])

            return edges

    def get_neighbors(
        self,
        node_id: str,
        relationship: str | None = None,
        direction: Literal["outgoing", "incoming", "both"] = "outgoing",
        node_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get neighboring nodes connected by edges."""
        edges = self.get_graph_edges(node_id, direction, relationship)
        neighbor_ids = set()

        for edge in edges:
            if edge["direction"] == "outgoing":
                neighbor_ids.add(edge["target_id"])
            else:
                neighbor_ids.add(edge["source_id"])

        if not neighbor_ids:
            return []

        with self._connect() as conn:
            placeholders = ",".join("?" * len(neighbor_ids))
            query = f"SELECT * FROM graph_nodes WHERE id IN ({placeholders})"
            params: list[Any] = list(neighbor_ids)

            if node_type:
                query += " AND type = ?"
                params.append(node_type)

            rows = conn.execute(query, params).fetchall()

            return [
                {
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "type": row["type"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"]),
                    "embedding": json.loads(row["embedding"]) if row["embedding"] else None,
                    "created_at": row["created_at"],
                }
                for row in rows
            ]

    def delete_graph_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
    ) -> bool:
        """Delete an edge from the knowledge graph."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM graph_edges WHERE source_id = ? AND target_id = ? AND relationship = ?",
                (source_id, target_id, relationship),
            )
            return cursor.rowcount > 0

    def clear_session_graph(self, session_id: str) -> None:
        """Clear all graph data for a session."""
        with self._connect() as conn:
            # Get node IDs first
            node_ids = conn.execute(
                "SELECT id FROM graph_nodes WHERE session_id = ?",
                (session_id,),
            ).fetchall()

            if node_ids:
                ids = [row["id"] for row in node_ids]
                placeholders = ",".join("?" * len(ids))

                # Delete edges connected to these nodes
                conn.execute(
                    f"DELETE FROM graph_edges WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})",
                    ids + ids,
                )

            # Delete nodes
            conn.execute("DELETE FROM graph_nodes WHERE session_id = ?", (session_id,))


class JSONStorageAdapter:
    """
    Adapter that wraps JSON storage to provide the same interface as SQLite Storage.

    This allows seamless switching between SQLite and JSON backends.
    """

    def __init__(self) -> None:
        from pinkyclawd.storage import get_json_storage
        self._json = get_json_storage()
        self._default_project_id = "default"

    # Session operations

    def create_session(self, session: Session) -> Session:
        """Create a new session."""
        from pinkyclawd.storage import SessionData
        session_data = SessionData(
            id=session.id,
            project_id=self._default_project_id,
            title=session.title,
            directory=session.directory,
            parent_id=session.parent_id,
            is_archived=session.archived_at is not None,
            metadata=session.metadata,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
        self._json.save_session(session_data)
        return session

    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID."""
        data = self._json.get_session(self._default_project_id, session_id)
        if data is None:
            # Try other projects
            for session in self._json.list_all_sessions():
                if session.id == session_id:
                    data = session
                    break
        if data is None:
            return None
        return Session(
            id=data.id,
            title=data.title,
            directory=data.directory,
            parent_id=data.parent_id,
            created_at=data.created_at,
            updated_at=data.updated_at,
            archived_at=datetime.now() if data.is_archived else None,
            status=SessionStatus.IDLE,
            metadata=data.metadata,
        )

    def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
        directory: str | None = None,
    ) -> list[Session]:
        """List sessions with optional filtering."""
        sessions = self._json.list_all_sessions()

        if directory:
            sessions = [s for s in sessions if s.directory == directory]

        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at or datetime.min, reverse=True)

        # Apply offset and limit
        sessions = sessions[offset:offset + limit]

        return [
            Session(
                id=s.id,
                title=s.title,
                directory=s.directory,
                parent_id=s.parent_id,
                created_at=s.created_at,
                updated_at=s.updated_at,
                archived_at=datetime.now() if s.is_archived else None,
                status=SessionStatus.IDLE,
                metadata=s.metadata,
            )
            for s in sessions
        ]

    def update_session(self, session: Session) -> None:
        """Update a session."""
        from pinkyclawd.storage import SessionData
        # Find existing session's project_id
        existing = None
        for s in self._json.list_all_sessions():
            if s.id == session.id:
                existing = s
                break
        project_id = existing.project_id if existing else self._default_project_id

        session_data = SessionData(
            id=session.id,
            project_id=project_id,
            title=session.title,
            directory=session.directory,
            parent_id=session.parent_id,
            is_archived=session.archived_at is not None,
            metadata=session.metadata,
            created_at=session.created_at,
            updated_at=datetime.now(),
        )
        self._json.save_session(session_data)

    def delete_session(self, session_id: str) -> None:
        """Delete a session and all its data."""
        # Find project_id
        for session in self._json.list_all_sessions():
            if session.id == session_id:
                self._json.delete_session(session.project_id, session_id)
                return

    # Message operations

    def add_message(self, message: Message) -> Message:
        """Add a message to a session."""
        from pinkyclawd.storage import MessageData, PartData

        # Get current message count for index
        existing_messages = self._json.list_messages(message.session_id)
        index = len(existing_messages)

        msg_data = MessageData(
            id=message.id,
            session_id=message.session_id,
            role=message.role.value,
            index=index,
            metadata=message.metadata,
            created_at=message.created_at,
        )
        self._json.save_message(msg_data)

        # Save parts
        for i, part in enumerate(message.parts):
            part_data = PartData(
                id=part.id,
                message_id=message.id,
                type=part.type.value,
                content=part.content,
                index=i,
                created_at=part.created_at,
            )
            self._json.save_part(part_data)

        return message

    def get_messages(self, session_id: str) -> list[Message]:
        """Get all messages for a session."""
        msg_list = self._json.list_messages(session_id)
        messages = []

        for msg_data in msg_list:
            parts_data = self._json.list_parts(msg_data.id)
            parts = [
                MessagePart(
                    id=p.id,
                    message_id=p.message_id,
                    type=PartType(p.type),
                    content=p.content,
                    created_at=p.created_at,
                )
                for p in parts_data
            ]

            messages.append(
                Message(
                    id=msg_data.id,
                    session_id=msg_data.session_id,
                    role=MessageRole(msg_data.role),
                    parts=parts,
                    created_at=msg_data.created_at,
                    metadata=msg_data.metadata,
                )
            )

        return messages

    def get_message(self, message_id: str) -> Message | None:
        """Get a message by ID."""
        # Need to find which session the message belongs to
        # This is inefficient but maintains compatibility
        for session in self._json.list_all_sessions():
            msg_data = self._json.get_message(session.id, message_id)
            if msg_data:
                parts_data = self._json.list_parts(message_id)
                parts = [
                    MessagePart(
                        id=p.id,
                        message_id=p.message_id,
                        type=PartType(p.type),
                        content=p.content,
                        created_at=p.created_at,
                    )
                    for p in parts_data
                ]
                return Message(
                    id=msg_data.id,
                    session_id=msg_data.session_id,
                    role=MessageRole(msg_data.role),
                    parts=parts,
                    created_at=msg_data.created_at,
                    metadata=msg_data.metadata,
                )
        return None

    def delete_message(self, message_id: str) -> bool:
        """Delete a message and its parts."""
        # Find which session the message belongs to
        for session in self._json.list_all_sessions():
            if self._json.get_message(session.id, message_id):
                return self._json.delete_message(session.id, message_id)
        return False

    def add_message_part(self, part: MessagePart) -> None:
        """Add a part to an existing message."""
        from pinkyclawd.storage import PartData

        existing_parts = self._json.list_parts(part.message_id)
        index = len(existing_parts)

        part_data = PartData(
            id=part.id,
            message_id=part.message_id,
            type=part.type.value,
            content=part.content,
            index=index,
            created_at=part.created_at,
        )
        self._json.save_part(part_data)

    def get_message_part(self, part_id: str) -> MessagePart | None:
        """Get a message part by ID."""
        # This requires searching through all messages
        for session in self._json.list_all_sessions():
            for msg in self._json.list_messages(session.id):
                part_data = self._json.get_part(msg.id, part_id)
                if part_data:
                    return MessagePart(
                        id=part_data.id,
                        message_id=part_data.message_id,
                        type=PartType(part_data.type),
                        content=part_data.content,
                        created_at=part_data.created_at,
                    )
        return None

    def update_message_part(self, part: MessagePart) -> None:
        """Update a message part."""
        from pinkyclawd.storage import PartData

        existing = self._json.get_part(part.message_id, part.id)
        index = existing.index if existing else 0

        part_data = PartData(
            id=part.id,
            message_id=part.message_id,
            type=part.type.value,
            content=part.content,
            index=index,
            created_at=part.created_at,
        )
        self._json.save_part(part_data)

    def delete_message_part(self, part_id: str) -> bool:
        """Delete a message part by ID."""
        for session in self._json.list_all_sessions():
            for msg in self._json.list_messages(session.id):
                if self._json.get_part(msg.id, part_id):
                    return self._json.delete_part(msg.id, part_id)
        return False

    # Context block operations

    def add_context_block(self, block: ContextBlock) -> ContextBlock:
        """Add a context block."""
        from pinkyclawd.storage import ContextBlockData

        block_data = ContextBlockData(
            id=block.id,
            session_id=block.session_id,
            task_id=block.task_id,
            task_description=block.task_description,
            summary=block.summary,
            content=block.content,
            tokens=block.tokens,
            created_at=block.created_at,
        )
        self._json.save_context_block(block_data)
        return block

    def get_context_blocks(
        self,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[ContextBlock]:
        """Get context blocks, optionally filtered by session."""
        blocks = self._json.list_context_blocks(session_id, limit)
        return [
            ContextBlock(
                id=b.id,
                session_id=b.session_id,
                task_id=b.task_id,
                task_description=b.task_description,
                summary=b.summary,
                content=b.content,
                tokens=b.tokens,
                created_at=b.created_at,
            )
            for b in blocks
        ]

    def search_context_blocks(self, query: str, limit: int = 10) -> list[ContextBlock]:
        """Search context blocks by content."""
        # Simple text search across all blocks
        all_blocks = self._json.list_context_blocks(limit=1000)
        query_lower = query.lower()

        matches = [
            b for b in all_blocks
            if query_lower in b.content.lower()
            or query_lower in b.summary.lower()
            or query_lower in b.task_description.lower()
        ]

        matches.sort(key=lambda b: b.created_at or datetime.min, reverse=True)
        return [
            ContextBlock(
                id=b.id,
                session_id=b.session_id,
                task_id=b.task_id,
                task_description=b.task_description,
                summary=b.summary,
                content=b.content,
                tokens=b.tokens,
                created_at=b.created_at,
            )
            for b in matches[:limit]
        ]

    # Embedding operations (stored in context block metadata for JSON)

    def save_embedding(
        self,
        block_id: str,
        vector: list[float],
        model: str,
        dimensions: int,
        content_hash: str,
    ) -> None:
        """Save an embedding for a context block."""
        # Find the block and update its embedding metadata
        for session in self._json.list_all_sessions():
            block = self._json.get_context_block(session.id, block_id)
            if block:
                block.embedding = vector
                block.metadata = block.metadata or {}
                block.metadata["embedding_model"] = model
                block.metadata["embedding_dimensions"] = dimensions
                block.metadata["content_hash"] = content_hash
                self._json.save_context_block(block)
                return

    def get_embedding(self, block_id: str) -> tuple[list[float], str, str] | None:
        """Get embedding for a context block."""
        for session in self._json.list_all_sessions():
            block = self._json.get_context_block(session.id, block_id)
            if block and block.embedding:
                model = block.metadata.get("embedding_model", "")
                content_hash = block.metadata.get("content_hash", "")
                return (block.embedding, model, content_hash)
        return None

    def get_all_embeddings(
        self,
        session_id: str | None = None,
    ) -> list[tuple[str, list[float], str]]:
        """Get all embeddings, optionally filtered by session."""
        results = []
        blocks = self._json.list_context_blocks(session_id, limit=10000)

        for block in blocks:
            if block.embedding:
                content_hash = block.metadata.get("content_hash", "")
                results.append((block.id, block.embedding, content_hash))

        return results

    def delete_embedding(self, block_id: str) -> None:
        """Delete embedding for a context block."""
        for session in self._json.list_all_sessions():
            block = self._json.get_context_block(session.id, block_id)
            if block:
                block.embedding = None
                if block.metadata:
                    block.metadata.pop("embedding_model", None)
                    block.metadata.pop("embedding_dimensions", None)
                    block.metadata.pop("content_hash", None)
                self._json.save_context_block(block)
                return

    def has_embedding(self, block_id: str, content_hash: str) -> bool:
        """Check if a valid embedding exists for a block."""
        for session in self._json.list_all_sessions():
            block = self._json.get_context_block(session.id, block_id)
            if block and block.embedding:
                return block.metadata.get("content_hash") == content_hash
        return False

    # Stub methods for graph operations (delegated to RLM Graph storage)

    def add_graph_node(self, *args, **kwargs) -> None:
        """Graph operations use separate RLM Graph storage."""
        pass

    def get_graph_node(self, node_id: str) -> dict[str, Any] | None:
        return None

    def get_graph_nodes(self, *args, **kwargs) -> list[dict[str, Any]]:
        return []

    def search_graph_nodes(self, *args, **kwargs) -> list[dict[str, Any]]:
        return []

    def delete_graph_node(self, node_id: str) -> bool:
        return False

    def add_graph_edge(self, *args, **kwargs) -> None:
        pass

    def get_graph_edges(self, *args, **kwargs) -> list[dict[str, Any]]:
        return []

    def get_neighbors(self, *args, **kwargs) -> list[dict[str, Any]]:
        return []

    def delete_graph_edge(self, *args, **kwargs) -> bool:
        return False

    def clear_session_graph(self, session_id: str) -> None:
        pass

    # Additional compatibility methods

    def get_sessions_by_status(self, status: SessionStatus) -> list[Session]:
        """Get all sessions with a specific status."""
        # JSON storage doesn't track status separately
        return []

    def get_session_by_share_token(self, share_token: str) -> Session | None:
        """Get a session by its share token."""
        for session_data in self._json.list_all_sessions():
            if session_data.metadata.get("share_token") == share_token:
                return Session(
                    id=session_data.id,
                    title=session_data.title,
                    directory=session_data.directory,
                    parent_id=session_data.parent_id,
                    created_at=session_data.created_at,
                    updated_at=session_data.updated_at,
                    share_token=share_token,
                    metadata=session_data.metadata,
                )
        return None

    def get_child_sessions(self, parent_id: str) -> list[Session]:
        """Get all child sessions of a parent."""
        return [
            Session(
                id=s.id,
                title=s.title,
                directory=s.directory,
                parent_id=s.parent_id,
                created_at=s.created_at,
                updated_at=s.updated_at,
                metadata=s.metadata,
            )
            for s in self._json.list_all_sessions()
            if s.parent_id == parent_id
        ]


# Union type for storage backends
StorageBackend = Storage | JSONStorageAdapter


def get_storage() -> StorageBackend:
    """
    Get the global storage instance.

    Returns the appropriate storage backend based on configuration.
    Prefer using pinkyclawd.core.get_storage() for consistency.
    """
    from pinkyclawd.core.state import get_state_factory
    return get_state_factory().storage
