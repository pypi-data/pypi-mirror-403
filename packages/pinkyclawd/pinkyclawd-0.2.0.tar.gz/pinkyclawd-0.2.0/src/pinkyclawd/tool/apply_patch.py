"""
Apply patch tool for applying unified diff format patches.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pinkyclawd.tool.base import (
    BOOLEAN_PARAM,
    STRING_PARAM,
    Tool,
    ToolContext,
    ToolResult,
    make_schema,
)


@dataclass
class PatchOperation:
    """A single file operation from a patch."""

    operation: str  # "add", "update", "delete", "move"
    file_path: str
    new_path: str | None = None  # For move operations
    content: str | None = None  # For add/update operations
    hunks: list[dict] | None = None  # For update with hunks


class UnifiedDiffParser:
    """Parser for unified diff format."""

    def __init__(self, patch_content: str) -> None:
        self.content = patch_content
        self.operations: list[PatchOperation] = []

    def parse(self) -> list[PatchOperation]:
        """Parse the patch content into operations."""
        lines = self.content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check for diff header
            if line.startswith("diff --git"):
                i = self._parse_file_diff(lines, i)
            elif line.startswith("---") and i + 1 < len(lines) and lines[i + 1].startswith("+++"):
                i = self._parse_file_diff(lines, i - 1)  # Adjust for missing diff header
            else:
                i += 1

        return self.operations

    def _parse_file_diff(self, lines: list[str], start: int) -> int:
        """Parse a single file diff."""
        i = start
        old_file = None
        new_file = None
        is_new_file = False
        is_deleted = False
        is_renamed = False
        hunks: list[dict] = []

        # Parse headers
        while i < len(lines):
            line = lines[i]

            if line.startswith("diff --git"):
                # Extract file paths from diff header
                match = re.match(r"diff --git a/(.+) b/(.+)", line)
                if match:
                    old_file = match.group(1)
                    new_file = match.group(2)
                i += 1
            elif line.startswith("new file mode"):
                is_new_file = True
                i += 1
            elif line.startswith("deleted file mode"):
                is_deleted = True
                i += 1
            elif line.startswith("rename from"):
                is_renamed = True
                match = re.match(r"rename from (.+)", line)
                if match:
                    old_file = match.group(1)
                i += 1
            elif line.startswith("rename to"):
                match = re.match(r"rename to (.+)", line)
                if match:
                    new_file = match.group(1)
                i += 1
            elif line.startswith("--- "):
                match = re.match(r"--- (?:a/)?(.+)", line)
                if match and match.group(1) != "/dev/null":
                    old_file = match.group(1)
                i += 1
            elif line.startswith("+++ "):
                match = re.match(r"\+\+\+ (?:b/)?(.+)", line)
                if match and match.group(1) != "/dev/null":
                    new_file = match.group(1)
                i += 1
            elif line.startswith("@@"):
                # Start of hunks
                break
            elif line.startswith("diff --git") or (i > start + 10):
                # Next file or too many header lines
                break
            else:
                i += 1

        # Parse hunks
        hunk_content: list[str] = []
        hunk_start: dict | None = None

        while i < len(lines):
            line = lines[i]

            if line.startswith("diff --git") or line.startswith("---"):
                # Next file
                break
            elif line.startswith("@@"):
                # Save previous hunk
                if hunk_start and hunk_content:
                    hunk_start["lines"] = hunk_content
                    hunks.append(hunk_start)

                # Parse hunk header
                match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
                if match:
                    hunk_start = {
                        "old_start": int(match.group(1)),
                        "old_count": int(match.group(2) or 1),
                        "new_start": int(match.group(3)),
                        "new_count": int(match.group(4) or 1),
                    }
                    hunk_content = []
                i += 1
            elif line.startswith("+") or line.startswith("-") or line.startswith(" "):
                hunk_content.append(line)
                i += 1
            elif line.strip() == "":
                i += 1
            else:
                break

        # Save last hunk
        if hunk_start and hunk_content:
            hunk_start["lines"] = hunk_content
            hunks.append(hunk_start)

        # Determine operation type
        if is_deleted:
            self.operations.append(
                PatchOperation(operation="delete", file_path=old_file or new_file or "")
            )
        elif is_renamed:
            self.operations.append(
                PatchOperation(
                    operation="move",
                    file_path=old_file or "",
                    new_path=new_file,
                    hunks=hunks if hunks else None,
                )
            )
        elif is_new_file:
            # Extract new file content from hunks
            content_lines = []
            for hunk in hunks:
                for line in hunk.get("lines", []):
                    if line.startswith("+"):
                        content_lines.append(line[1:])
            self.operations.append(
                PatchOperation(
                    operation="add",
                    file_path=new_file or "",
                    content="\n".join(content_lines),
                )
            )
        elif hunks:
            self.operations.append(
                PatchOperation(
                    operation="update", file_path=new_file or old_file or "", hunks=hunks
                )
            )

        return i


class ApplyPatchTool(Tool):
    """Apply multi-file patches in unified diff format."""

    @property
    def name(self) -> str:
        return "apply_patch"

    @property
    def description(self) -> str:
        return """Apply a patch in unified diff format.

