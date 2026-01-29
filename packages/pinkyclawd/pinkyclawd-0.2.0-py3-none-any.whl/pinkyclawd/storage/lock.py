"""
File locking for concurrent access.

Provides cross-platform file locking for safe concurrent reads and writes.
"""

from __future__ import annotations

import os
import time
import logging
from pathlib import Path
from threading import Lock as ThreadLock
from contextlib import contextmanager
from typing import Iterator

logger = logging.getLogger(__name__)

# Try to import fcntl for Unix file locking
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

# Try to import msvcrt for Windows file locking
try:
    import msvcrt
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False


class FileLock:
    """
    Cross-platform file lock.

    Uses fcntl on Unix and msvcrt on Windows.
    Falls back to a simple lock file mechanism if neither is available.
    """

    def __init__(self, path: Path | str, timeout: float = 10.0) -> None:
        """
        Initialize the file lock.

        Args:
            path: Path to the file to lock
            timeout: Maximum time to wait for lock (seconds)
        """
        self._path = Path(path)
        self._lock_path = self._path.with_suffix(self._path.suffix + ".lock")
        self._timeout = timeout
        self._fd: int | None = None
        self._thread_lock = ThreadLock()
        self._acquired = False

    @contextmanager
    def acquire(self, exclusive: bool = True) -> Iterator[None]:
        """
        Context manager to acquire and release the lock.

        Args:
            exclusive: If True, acquire exclusive lock. If False, shared lock.

        Raises:
            TimeoutError: If lock cannot be acquired within timeout
        """
        self._acquire_lock(exclusive)
        try:
            yield
        finally:
            self._release_lock()

    def _acquire_lock(self, exclusive: bool) -> None:
        """Acquire the file lock."""
        start_time = time.time()

        # First acquire thread lock
        if not self._thread_lock.acquire(timeout=self._timeout):
            raise TimeoutError(f"Could not acquire thread lock for {self._path}")

        try:
            # Ensure parent directory exists
            self._lock_path.parent.mkdir(parents=True, exist_ok=True)

            # Open lock file
            flags = os.O_RDWR | os.O_CREAT
            self._fd = os.open(str(self._lock_path), flags)

            # Acquire file lock
            while True:
                try:
                    self._lock_file(exclusive)
                    self._acquired = True
                    return
                except (IOError, OSError):
                    elapsed = time.time() - start_time
                    if elapsed >= self._timeout:
                        raise TimeoutError(
                            f"Could not acquire file lock for {self._path} "
                            f"after {self._timeout}s"
                        )
                    time.sleep(0.01)

        except Exception:
            # Release thread lock on failure
            self._thread_lock.release()
            if self._fd is not None:
                os.close(self._fd)
                self._fd = None
            raise

    def _release_lock(self) -> None:
        """Release the file lock."""
        try:
            if self._fd is not None:
                self._unlock_file()
                os.close(self._fd)
                self._fd = None
                self._acquired = False
        finally:
            self._thread_lock.release()

    def _lock_file(self, exclusive: bool) -> None:
        """Lock the file using platform-specific method."""
        if self._fd is None:
            return

        if HAS_FCNTL:
            # Unix
            operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
            fcntl.flock(self._fd, operation | fcntl.LOCK_NB)
        elif HAS_MSVCRT:
            # Windows
            msvcrt.locking(self._fd, msvcrt.LK_NBLCK, 1)
        else:
            # Fallback: simple file existence check
            if self._lock_path.exists():
                # Check if lock is stale (older than 60 seconds)
                try:
                    age = time.time() - self._lock_path.stat().st_mtime
                    if age < 60:
                        raise IOError("Lock file exists")
                except FileNotFoundError:
                    pass
            # Touch lock file
            self._lock_path.touch()

    def _unlock_file(self) -> None:
        """Unlock the file using platform-specific method."""
        if self._fd is None:
            return

        if HAS_FCNTL:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
        elif HAS_MSVCRT:
            try:
                msvcrt.locking(self._fd, msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        else:
            # Fallback: remove lock file
            try:
                self._lock_path.unlink()
            except FileNotFoundError:
                pass


class LockManager:
    """
    Manages multiple file locks.

    Thread-safe lock management for the storage system.
    """

    def __init__(self, timeout: float = 10.0) -> None:
        self._timeout = timeout
        self._locks: dict[Path, FileLock] = {}
        self._manager_lock = ThreadLock()

    def get_lock(self, path: Path | str) -> FileLock:
        """Get or create a lock for a path."""
        path = Path(path)
        with self._manager_lock:
            if path not in self._locks:
                self._locks[path] = FileLock(path, self._timeout)
            return self._locks[path]

    @contextmanager
    def read_lock(self, path: Path | str) -> Iterator[None]:
        """Acquire a shared (read) lock on a path."""
        lock = self.get_lock(path)
        with lock.acquire(exclusive=False):
            yield

    @contextmanager
    def write_lock(self, path: Path | str) -> Iterator[None]:
        """Acquire an exclusive (write) lock on a path."""
        lock = self.get_lock(path)
        with lock.acquire(exclusive=True):
            yield

    def cleanup(self) -> None:
        """Clean up stale lock files."""
        with self._manager_lock:
            for lock in self._locks.values():
                if lock._lock_path.exists():
                    try:
                        age = time.time() - lock._lock_path.stat().st_mtime
                        if age > 60:  # Older than 60 seconds
                            lock._lock_path.unlink()
                    except (FileNotFoundError, OSError):
                        pass
            self._locks.clear()


# Global lock manager
_lock_manager: LockManager | None = None


def get_lock_manager() -> LockManager:
    """Get the global lock manager."""
    global _lock_manager
    if _lock_manager is None:
        _lock_manager = LockManager()
    return _lock_manager
