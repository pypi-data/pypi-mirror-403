"""
Path utilities for configuration and data directories.

Follows XDG Base Directory specification on Linux/macOS,
with fallbacks for Windows.
"""

from __future__ import annotations

import os
import platform
from pathlib import Path


def get_config_dir() -> Path:
    """
    Get the configuration directory.

    - Linux/macOS: ~/.config/pinkyclawd
    - Windows: %APPDATA%/pinkyclawd
    """
    if platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

    config_dir = base / "pinkyclawd"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_data_dir() -> Path:
    """
    Get the data directory (for sessions, database).

    - Linux/macOS: ~/.local/share/pinkyclawd
    - Windows: %LOCALAPPDATA%/pinkyclawd
    """
    if platform.system() == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    data_dir = base / "pinkyclawd"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_cache_dir() -> Path:
    """
    Get the cache directory.

    - Linux/macOS: ~/.cache/pinkyclawd
    - Windows: %LOCALAPPDATA%/pinkyclawd/cache
    """
    if platform.system() == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        cache_dir = base / "pinkyclawd" / "cache"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        cache_dir = base / "pinkyclawd"

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_project_config_path(project_dir: Path | str | None = None) -> Path | None:
    """
    Get the project-specific config file path.

    Searches for:
    1. <project>/pinkyclawd.json
    2. <project>/.pinkyclawd/pinkyclawd.json

    Returns None if no project config found.
    """
    if project_dir is None:
        project_dir = Path.cwd()
    else:
        project_dir = Path(project_dir)

    # Check direct config
    direct = project_dir / "pinkyclawd.json"
    if direct.exists():
        return direct

    # Check .pinkyclawd directory
    dotdir = project_dir / ".pinkyclawd" / "pinkyclawd.json"
    if dotdir.exists():
        return dotdir

    return None


def get_global_config_path() -> Path:
    """Get the global configuration file path."""
    return get_config_dir() / "pinkyclawd.json"


def get_database_path() -> Path:
    """Get the SQLite database path."""
    return get_data_dir() / "pinkyclawd.db"


def get_themes_dir() -> Path:
    """Get the custom themes directory."""
    themes_dir = get_config_dir() / "themes"
    themes_dir.mkdir(parents=True, exist_ok=True)
    return themes_dir


def get_commands_dir(project_dir: Path | str | None = None) -> Path | None:
    """Get the custom commands directory for a project."""
    if project_dir is None:
        project_dir = Path.cwd()
    else:
        project_dir = Path(project_dir)

    commands_dir = project_dir / ".pinkyclawd" / "commands"
    if commands_dir.exists():
        return commands_dir
    return None


def get_plugins_dir() -> Path:
    """Get the plugins directory."""
    plugins_dir = get_config_dir() / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    return plugins_dir


def get_logs_dir() -> Path:
    """Get the logs directory."""
    logs_dir = get_data_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir
