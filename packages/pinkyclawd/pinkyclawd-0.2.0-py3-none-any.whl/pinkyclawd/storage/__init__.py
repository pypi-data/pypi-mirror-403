"""
JSON-based storage system for PinkyClawd.

Provides file-based storage using JSON files, replacing SQLite for
better debuggability and version control friendliness.

Usage:
    from pinkyclawd.storage import get_json_storage

    storage = get_json_storage()
    session = storage.get_session(project_id, session_id)
"""

from __future__ import annotations

# Lock utilities
from pinkyclawd.storage.lock import (
    FileLock,
    LockManager,
    get_lock_manager,
)

# JSON storage
from pinkyclawd.storage.json_storage import (
    StorageModel,
    ProjectData,
    SessionData,
    MessageData,
    PartData,
    ContextBlockData,
    JSONFileOps,
    EntityStore,
    JSONStorage,
    get_json_storage,
)

# Migrations
from pinkyclawd.storage.migrations import (
    Migration,
    MigrationRunner,
    get_migration_runner,
    run_migrations,
    migrate_from_sqlite,
)

__all__ = [
    # Lock
    "FileLock",
    "LockManager",
    "get_lock_manager",
    # Models
    "StorageModel",
    "ProjectData",
    "SessionData",
    "MessageData",
    "PartData",
    "ContextBlockData",
    # Storage
    "JSONFileOps",
    "EntityStore",
    "JSONStorage",
    "get_json_storage",
    # Migrations
    "Migration",
    "MigrationRunner",
    "get_migration_runner",
    "run_migrations",
    "migrate_from_sqlite",
]
