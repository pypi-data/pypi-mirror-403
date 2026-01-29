"""
Skill system for PinkyClawd.

Provides specialized instruction sets for common workflows.
Supports automatic discovery of SKILL.md files from:
- .claude/skills/ directories (project and global)
- .opencode/skill/ and .opencode/skills/ directories
"""

from pinkyclawd.skill.loader import (
    discover_and_load_skills,
    discover_skill_md_files,
    load_skill_from_file,
    load_skill_md,
    register_discovered_skills,
)
from pinkyclawd.skill.registry import (
    Skill,
    SkillRegistry,
    get_skill_registry,
)

__all__ = [
    "Skill",
    "SkillRegistry",
    "get_skill_registry",
    "load_skill_from_file",
    "load_skill_md",
    "discover_skill_md_files",
    "discover_and_load_skills",
    "register_discovered_skills",
]
