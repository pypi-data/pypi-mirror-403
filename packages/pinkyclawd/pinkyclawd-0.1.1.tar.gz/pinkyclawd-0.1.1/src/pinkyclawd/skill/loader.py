"""
Skill loader for loading skills from files.

Supports:
- JSON, YAML, and Markdown skill files
- SKILL.md discovery (Claude Code / OpenCode compatible)
- Frontmatter-based metadata parsing
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml

from pinkyclawd.skill.registry import Skill, get_skill_registry

logger = logging.getLogger(__name__)


def load_skill_from_file(path: str | Path) -> Skill | None:
    """
    Load a skill from a file.

    Supports JSON, YAML, and Markdown formats.

    Args:
        path: Path to the skill file

    Returns:
        Loaded skill or None if failed
    """
    path = Path(path)

    if not path.exists():
        return None

    try:
        content = path.read_text()

        if path.suffix == ".json":
            return _load_json_skill(content)
        elif path.suffix in (".yaml", ".yml"):
            return _load_yaml_skill(content)
        elif path.suffix == ".md":
            return _load_markdown_skill(content, path.stem)
        else:
            return None

    except Exception:
        return None


def _load_json_skill(content: str) -> Skill | None:
    """Load a skill from JSON."""
    data = json.loads(content)
    return _skill_from_dict(data)


def _load_yaml_skill(content: str) -> Skill | None:
    """Load a skill from YAML."""
    try:
        data = yaml.safe_load(content)
        return _skill_from_dict(data)
    except yaml.YAMLError:
        return None


def _load_markdown_skill(content: str, name: str) -> Skill | None:
    """
    Load a skill from Markdown.

    Format:
    ```
    # Skill Name

    Description line

    ---

    Instructions content...
    ```
    """
    lines = content.split("\n")

    # Find title
    title = name
    description = ""
    instructions_start = 0

    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.strip() == "---":
            instructions_start = i + 1
            break
        elif line.strip() and not description:
            description = line.strip()

    # Get instructions
    instructions = "\n".join(lines[instructions_start:]).strip()

    if not instructions:
        instructions = content

    return Skill(
        name=name,
        description=description or f"Skill: {title}",
        instructions=instructions,
    )


def _skill_from_dict(data: dict[str, Any]) -> Skill | None:
    """Create a skill from a dictionary."""
    if not isinstance(data, dict):
        return None

    name = data.get("name")
    description = data.get("description", "")
    instructions = data.get("instructions", "")

    if not name or not instructions:
        return None

    return Skill(
        name=name,
        description=description,
        instructions=instructions,
        args_description=data.get("args_description"),
    )


def load_skills_from_directory(directory: str | Path) -> list[Skill]:
    """
    Load all skills from a directory.

    Args:
        directory: Directory containing skill files

    Returns:
        List of loaded skills
    """
    directory = Path(directory)
    skills = []

    if not directory.exists():
        return skills

    for path in directory.iterdir():
        if path.is_file() and path.suffix in (".json", ".yaml", ".yml", ".md"):
            skill = load_skill_from_file(path)
            if skill:
                skills.append(skill)

    return skills


def register_skills_from_directory(directory: str | Path) -> int:
    """
    Load and register all skills from a directory.

    Args:
        directory: Directory containing skill files

    Returns:
        Number of skills registered
    """
    skills = load_skills_from_directory(directory)
    registry = get_skill_registry()

    for skill in skills:
        registry.register(skill)

    return len(skills)


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with optional frontmatter

    Returns:
        Tuple of (frontmatter dict, body content)
    """
    # Check for frontmatter delimiter
    match = re.match(r"^---\r?\n([\s\S]*?)\r?\n---\r?\n?", content)
    if not match:
        return {}, content

    frontmatter_text = match.group(1)
    body = content[match.end() :]

    # Preprocess frontmatter to handle colons in values
    lines = frontmatter_text.split("\n")
    result: list[str] = []

    for line in lines:
        # Skip comments and empty lines
        if line.strip().startswith("#") or line.strip() == "":
            result.append(line)
            continue

        # Skip continuation lines (indented)
        if re.match(r"^\s+", line):
            result.append(line)
            continue

        # Match key: value pattern
        kv_match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$", line)
        if not kv_match:
            result.append(line)
            continue

        key = kv_match.group(1)
        value = kv_match.group(2).strip()

        # Skip if value is empty, already quoted, or uses block scalar
        if value in ("", ">", "|") or value.startswith('"') or value.startswith("'"):
            result.append(line)
            continue

        # If value contains a colon, convert to block scalar
        if ":" in value:
            result.append(f"{key}: |")
            result.append(f"  {value}")
            continue

        result.append(line)

    processed = "\n".join(result)

    try:
        data = yaml.safe_load(processed) or {}
    except yaml.YAMLError:
        data = {}

    return data, body.strip()


