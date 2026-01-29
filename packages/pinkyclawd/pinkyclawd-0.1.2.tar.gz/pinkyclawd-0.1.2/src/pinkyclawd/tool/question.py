"""
Question tool for asking user questions.
"""

from __future__ import annotations

from typing import Any

from pinkyclawd.tool.base import (
    Tool,
    ToolContext,
    ToolResult,
    make_schema,
    STRING_PARAM,
    BOOLEAN_PARAM,
    ARRAY_PARAM,
)


class QuestionTool(Tool):
    """Ask the user questions during execution."""

    @property
    def name(self) -> str:
        return "question"

    @property
    def description(self) -> str:
        return """Ask the user questions during execution.

Use this to:
- Gather user preferences or requirements
- Clarify ambiguous instructions
- Get decisions on implementation choices
- Offer choices about direction

Options include a "Type your own answer" option by default.
Set multiple=true to allow selecting multiple choices."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                (
                    "questions",
                    "Questions to ask",
                    {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question": {
                                    "type": "string",
                                    "description": "Complete question text",
                                },
                                "header": {
                                    "type": "string",
                                    "description": "Short label (max 30 chars)",
                                    "maxLength": 30,
                                },
                                "multiple": {
                                    "type": "boolean",
                                    "description": "Allow multiple selections",
                                },
                                "options": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "label": {
                                                "type": "string",
                                                "description": "Display text (1-5 words)",
                                            },
                                            "description": {
                                                "type": "string",
                                                "description": "Explanation of choice",
                                            },
                                        },
                                        "required": ["label", "description"],
                                    },
                                },
                            },
                            "required": ["question", "header", "options"],
                        },
                    },
                ),
            ],
        )

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Ask questions (UI will handle display)."""
        questions = kwargs.get("questions", [])

        if not questions:
            return ToolResult.fail("No questions provided")

        # In the full implementation, this would trigger UI interaction
        # For now, return questions for the UI layer to handle
        return ToolResult.ok(
            "Questions submitted to user",
            questions=questions,
            awaiting_response=True,
        )
