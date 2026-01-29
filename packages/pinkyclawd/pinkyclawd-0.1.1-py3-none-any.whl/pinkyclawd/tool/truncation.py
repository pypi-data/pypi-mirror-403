"""
Truncation module for handling large tool outputs.

Provides utilities to truncate large outputs while preserving
the full content in a file for later reference.
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from pinkyclawd.config.paths import get_data_dir

logger = logging.getLogger(__name__)

# Default limits
MAX_LINES = 2000
MAX_BYTES = 50 * 1024  # 50 KB
RETENTION_DAYS = 7


@dataclass
class TruncationResult:
    """Result of a truncation operation."""

    content: str
    truncated: bool
    output_path: str | None = None


def get_output_dir() -> Path:
    """Get the directory for storing truncated output files."""
    output_dir = get_data_dir() / "tool-output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def cleanup_old_outputs(retention_days: int = RETENTION_DAYS) -> int:
    """
    Clean up old truncated output files.

    Args:
        retention_days: Number of days to retain files

    Returns:
        Number of files deleted
    """
    output_dir = get_output_dir()
    cutoff = datetime.now() - timedelta(days=retention_days)
    deleted = 0

    for filepath in output_dir.glob("tool_*"):
        try:
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            if mtime < cutoff:
                filepath.unlink()
                deleted += 1
        except OSError:
            pass

    if deleted > 0:
        logger.debug(f"Cleaned up {deleted} old tool output files")

    return deleted


def truncate_output(
    text: str,
    max_lines: int = MAX_LINES,
    max_bytes: int = MAX_BYTES,
    direction: Literal["head", "tail"] = "head",
    save_full: bool = True,
    has_task_tool: bool = False,
) -> TruncationResult:
    """
    Truncate large text output.

    If the text exceeds the limits, it will be truncated and the full
    content will be saved to a file.

    Args:
        text: The text to potentially truncate
        max_lines: Maximum number of lines to keep
        max_bytes: Maximum number of bytes to keep
        direction: Whether to keep head or tail of the content
        save_full: Whether to save the full content to a file
        has_task_tool: Whether the agent has access to the Task tool

    Returns:
        TruncationResult with the (possibly truncated) content
    """
    lines = text.split("\n")
    total_bytes = len(text.encode("utf-8"))

    # Check if truncation is needed
    if len(lines) <= max_lines and total_bytes <= max_bytes:
        return TruncationResult(content=text, truncated=False)

    # Perform truncation
    out: list[str] = []
    current_bytes = 0
    hit_bytes = False

    if direction == "head":
        for i, line in enumerate(lines):
            if i >= max_lines:
                break
            line_bytes = len(line.encode("utf-8")) + (1 if i > 0 else 0)
            if current_bytes + line_bytes > max_bytes:
                hit_bytes = True
                break
            out.append(line)
            current_bytes += line_bytes
    else:  # tail
        for i in range(len(lines) - 1, -1, -1):
            if len(out) >= max_lines:
                break
            line = lines[i]
            line_bytes = len(line.encode("utf-8")) + (1 if out else 0)
            if current_bytes + line_bytes > max_bytes:
                hit_bytes = True
                break
            out.insert(0, line)
            current_bytes += line_bytes

    # Calculate what was removed
    if hit_bytes:
        removed = total_bytes - current_bytes
        unit = "bytes"
    else:
        removed = len(lines) - len(out)
        unit = "lines"

    preview = "\n".join(out)
    output_path = None

    # Save full content to file
    if save_full:
        output_dir = get_output_dir()
        file_id = f"tool_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        output_path = str(output_dir / file_id)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

    # Create hint message
    if has_task_tool:
        hint = (
            f"The tool call succeeded but the output was truncated. "
            f"Full output saved to: {output_path}\n"
            "Use the Task tool to have explore agent process this file with "
            "Grep and Read (with offset/limit). Do NOT read the full file "
            "yourself - delegate to save context."
        )
    else:
        hint = (
            f"The tool call succeeded but the output was truncated. "
            f"Full output saved to: {output_path}\n"
            "Use Grep to search the full content or Read with offset/limit "
            "to view specific sections."
        )

    # Format the truncated message
    if direction == "head":
        message = f"{preview}\n\n...{removed} {unit} truncated...\n\n{hint}"
    else:
        message = f"...{removed} {unit} truncated...\n\n{hint}\n\n{preview}"

    return TruncationResult(
        content=message,
        truncated=True,
        output_path=output_path,
    )


def apply_truncation(result_output: str, **options) -> tuple[str, bool, str | None]:
    """
    Convenience function to apply truncation to a tool result.

    Args:
        result_output: The output to potentially truncate
        **options: Options passed to truncate_output

    Returns:
        Tuple of (output, truncated, output_path)
    """
    result = truncate_output(result_output, **options)
    return result.content, result.truncated, result.output_path