def load_skill_md(path: str | Path) -> Skill | None:
    """
    Load a skill from a SKILL.md file with frontmatter.

    Expected format:
    ```
    ---
    name: skill-name
    description: Short description of the skill
    ---

    Skill instructions go here...
    ```

    Args:
        path: Path to the SKILL.md file

    Returns:
        Loaded skill or None if failed
    """
    path = Path(path)

    if not path.exists():
        return None

    try:
        content = path.read_text()
        data, body = _parse_frontmatter(content)

        name = data.get("name")
        description = data.get("description", "")

        if not name:
            # Try to derive name from directory
            name = path.parent.name

        if not name:
            logger.warning("SKILL.md missing name: %s", path)
            return None

        return Skill(
            name=name,
            description=description,
            instructions=body if body else content,
            location=str(path.absolute()),
        )

    except Exception as e:
        logger.error("Failed to load skill from %s: %s", path, e)
        return None


def _find_parent_directories(start: Path, stop: Path | None = None) -> list[Path]:
    """
    Find all parent directories from start up to stop.

    Args:
        start: Starting directory
        stop: Stop directory (exclusive), defaults to filesystem root

    Returns:
        List of directories from start to stop
    """
    directories: list[Path] = []
    current = start.resolve()

    if stop:
        stop = stop.resolve()

    while True:
        directories.append(current)
        parent = current.parent

        if parent == current:  # Reached filesystem root
            break

        if stop and current == stop:
            break

        current = parent

    return directories


def _find_git_root(start: Path) -> Path | None:
    """Find the git repository root from a starting directory."""
    current = start.resolve()

    while True:
        if (current / ".git").exists():
            return current

        parent = current.parent
        if parent == current:
            return None
        current = parent


def discover_skill_md_files(
    cwd: str | Path | None = None,
    include_global: bool = True,
) -> list[Path]:
    """
    Discover SKILL.md files in standard locations.

    Searches:
    - .claude/skills/ directories from cwd up to git root
    - .opencode/skill/ and .opencode/skills/ directories
    - ~/.claude/skills/ (global, if include_global is True)

    Args:
        cwd: Current working directory (defaults to os.getcwd())
        include_global: Whether to include global ~/.claude/skills/

    Returns:
        List of paths to discovered SKILL.md files
    """
    if cwd is None:
        cwd = Path.cwd()
    else:
        cwd = Path(cwd)

    git_root = _find_git_root(cwd)
    skill_files: list[Path] = []

    # Collect directories to scan
    scan_dirs: list[Path] = []

    # Add .claude directories from cwd up to git root
    for parent in _find_parent_directories(cwd, git_root):
        claude_dir = parent / ".claude"
        if claude_dir.is_dir():
            scan_dirs.append(claude_dir)

        opencode_dir = parent / ".opencode"
        if opencode_dir.is_dir():
            scan_dirs.append(opencode_dir)

    # Add global ~/.claude directory
    if include_global:
        global_claude = Path.home() / ".claude"
        if global_claude.is_dir():
            scan_dirs.append(global_claude)

    # Scan for SKILL.md files
    for base_dir in scan_dirs:
        # Check .claude/skills/ pattern
        for skill_dir in ["skills", "skill"]:
            skills_path = base_dir / skill_dir
            if skills_path.is_dir():
                # Recursively find all SKILL.md files
                for skill_file in skills_path.rglob("SKILL.md"):
                    if skill_file.is_file():
                        skill_files.append(skill_file)

    return skill_files


def discover_and_load_skills(
    cwd: str | Path | None = None,
    include_global: bool = True,
) -> dict[str, Skill]:
    """
    Discover and load all SKILL.md files from standard locations.

    Args:
        cwd: Current working directory
        include_global: Whether to include global skills

    Returns:
        Dictionary mapping skill names to Skill objects
    """
    skill_files = discover_skill_md_files(cwd, include_global)
    skills: dict[str, Skill] = {}

    for skill_file in skill_files:
        skill = load_skill_md(skill_file)
        if skill is None:
            continue

        # Check for duplicates
        if skill.name in skills:
            existing = skills[skill.name]
            logger.warning(
                "Duplicate skill name '%s': existing at %s, duplicate at %s",
                skill.name,
                getattr(existing, "location", "unknown"),
                skill.location,
            )
            continue

        skills[skill.name] = skill

    return skills


def register_discovered_skills(
    cwd: str | Path | None = None,
    include_global: bool = True,
) -> int:
    """
    Discover and register all SKILL.md files from standard locations.

    Args:
        cwd: Current working directory
        include_global: Whether to include global skills

    Returns:
        Number of skills registered
    """
    skills = discover_and_load_skills(cwd, include_global)
    registry = get_skill_registry()

    for skill in skills.values():
        registry.register(skill)

    return len(skills)
