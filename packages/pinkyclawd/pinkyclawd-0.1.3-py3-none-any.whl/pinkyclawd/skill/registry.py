"""
Skill registry for managing skills.
"""

from __future__ import annotations

from dataclasses import dataclass

from pinkyclawd.skill.builtins import BUILTIN_SKILLS


@dataclass
class Skill:
    """A skill that provides specialized instructions."""

    name: str
    description: str
    instructions: str
    args_description: str | None = None
    location: str | None = None  # Path to skill file for discovered skills

    def get_instructions(self, args: str = "") -> str:
        """
        Get the skill instructions with optional argument substitution.

        Args:
            args: Optional arguments to substitute

        Returns:
            The skill instructions
        """
        if args and "{args}" in self.instructions:
            return self.instructions.replace("{args}", args)
        return self.instructions


class SkillRegistry:
    """
    Registry for all available skills.

    Manages built-in and custom skills, with automatic discovery
    of SKILL.md files from standard locations.
    """

    def __init__(self, auto_discover: bool = True) -> None:
        """
        Initialize the skill registry.

        Args:
            auto_discover: Whether to automatically discover SKILL.md files
        """
        self._skills: dict[str, Skill] = {}
        self._discovered: bool = False
        self._register_builtins()
        if auto_discover:
            self.discover_skills()

    def _register_builtins(self) -> None:
        """Register built-in skills."""
        for name, skill_data in BUILTIN_SKILLS.items():
            self._skills[name] = Skill(
                name=name,
                description=skill_data["description"],
                instructions=skill_data["instructions"],
                args_description=skill_data.get("args_description"),
            )

    def discover_skills(self, cwd: str | None = None, include_global: bool = True) -> int:
        """
        Discover and register SKILL.md files from standard locations.

        Searches:
        - .claude/skills/ directories from cwd up to git root
        - .opencode/skill/ and .opencode/skills/ directories
        - ~/.claude/skills/ (global, if include_global is True)

        Args:
            cwd: Current working directory (defaults to os.getcwd())
            include_global: Whether to include global ~/.claude/skills/

        Returns:
            Number of skills discovered and registered
        """
        # Import here to avoid circular imports
        from pinkyclawd.skill.loader import discover_and_load_skills

        skills = discover_and_load_skills(cwd, include_global)
        count = 0

        for skill in skills.values():
            # Don't overwrite built-in skills
            if skill.name not in self._skills:
                self._skills[skill.name] = skill
                count += 1

        self._discovered = True
        return count

    def register(self, skill: Skill) -> None:
        """Register a skill."""
        self._skills[skill.name] = skill

    def unregister(self, name: str) -> None:
        """Unregister a skill."""
        self._skills.pop(name, None)

    def get(self, name: str) -> Skill | None:
        """Get a skill by name."""
        return self._skills.get(name)

    def list_skills(self) -> list[str]:
        """List all skill names."""
        return list(self._skills.keys())

    def get_all(self) -> list[Skill]:
        """Get all skills."""
        return list(self._skills.values())


# Global registry
_registry: SkillRegistry | None = None


def get_skill_registry() -> SkillRegistry:
    """Get the global skill registry."""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry
