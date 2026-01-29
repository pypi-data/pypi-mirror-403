"""
MultiEdit tool for multiple sequential edits on a single file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pinkyclawd.tool.base import (
    ARRAY_PARAM,
    STRING_PARAM,
    Tool,
    ToolContext,
    ToolResult,
    make_schema,
)


class MultiEditTool(Tool):
    """Perform multiple sequential edits on a single file."""

    @property
    def name(self) -> str:
        return "multiedit"

    @property
    def description(self) -> str:
        return """Perform multiple sequential edits on a single file.

Use this when you need to make several changes to the same file.
Edits are applied in order, so earlier edits affect later ones.
The operation is atomic - all edits succeed or none are applied.

Each edit contains:
- oldString: The exact text to replace
- newString: The replacement text
- replaceAll: Whether to replace all occurrences (optional)"""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                ("filePath", "Absolute path to the file to modify", STRING_PARAM),
                (
                    "edits",
                    "Array of edit operations to apply",
                    ARRAY_PARAM(
                        {
                            "type": "object",
                            "properties": {
                                "oldString": {
                                    "type": "string",
                                    "description": "The exact text to replace",
                                },
                                "newString": {
                                    "type": "string",
                                    "description": "The replacement text",
                                },
                                "replaceAll": {
                                    "type": "boolean",
                                    "description": "Replace all occurrences (default: false)",
                                },
                            },
                            "required": ["oldString", "newString"],
                        }
                    ),
                ),
            ],
        )

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Execute multiple edits on a file."""
        file_path = kwargs.get("filePath", "")
        edits = kwargs.get("edits", [])

        if not file_path:
            return ToolResult.fail("No file path provided")

        if not edits:
            return ToolResult.fail("No edits provided")

        if not isinstance(edits, list):
            return ToolResult.fail("Edits must be an array")

        path = Path(file_path)
        if not path.is_absolute():
            path = ctx.working_directory / path

        if not path.exists():
            return ToolResult.fail(f"File not found: {path}")

        # Read original content
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            return ToolResult.fail(f"Failed to read file: {e}")

        # Store original for rollback
        original_content = content

        # Apply edits sequentially
        total_replacements = 0
        edit_results: list[str] = []

        for i, edit in enumerate(edits):
            if not isinstance(edit, dict):
                return ToolResult.fail(f"Edit {i + 1} is not an object")

            old_string = edit.get("oldString", "")
            new_string = edit.get("newString", "")
            replace_all = edit.get("replaceAll", False)

            if not old_string:
                return ToolResult.fail(f"Edit {i + 1}: No oldString provided")

            if old_string == new_string:
                return ToolResult.fail(
                    f"Edit {i + 1}: oldString and newString are identical"
                )

            # Count occurrences
            count = content.count(old_string)

            if count == 0:
                # Rollback - don't write anything
                return ToolResult.fail(
                    f"Edit {i + 1}: oldString not found in file "
                    f"(note: earlier edits may have changed the content)"
                )

            if count > 1 and not replace_all:
                return ToolResult.fail(
                    f"Edit {i + 1}: oldString found {count} times. "
                    "Provide more context to uniquely identify the match, "
                    "or use replaceAll=true."
                )

            # Apply the edit
            if replace_all:
                content = content.replace(old_string, new_string)
                replacements = count
            else:
                content = content.replace(old_string, new_string, 1)
                replacements = 1

            total_replacements += replacements
            edit_results.append(f"Edit {i + 1}: {replacements} replacement(s)")

        # Write the final content
        try:
            path.write_text(content, encoding="utf-8")
        except Exception as e:
            return ToolResult.fail(f"Failed to write file: {e}")

        # Build result message
        result_lines = [
            f"Applied {len(edits)} edits to {path}",
            f"Total replacements: {total_replacements}",
            "",
        ]
        result_lines.extend(edit_results)

        return ToolResult.ok(
            "\n".join(result_lines),
            edits_applied=len(edits),
            total_replacements=total_replacements,
        )
