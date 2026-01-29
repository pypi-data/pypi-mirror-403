"""
Session sharing functionality.

Generates shareable URLs and handles session sharing configuration.
"""

from __future__ import annotations

import json
import uuid
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal

from pinkyclawd.config.settings import get_config
from pinkyclawd.config.storage import Session, Message, get_storage

logger = logging.getLogger(__name__)


@dataclass
class ShareConfig:
    """Configuration for a shared session."""

    share_id: str
    session_id: str
    created_at: datetime
    expires_at: datetime | None = None
    access_level: Literal["read", "fork"] = "read"
    password_hash: str | None = None
    view_count: int = 0
    max_views: int | None = None

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def is_view_limited(self) -> bool:
        if self.max_views is None:
            return False
        return self.view_count >= self.max_views

    def to_dict(self) -> dict[str, Any]:
        return {
            "share_id": self.share_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "access_level": self.access_level,
            "view_count": self.view_count,
            "max_views": self.max_views,
        }


@dataclass
class ShareResult:
    """Result of creating a share link."""

    success: bool
    url: str | None = None
    share_id: str | None = None
    error: str | None = None


class SessionSharer:
    """
    Handles session sharing operations.

    Creates shareable links and manages share configurations.
    """

    def __init__(self) -> None:
        self._storage = get_storage()
        self._shares: dict[str, ShareConfig] = {}

    def create_share(
        self,
        session_id: str,
        expires_in: timedelta | None = None,
        access_level: Literal["read", "fork"] = "read",
        password: str | None = None,
        max_views: int | None = None,
    ) -> ShareResult:
        """
        Create a shareable link for a session.

        Args:
            session_id: Session to share
            expires_in: Time until link expires
            access_level: Read-only or allow forking
            password: Optional password protection
            max_views: Optional view limit

        Returns:
            ShareResult with URL
        """
        config = get_config()

        # Check if sharing is enabled
        if config.share == "disabled":
            return ShareResult(
                success=False,
                error="Session sharing is disabled in configuration",
            )

        # Verify session exists
        session = self._storage.get_session(session_id)
        if not session:
            return ShareResult(
                success=False,
                error=f"Session {session_id} not found",
            )

        # Generate share ID
        share_id = self._generate_share_id(session_id)

        # Calculate expiration
        expires_at = None
        if expires_in:
            expires_at = datetime.now() + expires_in

        # Hash password if provided
        password_hash = None
        if password:
            password_hash = self._hash_password(password)

        # Create share config
        share_config = ShareConfig(
            share_id=share_id,
            session_id=session_id,
            created_at=datetime.now(),
            expires_at=expires_at,
            access_level=access_level,
            password_hash=password_hash,
            max_views=max_views,
        )

        self._shares[share_id] = share_config

        # Store in session metadata
        session.metadata["share_id"] = share_id
        session.metadata["shared_at"] = datetime.now().isoformat()
        self._storage.update_session(session)

        # Generate URL
        base_url = config.server.get("share_base_url", "https://pinkyclawd.dev/share")
        url = f"{base_url}/{share_id}"

        logger.info(f"Created share link for session {session_id}: {share_id}")

        return ShareResult(
            success=True,
            url=url,
            share_id=share_id,
        )

    def get_shared_session(
        self,
        share_id: str,
        password: str | None = None,
    ) -> tuple[Session | None, list[Message] | None, str | None]:
        """
        Get a shared session by share ID.

        Args:
            share_id: Share ID from URL
            password: Password if required

        Returns:
            Tuple of (session, messages, error)
        """
        share_config = self._shares.get(share_id)
        if not share_config:
            return None, None, "Share link not found or expired"

        # Check expiration
        if share_config.is_expired():
            return None, None, "Share link has expired"

        # Check view limit
        if share_config.is_view_limited():
            return None, None, "Share link view limit reached"

        # Check password
        if share_config.password_hash:
            if not password:
                return None, None, "Password required"
            if self._hash_password(password) != share_config.password_hash:
                return None, None, "Invalid password"

        # Get session and messages
        session = self._storage.get_session(share_config.session_id)
        if not session:
            return None, None, "Session no longer exists"

        messages = self._storage.get_messages(share_config.session_id)

        # Increment view count
        share_config.view_count += 1

        return session, messages, None

    def revoke_share(self, share_id: str) -> bool:
        """Revoke a share link."""
        if share_id in self._shares:
            config = self._shares.pop(share_id)

            # Remove from session metadata
            session = self._storage.get_session(config.session_id)
            if session:
                session.metadata.pop("share_id", None)
                session.metadata.pop("shared_at", None)
                self._storage.update_session(session)

            logger.info(f"Revoked share link {share_id}")
            return True

        return False

    def list_shares(self, session_id: str | None = None) -> list[ShareConfig]:
        """List all shares, optionally filtered by session."""
        shares = list(self._shares.values())
        if session_id:
            shares = [s for s in shares if s.session_id == session_id]
        return shares

    def _generate_share_id(self, session_id: str) -> str:
        """Generate a unique share ID."""
        unique = f"{session_id}:{uuid.uuid4().hex}:{datetime.now().isoformat()}"
        hash_val = hashlib.sha256(unique.encode()).hexdigest()
        return hash_val[:12]

    def _hash_password(self, password: str) -> str:
        """Hash a password for storage."""
        return hashlib.sha256(password.encode()).hexdigest()


# Global sharer instance
_sharer: SessionSharer | None = None


def get_sharer() -> SessionSharer:
    """Get the global session sharer."""
    global _sharer
    if _sharer is None:
        _sharer = SessionSharer()
    return _sharer


def create_share_url(
    session_id: str,
    expires_in_hours: int | None = None,
) -> ShareResult:
    """
    Create a shareable URL for a session.

    Args:
        session_id: Session to share
        expires_in_hours: Hours until expiration

    Returns:
        ShareResult with URL
    """
    expires_in = None
    if expires_in_hours:
        expires_in = timedelta(hours=expires_in_hours)

    return get_sharer().create_share(session_id, expires_in=expires_in)
