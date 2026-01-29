"""
OAuth2 token storage and management.
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Optional encryption support
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


@dataclass
class OAuth2Token:
    """OAuth2 token with metadata."""

    access_token: str
    token_type: str = "Bearer"
    refresh_token: str | None = None
    expires_at: datetime | None = None
    scope: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        if not self.expires_at:
            return False
        # Consider expired 5 minutes before actual expiry
        return datetime.now() > self.expires_at - timedelta(minutes=5)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        d = {
            "access_token": self.access_token,
            "token_type": self.token_type,
        }
        if self.refresh_token:
            d["refresh_token"] = self.refresh_token
        if self.expires_at:
            d["expires_at"] = self.expires_at.isoformat()
        if self.scope:
            d["scope"] = self.scope
        if self.extra:
            d["extra"] = self.extra
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> OAuth2Token:
        """Create from dictionary."""
        expires_at = None
        if "expires_at" in d:
            expires_at = datetime.fromisoformat(d["expires_at"])
        elif "expires_in" in d:
            expires_at = datetime.now() + timedelta(seconds=d["expires_in"])

        return cls(
            access_token=d["access_token"],
            token_type=d.get("token_type", "Bearer"),
            refresh_token=d.get("refresh_token"),
            expires_at=expires_at,
            scope=d.get("scope"),
            extra=d.get("extra", {}),
        )

    def authorization_header(self) -> str:
        """Get the Authorization header value."""
        return f"{self.token_type} {self.access_token}"


class TokenStore:
    """
    Secure storage for OAuth2 tokens.

    Stores tokens in a JSON file with optional encryption.
    """

    def __init__(self, path: Path | None = None, encrypt: bool = True) -> None:
        if path is None:
            path = get_default_token_path()
        self.path = path
        self.encrypt = encrypt and CRYPTO_AVAILABLE
        self._tokens: dict[str, OAuth2Token] = {}
        self._key: bytes | None = None
        self._load()

    def _get_encryption_key(self) -> bytes:
        """Get or derive the encryption key."""
        if self._key:
            return self._key

        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography package not installed")

        # Derive key from machine-specific information
        key_material = (
            os.getlogin() + str(Path.home()) + "pinkyclawd-token-store"
        ).encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"pinkyclawd-salt-v1",
            iterations=100000,
        )
        self._key = base64.urlsafe_b64encode(kdf.derive(key_material))
        return self._key

    def _encrypt(self, data: str) -> str:
        """Encrypt data."""
        if not self.encrypt:
            return data

        key = self._get_encryption_key()
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()

    def _decrypt(self, data: str) -> str:
        """Decrypt data."""
        if not self.encrypt:
            return data

        key = self._get_encryption_key()
        f = Fernet(key)
        return f.decrypt(data.encode()).decode()

    def _load(self) -> None:
        """Load tokens from file."""
        if not self.path.exists():
            return

        try:
            with open(self.path) as f:
                data = json.load(f)

            # Handle encrypted data
            if isinstance(data, str):
                data = json.loads(self._decrypt(data))

            for name, token_data in data.items():
                self._tokens[name] = OAuth2Token.from_dict(token_data)

        except Exception:
            # If loading fails, start fresh
            self._tokens = {}

    def _save(self) -> None:
        """Save tokens to file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)

        data = {name: token.to_dict() for name, token in self._tokens.items()}
        json_data = json.dumps(data)

        if self.encrypt:
            json_data = json.dumps(self._encrypt(json_data))

        with open(self.path, "w") as f:
            f.write(json_data)

        # Set restrictive permissions
        os.chmod(self.path, 0o600)

    def get(self, name: str) -> OAuth2Token | None:
        """Get a token by name."""
        return self._tokens.get(name)

    def set(self, name: str, token: OAuth2Token) -> None:
        """Store a token."""
        self._tokens[name] = token
        self._save()

    def delete(self, name: str) -> bool:
        """Delete a token."""
        if name in self._tokens:
            del self._tokens[name]
            self._save()
            return True
        return False

    def list(self) -> list[str]:
        """List all token names."""
        return list(self._tokens.keys())

    def clear(self) -> None:
        """Clear all tokens."""
        self._tokens = {}
        self._save()


def get_default_token_path() -> Path:
    """Get the default path for token storage."""
    config_dir = Path.home() / ".config" / "pinkyclawd"
    return config_dir / "tokens.json"


# Global token store
_store: TokenStore | None = None


def get_token_store() -> TokenStore:
    """Get the global token store."""
    global _store
    if _store is None:
        _store = TokenStore()
    return _store
