"""
Edit tool for search/replace operations on files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pinkyclawd.tool.base import (
    Tool,
    ToolContext,
    ToolResult,
    make_schema,
    STRING_PARAM,
    BOOLEAN_PARAM,
)


class EditTool(Tool):
    """Edit files using exact string replacement."""

    @property
    def name(self) -> str:
        return "edit"

    @property
    def description(self) -> str:
        return """Perform exact string replacements in files.

You MUST use the Read tool before editing to see exact content.
The oldString must match exactly (including whitespace/indentation).
The edit will FAIL if oldString is not found.
The edit will FAIL if oldString matches multiple times (provide more context).
Use replaceAll=true to replace all occurrences."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                ("filePath", "Absolute path to the file to modify", STRING_PARAM),
                ("oldString", "The exact text to replace", STRING_PARAM),
                (
                    "newString",
                    "The text to replace it with (must differ from oldString)",
                    STRING_PARAM,
                ),
            ],
            optional=[
                (
                    "replaceAll",
                    "Replace all occurrences (default: false)",
                    BOOLEAN_PARAM,
                ),
            ],
        )

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Edit a file."""
        file_path = kwargs.get("filePath", "")
        old_string = kwargs.get("oldString", "")
        new_string = kwargs.get("newString", "")
        replace_all = kwargs.get("replaceAll", False)

        if not file_path:
            return ToolResult.fail("No file path provided")
        if not old_string:
            return ToolResult.fail("No oldString provided")
        if old_string == new_string:
            return ToolResult.fail("oldString and newString are identical")

        path = Path(file_path)
        if not path.is_absolute():
            path = ctx.working_directory / path

        if not path.exists():
            return ToolResult.fail(f"File not found: {path}")

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            return ToolResult.fail(f"Failed to read file: {e}")

        # Count occurrences
        count = content.count(old_string)

        if count == 0:
            return ToolResult.fail("oldString not found in content")

        if count > 1 and not replace_all:
            return ToolResult.fail(
                f"oldString found {count} times. "
                "Provide more context to uniquely identify the match, "
                "or use replaceAll=true to replace all occurrences."
            )

        # Perform replacement
        if replace_all:
            new_content = content.replace(old_string, new_string)
        else:
            new_content = content.replace(old_string, new_string, 1)

        try:
            path.write_text(new_content, encoding="utf-8")
        except Exception as e:
            return ToolResult.fail(f"Failed to write file: {e}")

        return ToolResult.ok(
            f"Replaced {count if replace_all else 1} occurrence(s) in {path}",
            replacements=count if replace_all else 1,
        )
