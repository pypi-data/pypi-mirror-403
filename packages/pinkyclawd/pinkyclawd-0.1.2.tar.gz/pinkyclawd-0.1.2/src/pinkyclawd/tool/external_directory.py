"""
External directory access control.

Provides utilities to check if a file path is outside the project
directory and request permission for access.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pinkyclawd.tool.base import ToolContext


def get_project_root() -> Path:
    """
    Get the project root directory.

    Looks for common project markers (.git, pyproject.toml, package.json)
    starting from the current directory and walking up.

    Returns:
        Project root or current working directory if no markers found
    """
    markers = [".git", "pyproject.toml", "package.json", ".opencode", ".claude"]
    current = Path.cwd().resolve()

    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent

    return Path.cwd().resolve()


def is_within_project(path: str | Path) -> bool:
    """
    Check if a path is within the project root.

    Args:
        path: Path to check

    Returns:
        True if path is within project, False otherwise
    """
    try:
        target = Path(path).resolve()
        root = get_project_root()
        return target == root or root in target.parents
    except (OSError, ValueError):
        return False


async def assert_external_directory(
    ctx: ToolContext,
    target: str | None,
    bypass: bool = False,
    kind: Literal["file", "directory"] = "file",
) -> None:
    """
    Assert that external directory access is permitted.

    If the target path is outside the project directory, this will
    request permission from the user.

    Args:
        ctx: Tool execution context
        target: Target path to check
        bypass: If True, skip the check
        kind: Whether target is a file or directory

    Raises:
        PermissionError: If access is denied
    """
    if not target:
        return

    if bypass:
        return

    if is_within_project(target):
        return

    # Get the parent directory for permission scope
    target_path = Path(target)
    if kind == "directory":
        parent_dir = target_path
    else:
        parent_dir = target_path.parent

    # Request permission
    if ctx.on_permission_request:
        prompt = (
            f"Access to path outside project directory:\n"
            f"  Path: {target}\n"
            f"  Parent directory: {parent_dir}\n\n"
            f"Allow access?"
        )
        allowed = await ctx.on_permission_request("external_directory", prompt)

        if not allowed:
            raise PermissionError(
                f"Access denied to external path: {target}"
            )


def check_external_path(path: str | Path) -> dict:
    """
    Check if a path is external and return info about it.

    Args:
        path: Path to check

    Returns:
        Dictionary with path info including whether it's external
    """
    target = Path(path).resolve()
    root = get_project_root()

    return {
        "path": str(target),
        "is_external": not is_within_project(target),
        "project_root": str(root),
        "parent_dir": str(target.parent),
    }
