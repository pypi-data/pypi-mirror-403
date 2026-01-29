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
            """)

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
                INSERT INTO sessions (id, title, directory, parent_id, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session.id,
                    session.title,
                    session.directory,
                    session.parent_id,
                    session.created_at.isoformat(),
                    session.updated_at.isoformat(),
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
                    metadata=json.loads(row["metadata"]),
                )
        return None

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
            return [
                Session(
                    id=row["id"],
                    title=row["title"],
                    directory=row["directory"],
                    parent_id=row["parent_id"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    archived_at=datetime.fromisoformat(row["archived_at"])
                    if row["archived_at"]
                    else None,
                    metadata=json.loads(row["metadata"]),
                )
                for row in rows
            ]

    def update_session(self, session: Session) -> None:
        """Update a session."""
        session.updated_at = datetime.now()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE sessions
                SET title = ?, directory = ?, parent_id = ?, updated_at = ?,
                    archived_at = ?, metadata = ?
                WHERE id = ?
                """,
                (
                    session.title,
                    session.directory,
                    session.parent_id,
                    session.updated_at.isoformat(),
                    session.archived_at.isoformat() if session.archived_at else None,
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


# Global storage instance
_storage: Storage | None = None


def get_storage() -> Storage:
    """Get the global storage instance."""
    global _storage
    if _storage is None:
        _storage = Storage()
    return _storage
