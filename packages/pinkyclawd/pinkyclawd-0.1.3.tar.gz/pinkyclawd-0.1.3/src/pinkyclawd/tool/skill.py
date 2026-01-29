"""
Skill tool for loading specialized skill instructions.
"""

from __future__ import annotations

from typing import Any

from pinkyclawd.tool.base import STRING_PARAM, Tool, ToolContext, ToolResult, make_schema


class SkillTool(Tool):
    """Load specialized skill instructions into the conversation."""

    @property
    def name(self) -> str:
        return "skill"

    @property
    def description(self) -> str:
        return """Load a specialized skill to get expert guidance.

Available skills:
- commit: Git commit workflow with best practices
- pr: Pull request creation and formatting
- review: Code review guidelines
- test: Test writing and running
- deploy: Deployment helpers
- refactor: Code refactoring patterns

Skills inject specialized instructions to help with specific workflows."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                ("name", "Name of the skill to load", STRING_PARAM),
            ],
            optional=[
                ("args", "Optional arguments for the skill", STRING_PARAM),
            ],
        )

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Load a skill."""
        skill_name = kwargs.get("name", "")
        args = kwargs.get("args", "")

        if not skill_name:
            return ToolResult.fail("No skill name provided")

        # Import skill registry
        try:
            from pinkyclawd.skill.registry import get_skill_registry

            registry = get_skill_registry()
            skill = registry.get(skill_name)

            if not skill:
                available = registry.list_skills()
                return ToolResult.fail(
                    f"Skill '{skill_name}' not found. "
                    f"Available: {', '.join(available)}"
                )

            # Load the skill instructions
            instructions = skill.get_instructions(args)

            return ToolResult.ok(
                f"Loaded skill: {skill_name}\n\n{instructions}",
                skill=skill_name,
                skill_loaded=True,
            )

        except ImportError:
            # Skill system not yet implemented - return stub
            return ToolResult.ok(
                f"Skill '{skill_name}' would be loaded here.\n\n"
                "Note: Skill system is being implemented.",
                skill=skill_name,
                skill_loaded=False,
                stub=True,
            )
