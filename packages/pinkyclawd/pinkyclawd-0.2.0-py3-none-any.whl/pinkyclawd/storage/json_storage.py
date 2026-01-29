"""
JSON file storage system for PinkyClawd.

Provides a file-based storage system using JSON files, replacing SQLite.
Each entity type has its own directory structure for easy debugging
and version control friendliness.

Directory Structure:
    ~/.pinkyclawd/storage/
    ├── migration              # Version tracker
    ├── project/{project_id}.json
    ├── session/{project_id}/{session_id}.json
    ├── message/{session_id}/{message_id}.json
    ├── part/{message_id}/{part_id}.json
    └── context/{session_id}/{block_id}.json
"""

from __future__ import annotations

import json
import shutil
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import TypeVar, Generic, Any, Iterator
from pydantic import BaseModel

from pinkyclawd.storage.lock import get_lock_manager, LockManager
from pinkyclawd.config.paths import get_data_dir

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# =============================================================================
# MODELS
# =============================================================================

class StorageModel(BaseModel):
    """Base model for storable entities."""

    id: str
    created_at: datetime = None
    updated_at: datetime = None

    def __init__(self, **data):
        if data.get("created_at") is None:
            data["created_at"] = datetime.now()
        if data.get("updated_at") is None:
            data["updated_at"] = datetime.now()
        super().__init__(**data)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }


class ProjectData(StorageModel):
    """Project metadata."""
    name: str = ""
    path: str = ""
    metadata: dict[str, Any] = {}


class SessionData(StorageModel):
    """Session metadata."""
    project_id: str
    title: str = "New Session"
    directory: str = ""
    parent_id: str | None = None
    is_archived: bool = False
    metadata: dict[str, Any] = {}
    message_count: int = 0


class MessageData(StorageModel):
    """Message data."""
    session_id: str
    role: str  # user, assistant, system, tool
    index: int = 0
    metadata: dict[str, Any] = {}


class PartData(StorageModel):
    """Message part data."""
    message_id: str
    type: str  # text, tool_use, tool_result, image
    content: dict[str, Any] = {}
    index: int = 0


class ContextBlockData(StorageModel):
    """Archived context block."""
    session_id: str
    task_id: str | None = None
    task_description: str = ""
    summary: str = ""
    content: str = ""
    tokens: int = 0
    embedding: list[float] | None = None
    metadata: dict[str, Any] = {}


# =============================================================================
# JSON FILE OPERATIONS
# =============================================================================

class JSONFileOps:
    """Low-level JSON file operations with locking."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._lock_manager = get_lock_manager()

    def read(self, path: Path) -> dict[str, Any] | None:
        """Read JSON from file with locking."""
        if not path.exists():
            return None

        with self._lock_manager.read_lock(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Error reading {path}: {e}")
                return None

    def write(self, path: Path, data: dict[str, Any]) -> bool:
        """Write JSON to file with locking."""
        path.parent.mkdir(parents=True, exist_ok=True)

        with self._lock_manager.write_lock(path):
            try:
                # Write to temp file first, then atomic rename
                temp_path = path.with_suffix(".tmp")
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
                temp_path.replace(path)
                return True
            except OSError as e:
                logger.error(f"Error writing {path}: {e}")
                return False

    def delete(self, path: Path) -> bool:
        """Delete a JSON file with locking."""
        if not path.exists():
            return True

        with self._lock_manager.write_lock(path):
            try:
                path.unlink()
                # Clean up empty parent directories
                self._cleanup_empty_dirs(path.parent)
                return True
            except OSError as e:
                logger.error(f"Error deleting {path}: {e}")
                return False

    def list_files(self, directory: Path, pattern: str = "*.json") -> list[Path]:
        """List JSON files in a directory."""
        if not directory.exists():
            return []
        return list(directory.glob(pattern))

    def _cleanup_empty_dirs(self, directory: Path) -> None:
        """Remove empty directories up to base_dir."""
        try:
            while directory != self._base_dir and directory.is_dir():
                if any(directory.iterdir()):
                    break
                directory.rmdir()
                directory = directory.parent
        except OSError:
            pass


# =============================================================================
# ENTITY STORE
# =============================================================================

class EntityStore(Generic[T]):
    """
    Generic store for a specific entity type.

    Handles CRUD operations for entities of type T.
    """

    def __init__(
        self,
        ops: JSONFileOps,
        base_path: Path,
        model_class: type[T],
    ) -> None:
        self._ops = ops
        self._base_path = base_path
        self._model_class = model_class

    def _get_path(self, *parts: str) -> Path:
        """Get file path for an entity."""
        return self._base_path.joinpath(*parts).with_suffix(".json")

    def get(self, *key_parts: str) -> T | None:
        """Get an entity by key parts."""
        path = self._get_path(*key_parts)
        data = self._ops.read(path)
        if data is None:
            return None
        try:
            return self._model_class(**data)
        except Exception as e:
            logger.error(f"Error parsing {path}: {e}")
            return None

    def save(self, entity: T, *key_parts: str) -> bool:
        """Save an entity."""
        path = self._get_path(*key_parts)
        # Update timestamps
        data = entity.model_dump(mode="json")
        data["updated_at"] = datetime.now().isoformat()
        return self._ops.write(path, data)

    def delete(self, *key_parts: str) -> bool:
        """Delete an entity."""
        path = self._get_path(*key_parts)
        return self._ops.delete(path)

    def list(self, *parent_parts: str) -> list[T]:
        """List all entities under a parent path."""
        parent_path = self._base_path.joinpath(*parent_parts) if parent_parts else self._base_path
        files = self._ops.list_files(parent_path)
        entities = []
        for file in files:
            data = self._ops.read(file)
            if data:
                try:
                    entities.append(self._model_class(**data))
                except Exception as e:
                    logger.warning(f"Error parsing {file}: {e}")
        return entities

    def exists(self, *key_parts: str) -> bool:
        """Check if an entity exists."""
        path = self._get_path(*key_parts)
        return path.exists()


# =============================================================================
# MAIN STORAGE CLASS
# =============================================================================

class JSONStorage:
    """
    JSON file-based storage system.

    Provides CRUD operations for all entity types using JSON files.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        if base_dir is None:
            base_dir = get_data_dir() / "storage"
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

        self._ops = JSONFileOps(base_dir)

        # Entity stores
        self._projects = EntityStore(
            self._ops, base_dir / "project", ProjectData
        )
        self._sessions = EntityStore(
            self._ops, base_dir / "session", SessionData
        )
        self._messages = EntityStore(
            self._ops, base_dir / "message", MessageData
        )
        self._parts = EntityStore(
            self._ops, base_dir / "part", PartData
        )
        self._context_blocks = EntityStore(
            self._ops, base_dir / "context", ContextBlockData
        )

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    # =========================================================================
    # Projects
    # =========================================================================

    def get_project(self, project_id: str) -> ProjectData | None:
        return self._projects.get(project_id)

    def save_project(self, project: ProjectData) -> bool:
        return self._projects.save(project, project.id)

    def delete_project(self, project_id: str) -> bool:
        return self._projects.delete(project_id)

    def list_projects(self) -> list[ProjectData]:
        return self._projects.list()

    # =========================================================================
    # Sessions
    # =========================================================================

    def get_session(self, project_id: str, session_id: str) -> SessionData | None:
        return self._sessions.get(project_id, session_id)

    def save_session(self, session: SessionData) -> bool:
        return self._sessions.save(session, session.project_id, session.id)

    def delete_session(self, project_id: str, session_id: str) -> bool:
        # Also delete all messages
        self._delete_session_messages(session_id)
        return self._sessions.delete(project_id, session_id)

    def list_sessions(self, project_id: str) -> list[SessionData]:
        return self._sessions.list(project_id)

    def list_all_sessions(self) -> list[SessionData]:
        """List all sessions across all projects."""
        sessions = []
        for project_dir in (self._base_dir / "session").iterdir():
            if project_dir.is_dir():
                sessions.extend(self._sessions.list(project_dir.name))
        return sessions

    # =========================================================================
    # Messages
    # =========================================================================

    def get_message(self, session_id: str, message_id: str) -> MessageData | None:
        return self._messages.get(session_id, message_id)

    def save_message(self, message: MessageData) -> bool:
        return self._messages.save(message, message.session_id, message.id)

    def delete_message(self, session_id: str, message_id: str) -> bool:
        # Also delete parts
        self._delete_message_parts(message_id)
        return self._messages.delete(session_id, message_id)

    def list_messages(self, session_id: str) -> list[MessageData]:
        messages = self._messages.list(session_id)
        return sorted(messages, key=lambda m: m.index)

    def _delete_session_messages(self, session_id: str) -> None:
        """Delete all messages for a session."""
        for message in self.list_messages(session_id):
            self.delete_message(session_id, message.id)

    # =========================================================================
    # Parts
    # =========================================================================

    def get_part(self, message_id: str, part_id: str) -> PartData | None:
        return self._parts.get(message_id, part_id)

    def save_part(self, part: PartData) -> bool:
        return self._parts.save(part, part.message_id, part.id)

    def delete_part(self, message_id: str, part_id: str) -> bool:
        return self._parts.delete(message_id, part_id)

    def list_parts(self, message_id: str) -> list[PartData]:
        parts = self._parts.list(message_id)
        return sorted(parts, key=lambda p: p.index)

    def _delete_message_parts(self, message_id: str) -> None:
        """Delete all parts for a message."""
        for part in self.list_parts(message_id):
            self.delete_part(message_id, part.id)

    # =========================================================================
    # Context Blocks
    # =========================================================================

    def get_context_block(self, session_id: str, block_id: str) -> ContextBlockData | None:
        return self._context_blocks.get(session_id, block_id)

    def save_context_block(self, block: ContextBlockData) -> bool:
        return self._context_blocks.save(block, block.session_id, block.id)

    def delete_context_block(self, session_id: str, block_id: str) -> bool:
        return self._context_blocks.delete(session_id, block_id)

    def list_context_blocks(
        self,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[ContextBlockData]:
        if session_id:
            blocks = self._context_blocks.list(session_id)
        else:
            blocks = []
            context_dir = self._base_dir / "context"
            if context_dir.exists():
                for session_dir in context_dir.iterdir():
                    if session_dir.is_dir():
                        blocks.extend(self._context_blocks.list(session_dir.name))

        # Sort by created_at descending
        blocks.sort(key=lambda b: b.created_at or datetime.min, reverse=True)
        return blocks[:limit]

    # =========================================================================
    # Utility
    # =========================================================================

    def get_storage_size(self) -> int:
        """Get total storage size in bytes."""
        total = 0
        for path in self._base_dir.rglob("*.json"):
            try:
                total += path.stat().st_size
            except OSError:
                pass
        return total

    def cleanup(self) -> None:
        """Clean up temporary files and empty directories."""
        # Remove temp files
        for temp_file in self._base_dir.rglob("*.tmp"):
            try:
                temp_file.unlink()
            except OSError:
                pass

        # Remove lock files
        for lock_file in self._base_dir.rglob("*.lock"):
            try:
                lock_file.unlink()
            except OSError:
                pass

    def export_session(self, session_id: str, output_path: Path) -> bool:
        """Export a session and all its data to a directory."""
        try:
            output_path.mkdir(parents=True, exist_ok=True)

            # Find session
            all_sessions = self.list_all_sessions()
            session = next((s for s in all_sessions if s.id == session_id), None)
            if not session:
                return False

            # Export session
            session_file = output_path / "session.json"
            with open(session_file, "w") as f:
                json.dump(session.model_dump(mode="json"), f, indent=2)

            # Export messages
            messages_dir = output_path / "messages"
            messages_dir.mkdir(exist_ok=True)
            for msg in self.list_messages(session_id):
                msg_file = messages_dir / f"{msg.id}.json"
                msg_data = msg.model_dump(mode="json")
                msg_data["parts"] = [
                    part.model_dump(mode="json")
                    for part in self.list_parts(msg.id)
                ]
                with open(msg_file, "w") as f:
                    json.dump(msg_data, f, indent=2)

            # Export context blocks
            context_dir = output_path / "context"
            context_dir.mkdir(exist_ok=True)
            for block in self.list_context_blocks(session_id):
                block_file = context_dir / f"{block.id}.json"
                with open(block_file, "w") as f:
                    json.dump(block.model_dump(mode="json"), f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Error exporting session: {e}")
            return False


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_json_storage: JSONStorage | None = None


def get_json_storage() -> JSONStorage:
    """Get the global JSON storage instance."""
    global _json_storage
    if _json_storage is None:
        _json_storage = JSONStorage()
    return _json_storage
