"""
Schema migration system for JSON storage.

Handles data migrations when the storage schema changes.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Any

from pinkyclawd.storage.json_storage import get_json_storage
from pinkyclawd.config.paths import get_data_dir

logger = logging.getLogger(__name__)


@dataclass
class Migration:
    """A migration definition."""
    version: int
    name: str
    up: Callable[[Path], bool]
    down: Callable[[Path], bool] | None = None


class MigrationRunner:
    """
    Runs migrations on the storage directory.

    Tracks applied migrations in a version file.
    """

    VERSION_FILE = "migration"

    def __init__(self, storage_dir: Path | None = None) -> None:
        if storage_dir is None:
            storage_dir = get_data_dir() / "storage"
        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._version_file = self._storage_dir / self.VERSION_FILE
        self._migrations: list[Migration] = []

    def register(self, migration: Migration) -> None:
        """Register a migration."""
        self._migrations.append(migration)
        self._migrations.sort(key=lambda m: m.version)

    def get_current_version(self) -> int:
        """Get the current schema version."""
        if not self._version_file.exists():
            return 0

        try:
            data = json.loads(self._version_file.read_text())
            return data.get("version", 0)
        except (json.JSONDecodeError, OSError):
            return 0

    def set_version(self, version: int) -> None:
        """Set the current schema version."""
        data = {
            "version": version,
            "migrated_at": datetime.now().isoformat(),
        }
        self._version_file.write_text(json.dumps(data, indent=2))

    def get_pending_migrations(self) -> list[Migration]:
        """Get migrations that need to be applied."""
        current = self.get_current_version()
        return [m for m in self._migrations if m.version > current]

    def run_pending(self, dry_run: bool = False) -> list[str]:
        """
        Run all pending migrations.

        Args:
            dry_run: If True, don't actually apply migrations

        Returns:
            List of applied migration names
        """
        pending = self.get_pending_migrations()
        if not pending:
            logger.info("No pending migrations")
            return []

        applied = []
        for migration in pending:
            logger.info(f"Applying migration {migration.version}: {migration.name}")
            if not dry_run:
                try:
                    if migration.up(self._storage_dir):
                        self.set_version(migration.version)
                        applied.append(migration.name)
                    else:
                        logger.error(f"Migration {migration.name} failed")
                        break
                except Exception as e:
                    logger.error(f"Migration {migration.name} error: {e}")
                    break
            else:
                applied.append(migration.name)

        return applied

    def rollback(self, target_version: int = 0) -> list[str]:
        """
        Rollback migrations to a target version.

        Args:
            target_version: Version to rollback to

        Returns:
            List of rolled back migration names
        """
        current = self.get_current_version()
        if current <= target_version:
            logger.info(f"Already at version {current}")
            return []

        # Get migrations to rollback in reverse order
        to_rollback = [
            m for m in self._migrations
            if m.version <= current and m.version > target_version
        ]
        to_rollback.sort(key=lambda m: m.version, reverse=True)

        rolled_back = []
        for migration in to_rollback:
            if migration.down is None:
                logger.warning(f"No rollback for migration {migration.name}")
                continue

            logger.info(f"Rolling back migration {migration.version}: {migration.name}")
            try:
                if migration.down(self._storage_dir):
                    rolled_back.append(migration.name)
                else:
                    logger.error(f"Rollback of {migration.name} failed")
                    break
            except Exception as e:
                logger.error(f"Rollback of {migration.name} error: {e}")
                break

        # Update version
        if rolled_back:
            remaining = [
                m for m in self._migrations
                if m.version <= self.get_current_version()
                and m.name not in rolled_back
            ]
            new_version = max((m.version for m in remaining), default=0)
            self.set_version(new_version)

        return rolled_back


# =============================================================================
# BUILT-IN MIGRATIONS
# =============================================================================

def migration_001_init(storage_dir: Path) -> bool:
    """Initial schema setup."""
    # Create directory structure
    dirs = ["project", "session", "message", "part", "context"]
    for dir_name in dirs:
        (storage_dir / dir_name).mkdir(exist_ok=True)
    return True


def migration_002_add_embeddings_dir(storage_dir: Path) -> bool:
    """Add embeddings directory."""
    (storage_dir / "embeddings").mkdir(exist_ok=True)
    return True


def migration_003_add_graph_dir(storage_dir: Path) -> bool:
    """Add graph directory for RLM-Graph."""
    graph_dir = storage_dir / "graph"
    graph_dir.mkdir(exist_ok=True)
    (graph_dir / "nodes").mkdir(exist_ok=True)
    (graph_dir / "edges").mkdir(exist_ok=True)
    return True


# =============================================================================
# DEFAULT MIGRATIONS
# =============================================================================

def get_default_migrations() -> list[Migration]:
    """Get the list of default migrations."""
    return [
        Migration(
            version=1,
            name="initial_schema",
            up=migration_001_init,
        ),
        Migration(
            version=2,
            name="add_embeddings",
            up=migration_002_add_embeddings_dir,
        ),
        Migration(
            version=3,
            name="add_graph",
            up=migration_003_add_graph_dir,
        ),
    ]


def get_migration_runner() -> MigrationRunner:
    """Get a migration runner with default migrations."""
    runner = MigrationRunner()
    for migration in get_default_migrations():
        runner.register(migration)
    return runner


def run_migrations() -> list[str]:
    """Run all pending migrations."""
    runner = get_migration_runner()
    return runner.run_pending()


# =============================================================================
# SQLITE TO JSON MIGRATION
# =============================================================================

def migrate_from_sqlite(sqlite_path: Path, json_storage_dir: Path) -> bool:
    """
    Migrate data from SQLite to JSON storage.

    Args:
        sqlite_path: Path to SQLite database
        json_storage_dir: Path to JSON storage directory

    Returns:
        True if migration succeeded
    """
    import sqlite3
    import uuid

    if not sqlite_path.exists():
        logger.info("No SQLite database to migrate")
        return True

    try:
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row

        from pinkyclawd.storage.json_storage import (
            JSONStorage,
            SessionData,
            MessageData,
            PartData,
            ContextBlockData,
        )

        storage = JSONStorage(json_storage_dir)

        # Migrate sessions
        cursor = conn.execute("SELECT * FROM sessions")
        for row in cursor:
            session = SessionData(
                id=row["id"],
                project_id=row.get("project_id", "default"),
                title=row["title"] or "Untitled",
                directory=row.get("directory", ""),
                parent_id=row.get("parent_id"),
                is_archived=bool(row.get("is_archived", False)),
                created_at=datetime.fromisoformat(row["created_at"])
                    if row["created_at"] else datetime.now(),
                updated_at=datetime.fromisoformat(row["updated_at"])
                    if row.get("updated_at") else datetime.now(),
            )
            storage.save_session(session)
            logger.info(f"Migrated session: {session.id}")

        # Migrate messages
        cursor = conn.execute("SELECT * FROM messages ORDER BY created_at")
        message_index = {}  # session_id -> current index
        for row in cursor:
            session_id = row["session_id"]
            if session_id not in message_index:
                message_index[session_id] = 0

            message = MessageData(
                id=row["id"],
                session_id=session_id,
                role=row["role"],
                index=message_index[session_id],
                created_at=datetime.fromisoformat(row["created_at"])
                    if row["created_at"] else datetime.now(),
            )
            storage.save_message(message)
            message_index[session_id] += 1

        # Migrate message parts
        cursor = conn.execute("SELECT * FROM message_parts ORDER BY created_at")
        part_index = {}  # message_id -> current index
        for row in cursor:
            message_id = row["message_id"]
            if message_id not in part_index:
                part_index[message_id] = 0

            content = json.loads(row["content"]) if row.get("content") else {}
            part = PartData(
                id=row["id"],
                message_id=message_id,
                type=row["type"],
                content=content,
                index=part_index[message_id],
            )
            storage.save_part(part)
            part_index[message_id] += 1

        # Migrate context blocks
        cursor = conn.execute("SELECT * FROM context_blocks")
        for row in cursor:
            embedding = None
            if row.get("embedding"):
                try:
                    embedding = json.loads(row["embedding"])
                except json.JSONDecodeError:
                    pass

            block = ContextBlockData(
                id=row["id"],
                session_id=row["session_id"],
                task_id=row.get("task_id"),
                task_description=row.get("task_description", ""),
                summary=row.get("summary", ""),
                content=row.get("content", ""),
                tokens=row.get("tokens", 0),
                embedding=embedding,
                created_at=datetime.fromisoformat(row["created_at"])
                    if row["created_at"] else datetime.now(),
            )
            storage.save_context_block(block)

        conn.close()
        logger.info("SQLite to JSON migration completed successfully")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False
