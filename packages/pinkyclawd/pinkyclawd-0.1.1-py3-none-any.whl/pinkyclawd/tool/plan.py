"""
Plan tools for switching between plan and build agents.
"""

from __future__ import annotations

from typing import Any

from pinkyclawd.tool.base import STRING_PARAM, Tool, ToolContext, ToolResult, make_schema


class PlanEnterTool(Tool):
    """Switch to plan mode for designing implementation."""

    @property
    def name(self) -> str:
        return "plan_enter"

    @property
    def description(self) -> str:
        return """Switch to plan mode to design an implementation approach.

Use this when:
- Starting a complex task that needs planning
- You need user approval before making changes
- The task requires architectural decisions
- There are multiple valid approaches to consider

In plan mode:
- Explore the codebase thoroughly
- Design your implementation approach
- Present the plan for user approval
- Use plan_exit when ready to implement"""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                (
                    "reason",
                    "Why you're entering plan mode (what needs planning)",
                    STRING_PARAM,
                ),
            ],
        )

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Enter plan mode."""
        reason = kwargs.get("reason", "")

        if not reason:
            return ToolResult.fail("No reason provided for entering plan mode")

        # The agent registry handles the actual mode switch
        # This tool signals the intent and returns context
        return ToolResult.ok(
            f"Entering plan mode.\n\nReason: {reason}\n\n"
            "You are now in plan mode. Focus on:\n"
            "1. Exploring the codebase to understand existing patterns\n"
            "2. Designing a clear implementation approach\n"
            "3. Identifying potential issues or tradeoffs\n"
            "4. Presenting the plan for user approval\n\n"
            "When ready, use plan_exit to return to build mode.",
            mode="plan",
            reason=reason,
            mode_switch=True,
        )


class PlanExitTool(Tool):
    """Exit plan mode and return to build mode."""

    @property
    def name(self) -> str:
        return "plan_exit"

    @property
    def description(self) -> str:
        return """Exit plan mode and return to build mode for implementation.

Use this after:
- You've explored the codebase
- Designed your implementation approach
- The user has approved the plan

Include a summary of the plan that was approved."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                (
                    "summary",
                    "Summary of the approved plan to implement",
                    STRING_PARAM,
                ),
            ],
            optional=[
                (
                    "approved",
                    "Whether the plan was approved (default: true)",
                    {"type": "boolean"},
                ),
            ],
        )

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Exit plan mode."""
        summary = kwargs.get("summary", "")
        approved = kwargs.get("approved", True)

        if not summary:
            return ToolResult.fail("No plan summary provided")

        if not approved:
            return ToolResult.ok(
                "Plan was not approved. Remaining in plan mode.\n\n"
                "Revise the plan based on feedback and try again.",
                mode="plan",
                approved=False,
                mode_switch=False,
            )

        return ToolResult.ok(
            f"Exiting plan mode.\n\n"
            f"Approved plan:\n{summary}\n\n"
            "You are now in build mode. Implement the approved plan.",
            mode="build",
            summary=summary,
            approved=True,
            mode_switch=True,
        )
