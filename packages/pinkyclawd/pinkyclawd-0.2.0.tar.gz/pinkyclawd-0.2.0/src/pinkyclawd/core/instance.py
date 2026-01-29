"""
Project instance management for PinkyClawd.

Manages the current project context, including:
- Working directory and project root
- Project-specific configuration
- Session context
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class ProjectContext:
    """Context for the current project."""

    # Project paths
    root_path: Path
    config_path: Path | None = None

    # Project configuration
    project_config: dict[str, Any] = field(default_factory=dict)

    # Current session
    session_id: str | None = None

    # Project metadata
    name: str = ""
    git_root: Path | None = None

    @property
    def has_config(self) -> bool:
        """Check if project has local configuration."""
        return self.config_path is not None and self.config_path.exists()

    @property
    def is_git_repo(self) -> bool:
        """Check if project is a git repository."""
        return self.git_root is not None

    def get_relative_path(self, path: Path | str) -> Path:
        """Get path relative to project root."""
        path = Path(path)
        try:
            return path.relative_to(self.root_path)
        except ValueError:
            return path


class ProjectInstance:
    """
    Manages the current project instance.

    Thread-safe singleton that tracks the current working project
    and provides access to project-specific state.
    """

    _instance: ProjectInstance | None = None
    _lock: Lock = Lock()

    def __new__(cls) -> ProjectInstance:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._context: ProjectContext | None = None
        self._initialized = True

    @property
    def context(self) -> ProjectContext | None:
        """Get the current project context."""
        return self._context

    @property
    def is_active(self) -> bool:
        """Check if a project is currently active."""
        return self._context is not None

    def initialize(self, path: Path | str | None = None) -> ProjectContext:
        """
        Initialize the project context.

        Args:
            path: Project root path (defaults to current directory)

        Returns:
            The initialized ProjectContext
        """
        if path is None:
            path = Path.cwd()
        else:
            path = Path(path).resolve()

        # Find git root if in a git repo
        git_root = self._find_git_root(path)

        # Find project config
        config_path = self._find_project_config(path)

        # Load project config if exists
        project_config = {}
        if config_path and config_path.exists():
            project_config = self._load_project_config(config_path)

        # Determine project name
        name = project_config.get("name", path.name)

        self._context = ProjectContext(
            root_path=path,
            config_path=config_path,
            project_config=project_config,
            name=name,
            git_root=git_root,
        )

        logger.info(f"Initialized project: {name} at {path}")
        return self._context

    def set_session(self, session_id: str) -> None:
        """Set the current session ID."""
        if self._context:
            self._context.session_id = session_id
            logger.debug(f"Set session: {session_id}")

    def clear_session(self) -> None:
        """Clear the current session."""
        if self._context:
            self._context.session_id = None

    def close(self) -> None:
        """Close the current project instance."""
        if self._context:
            logger.info(f"Closing project: {self._context.name}")
            self._context = None

    def _find_git_root(self, path: Path) -> Path | None:
        """Find the git root directory."""
        current = path
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        return None

    def _find_project_config(self, path: Path) -> Path | None:
        """Find the project config file."""
        config_dir = path / ".pinkyclawd"
        if config_dir.is_dir():
            config_file = config_dir / "pinkyclawd.json"
            if config_file.exists():
                return config_file
        return None

    def _load_project_config(self, config_path: Path) -> dict[str, Any]:
        """Load project configuration."""
        import json

        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load project config: {e}")
            return {}

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.close()
                cls._instance._initialized = False
            cls._instance = None


def get_project_instance() -> ProjectInstance:
    """Get the global project instance."""
    return ProjectInstance()


def get_project_context() -> ProjectContext | None:
    """Get the current project context."""
    return get_project_instance().context


def initialize_project(path: Path | str | None = None) -> ProjectContext:
    """Initialize the project context."""
    return get_project_instance().initialize(path)
