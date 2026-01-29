"""
Session manager for creating, loading, and managing sessions.

Handles session lifecycle including creation, forking, compaction,
and child session relationships.
"""

from __future__ import annotations

import uuid
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pinkyclawd.config.storage import (
    Session,
    Message,
    MessagePart,
    MessageRole,
    PartType,
    get_storage,
)
from pinkyclawd.events import (
    EventType,
    SessionEvent,
    get_event_bus,
    emit_session_created,
)
from pinkyclawd.rlm.context import get_context_manager
from pinkyclawd.rlm.archive import get_archiver

logger = logging.getLogger(__name__)


@dataclass
class SessionInfo:
    """Summary information about a session."""

    id: str
    title: str
    directory: str
    message_count: int
    created_at: datetime
    updated_at: datetime
    is_archived: bool
    parent_id: str | None = None
    child_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "directory": self.directory,
            "message_count": self.message_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_archived": self.is_archived,
            "parent_id": self.parent_id,
            "child_count": self.child_count,
        }


class SessionManager:
    """
    Manages session lifecycle and operations.

    Provides CRUD operations, forking, compaction, and session relationships.

    Note: This class is managed by the StateFactory. Use get_session_manager()
    from pinkyclawd.core to get the singleton instance.
    """

    def __init__(self) -> None:
        self._storage = get_storage()
        self._event_bus = get_event_bus()
        self._context_manager = get_context_manager()
        self._archiver = get_archiver()
        self._current_session_id: str | None = None

    @property
    def current_session_id(self) -> str | None:
        """Get the current active session ID."""
        return self._current_session_id

    def create(
        self,
        title: str = "New Session",
        directory: str | Path | None = None,
        parent_id: str | None = None,
    ) -> Session:
        """
        Create a new session.

        Args:
            title: Session title
            directory: Working directory for the session
            parent_id: Optional parent session for forking

        Returns:
            Created session
        """
        session_id = f"ses_{uuid.uuid4().hex[:12]}"

        session = Session(
            id=session_id,
            title=title,
            directory=str(directory) if directory else str(Path.cwd()),
            parent_id=parent_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self._storage.create_session(session)
        self._current_session_id = session_id

        # Emit event
        emit_session_created(session_id, title=title)

        logger.info(f"Created session {session_id}: {title}")
        return session

    def get(self, session_id: str) -> Session | None:
        """Get a session by ID."""
        return self._storage.get_session(session_id)

    def get_or_create(
        self,
        session_id: str | None = None,
        directory: str | Path | None = None,
    ) -> Session:
        """Get an existing session or create a new one."""
        if session_id:
            session = self.get(session_id)
            if session:
                self._current_session_id = session_id
                return session

        return self.create(directory=directory)

    def list(
        self,
        limit: int = 50,
        offset: int = 0,
        directory: str | None = None,
    ) -> list[SessionInfo]:
        """
        List sessions with summary information.

        Args:
            limit: Maximum sessions to return
            offset: Pagination offset
            directory: Filter by directory

        Returns:
            List of session info objects
        """
        sessions = self._storage.list_sessions(
            limit=limit,
            offset=offset,
            directory=directory,
        )

        result = []
        for session in sessions:
            messages = self._storage.get_messages(session.id)
            children = self._get_children(session.id)

            result.append(
                SessionInfo(
                    id=session.id,
                    title=session.title,
                    directory=session.directory,
                    message_count=len(messages),
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    is_archived=session.archived_at is not None,
                    parent_id=session.parent_id,
                    child_count=len(children),
                )
            )

        return result

    def update(
        self,
        session_id: str,
        title: str | None = None,
        directory: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Session | None:
        """Update session properties."""
        session = self._storage.get_session(session_id)
        if not session:
            return None

        if title is not None:
            session.title = title
        if directory is not None:
            session.directory = directory
        if metadata is not None:
            session.metadata.update(metadata)

        self._storage.update_session(session)

        # Emit event
        self._event_bus.emit_sync(
            SessionEvent(
                type=EventType.SESSION_UPDATED,
                data={"session_id": session_id},
            )
        )

        return session

    def delete(self, session_id: str) -> bool:
        """
        Delete a session and all its data.

        Args:
            session_id: Session to delete

        Returns:
            True if deleted
        """
        session = self._storage.get_session(session_id)
        if not session:
            return False

        # Delete child sessions first
        children = self._get_children(session_id)
        for child in children:
            self.delete(child.id)

        self._storage.delete_session(session_id)
        self._context_manager.reset_session(session_id)

        # Emit event
        self._event_bus.emit_sync(
            SessionEvent(
                type=EventType.SESSION_DELETED,
                data={"session_id": session_id},
            )
        )

        # Clear current session if deleted
        if self._current_session_id == session_id:
            self._current_session_id = None

        logger.info(f"Deleted session {session_id}")
        return True

    def fork(
        self,
        session_id: str,
        from_message_id: str | None = None,
        title: str | None = None,
    ) -> Session | None:
        """
        Fork a session from a specific point.

        Args:
            session_id: Session to fork
            from_message_id: Message to fork from (includes this message)
            title: Title for new session

        Returns:
            New forked session
        """
        parent = self._storage.get_session(session_id)
        if not parent:
            return None

        messages = self._storage.get_messages(session_id)

        # Find messages up to fork point
        if from_message_id:
            fork_messages = []
            for msg in messages:
                fork_messages.append(msg)
                if msg.id == from_message_id:
                    break
        else:
            fork_messages = messages

        # Create new session
        fork_title = title or f"Fork of {parent.title}"
        new_session = self.create(
            title=fork_title,
            directory=parent.directory,
            parent_id=session_id,
        )

        # Copy messages
        for msg in fork_messages:
            new_msg = Message(
                id=f"msg_{uuid.uuid4().hex[:12]}",
                session_id=new_session.id,
                role=msg.role,
                parts=[
                    MessagePart(
                        id=f"part_{uuid.uuid4().hex[:12]}",
                        message_id="",  # Will be set below
                        type=part.type,
                        content=part.content.copy(),
                    )
                    for part in msg.parts
                ],
                metadata=msg.metadata.copy(),
            )
            # Fix message IDs in parts
            for part in new_msg.parts:
                part.message_id = new_msg.id

            self._storage.add_message(new_msg)

        logger.info(
            f"Forked session {session_id} to {new_session.id} with {len(fork_messages)} messages"
        )

        return new_session

    def compact(self, session_id: str) -> bool:
        """
        Compact a session by archiving old messages.

        Archives messages and removes them from active context.

        Args:
            session_id: Session to compact

        Returns:
            True if compaction performed
        """
        session = self._storage.get_session(session_id)
        if not session:
            return False

        # Emit compacting event
        self._event_bus.emit_sync(
            SessionEvent(
                type=EventType.SESSION_COMPACTING,
                data={"session_id": session_id},
            )
        )

        # Archive oldest messages
        result = self._archiver.archive_oldest(session_id)

        if result.success:
            logger.info(
                f"Compacted session {session_id}: "
                f"archived {result.messages_archived} messages "
                f"({result.tokens_archived} tokens)"
            )
            return True

        return False

    def rename(self, session_id: str, new_title: str) -> bool:
        """Rename a session."""
        session = self.update(session_id, title=new_title)
        return session is not None

    def archive(self, session_id: str) -> bool:
        """Mark a session as archived."""
        session = self._storage.get_session(session_id)
        if not session:
            return False

        session.archived_at = datetime.now()
        self._storage.update_session(session)
        return True

    def unarchive(self, session_id: str) -> bool:
        """Unarchive a session."""
        session = self._storage.get_session(session_id)
        if not session:
            return False

        session.archived_at = None
        self._storage.update_session(session)
        return True

    def get_messages(self, session_id: str) -> list[Message]:
        """Get all messages for a session."""
        return self._storage.get_messages(session_id)

    def add_message(self, session_id: str, message: Message) -> Message:
        """Add a message to a session."""
        message.session_id = session_id
        self._storage.add_message(message)

        # Update context manager
        self._context_manager.add_message(session_id, message)

        # Update session timestamp
        session = self._storage.get_session(session_id)
        if session:
            session.updated_at = datetime.now()
            self._storage.update_session(session)

        return message

    def set_current(self, session_id: str) -> bool:
        """Set the current active session."""
        session = self._storage.get_session(session_id)
        if session:
            self._current_session_id = session_id
            return True
        return False

    def _get_children(self, session_id: str) -> list[Session]:
        """Get child sessions of a parent."""
        all_sessions = self._storage.list_sessions(limit=1000)
        return [s for s in all_sessions if s.parent_id == session_id]

def get_session_manager() -> SessionManager:
    """
    Get the global session manager.

    Prefer using pinkyclawd.core.get_session_manager() for consistency.
    """
    from pinkyclawd.core.state import get_state_factory
    return get_state_factory().session_manager


# Convenience functions


def create_session(
    title: str = "New Session",
    directory: str | Path | None = None,
) -> Session:
    """Create a new session."""
    return get_session_manager().create(title=title, directory=directory)


def get_session(session_id: str) -> Session | None:
    """Get a session by ID."""
    return get_session_manager().get(session_id)


def list_sessions(
    limit: int = 50,
    directory: str | None = None,
) -> list[SessionInfo]:
    """List sessions."""
    return get_session_manager().list(limit=limit, directory=directory)


def delete_session(session_id: str) -> bool:
    """Delete a session."""
    return get_session_manager().delete(session_id)


def fork_session(
    session_id: str,
    from_message_id: str | None = None,
) -> Session | None:
    """Fork a session."""
    return get_session_manager().fork(session_id, from_message_id)