Supports:
- Adding new files
- Updating existing files with hunks
- Deleting files
- Moving/renaming files

The patch should be in standard unified diff format (git diff output).
Use dryRun=true to preview changes without applying."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                ("patch", "The patch content in unified diff format", STRING_PARAM),
            ],
            optional=[
                (
                    "dryRun",
                    "Preview changes without applying (default: false)",
                    BOOLEAN_PARAM,
                ),
            ],
        )

    @property
    def requires_confirmation(self) -> bool:
        return True

    def _apply_hunks(self, original: str, hunks: list[dict]) -> str:
        """Apply hunks to file content."""
        lines = original.split("\n")
        result_lines = []
        line_offset = 0

        for hunk in hunks:
            old_start = hunk["old_start"] - 1 + line_offset
            hunk_lines = hunk.get("lines", [])

            # Copy lines before hunk
            while len(result_lines) < old_start:
                if len(result_lines) < len(lines):
                    result_lines.append(lines[len(result_lines)])
                else:
                    break

            # Apply hunk
            old_line_idx = old_start
            for hunk_line in hunk_lines:
                if hunk_line.startswith("-"):
                    # Remove line - skip in original
                    old_line_idx += 1
                elif hunk_line.startswith("+"):
                    # Add line
                    result_lines.append(hunk_line[1:])
                elif hunk_line.startswith(" "):
                    # Context line - copy from original
                    if old_line_idx < len(lines):
                        result_lines.append(lines[old_line_idx])
                    old_line_idx += 1

        # Copy remaining lines
        remaining_start = len(result_lines)
        if hunks:
            last_hunk = hunks[-1]
            remaining_start = last_hunk["old_start"] - 1 + last_hunk["old_count"] + line_offset

        for i in range(remaining_start, len(lines)):
            if i < len(lines):
                result_lines.append(lines[i])

        return "\n".join(result_lines)

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Apply a patch."""
        patch_content = kwargs.get("patch", "")
        dry_run = kwargs.get("dryRun", False)

        if not patch_content:
            return ToolResult.fail("No patch content provided")

        # Parse the patch
        parser = UnifiedDiffParser(patch_content)
        try:
            operations = parser.parse()
        except Exception as e:
            return ToolResult.fail(f"Failed to parse patch: {e}")

        if not operations:
            return ToolResult.fail("No operations found in patch")

        results: list[str] = []
        errors: list[str] = []

        for op in operations:
            file_path = Path(op.file_path)
            if not file_path.is_absolute():
                file_path = ctx.working_directory / file_path

            try:
                if op.operation == "add":
                    if dry_run:
                        results.append(f"Would create: {op.file_path}")
                    else:
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_text(op.content or "", encoding="utf-8")
                        results.append(f"Created: {op.file_path}")

                elif op.operation == "delete":
                    if dry_run:
                        results.append(f"Would delete: {op.file_path}")
                    else:
                        if file_path.exists():
                            file_path.unlink()
                            results.append(f"Deleted: {op.file_path}")
                        else:
                            errors.append(f"File not found: {op.file_path}")

                elif op.operation == "move":
                    new_path = Path(op.new_path or "")
                    if not new_path.is_absolute():
                        new_path = ctx.working_directory / new_path

                    if dry_run:
                        results.append(f"Would move: {op.file_path} -> {op.new_path}")
                    else:
                        if file_path.exists():
                            new_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(file_path), str(new_path))

                            # Apply any hunks to the moved file
                            if op.hunks:
                                content = new_path.read_text(encoding="utf-8")
                                new_content = self._apply_hunks(content, op.hunks)
                                new_path.write_text(new_content, encoding="utf-8")

                            results.append(f"Moved: {op.file_path} -> {op.new_path}")
                        else:
                            errors.append(f"File not found: {op.file_path}")

                elif op.operation == "update":
                    if not file_path.exists():
                        errors.append(f"File not found: {op.file_path}")
                        continue

                    if dry_run:
                        results.append(f"Would update: {op.file_path}")
                    else:
                        content = file_path.read_text(encoding="utf-8")
                        new_content = self._apply_hunks(content, op.hunks or [])
                        file_path.write_text(new_content, encoding="utf-8")
                        results.append(f"Updated: {op.file_path}")

            except Exception as e:
                errors.append(f"Error with {op.file_path}: {e}")

        # Build output
        output_lines = []
        if dry_run:
            output_lines.append("Dry run - no changes applied:\n")

        output_lines.extend(results)

        if errors:
            output_lines.append("\nErrors:")
            output_lines.extend(f"  - {e}" for e in errors)

        success = len(errors) == 0
        return ToolResult(
            success=success,
            output="\n".join(output_lines),
            error=f"{len(errors)} error(s)" if errors else None,
            metadata={
                "operations": len(operations),
                "succeeded": len(results),
                "failed": len(errors),
                "dry_run": dry_run,
            },
        )
