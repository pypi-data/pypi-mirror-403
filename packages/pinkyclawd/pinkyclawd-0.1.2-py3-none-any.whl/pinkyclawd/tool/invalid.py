"""
Invalid tool for handling tool argument validation errors.

This tool is invoked when a tool call has invalid arguments,
providing a standardized error response to the AI.
"""

from __future__ import annotations

from typing import Any

from pinkyclawd.tool.base import (
    Tool,
    ToolContext,
    ToolResult,
    make_schema,
    STRING_PARAM,
)


class InvalidTool(Tool):
    """
    Tool for handling invalid tool arguments.

    This is not meant to be called directly by the AI, but is used
    internally when tool arguments fail validation.
    """

    @property
    def name(self) -> str:
        return "invalid"

    @property
    def description(self) -> str:
        return "Do not use - internal error handling"

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                ("tool", "The tool that had invalid arguments", STRING_PARAM),
                ("error", "The validation error message", STRING_PARAM),
            ],
        )

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Return an error message for invalid tool arguments."""
        tool_name = kwargs.get("tool", "unknown")
        error = kwargs.get("error", "Unknown validation error")

        return ToolResult.fail(
            error=f"Invalid arguments for tool '{tool_name}': {error}",
            output=f"The arguments provided to the tool are invalid: {error}",
        )
