"""
Session import/export functionality.

Enables exporting sessions to JSON and importing from external sources.
"""

from __future__ import annotations

import json
import uuid
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from pinkyclawd.config.storage import (
    Session,
    Message,
    MessagePart,
    MessageRole,
    PartType,
    ContextBlock,
    get_storage,
)
from pinkyclawd.session.manager import get_session_manager

logger = logging.getLogger(__name__)


@dataclass
class ExportResult:
    """Result of an export operation."""

    success: bool
    path: Path | None = None
    data: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class ImportResult:
    """Result of an import operation."""

    success: bool
    session_id: str | None = None
    message_count: int = 0
    error: str | None = None


class SessionExporter:
    """
    Handles session export and import operations.

    Supports JSON format with full message and context preservation.
    """

    VERSION = "1.0"

    def __init__(self) -> None:
        self._storage = get_storage()
        self._session_manager = get_session_manager()

    def export_to_json(
        self,
        session_id: str,
        path: Path | str | None = None,
        include_context: bool = True,
    ) -> ExportResult:
        """
        Export a session to JSON.

        Args:
            session_id: Session to export
            path: Output path (optional, returns data if not provided)
            include_context: Include archived context blocks

        Returns:
            ExportResult with path or data
        """
        session = self._storage.get_session(session_id)
        if not session:
            return ExportResult(
                success=False,
                error=f"Session {session_id} not found",
            )

        messages = self._storage.get_messages(session_id)

        # Build export data
        export_data = {
            "version": self.VERSION,
            "exported_at": datetime.now().isoformat(),
            "session": {
                "id": session.id,
                "title": session.title,
                "directory": session.directory,
                "parent_id": session.parent_id,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "metadata": session.metadata,
            },
            "messages": [self._export_message(msg) for msg in messages],
        }

        # Include context blocks if requested
        if include_context:
            blocks = self._storage.get_context_blocks(session_id=session_id)
            export_data["context_blocks"] = [self._export_context_block(block) for block in blocks]

        if path:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(export_data, indent=2))
            logger.info(f"Exported session {session_id} to {path}")
            return ExportResult(success=True, path=path)

        return ExportResult(success=True, data=export_data)

    def import_from_json(
        self,
        path: Path | str | None = None,
        data: dict[str, Any] | None = None,
        new_session_id: str | None = None,
    ) -> ImportResult:
        """
        Import a session from JSON.

        Args:
            path: Path to JSON file
            data: JSON data (alternative to path)
            new_session_id: Override session ID

        Returns:
            ImportResult with new session ID
        """
        # Load data
        if path:
            path = Path(path)
            if not path.exists():
                return ImportResult(
                    success=False,
                    error=f"File not found: {path}",
                )
            data = json.loads(path.read_text())

        if not data:
            return ImportResult(
                success=False,
                error="No data provided",
            )

        # Validate version
        version = data.get("version", "unknown")
        if version != self.VERSION:
            logger.warning(f"Import version mismatch: {version} vs {self.VERSION}")

        # Extract session data
        session_data = data.get("session", {})
        messages_data = data.get("messages", [])
        context_blocks_data = data.get("context_blocks", [])

        # Create session
        session_id = new_session_id or f"ses_{uuid.uuid4().hex[:12]}"

        session = Session(
            id=session_id,
            title=session_data.get("title", "Imported Session"),
            directory=session_data.get("directory", ""),
            parent_id=session_data.get("parent_id"),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=session_data.get("metadata", {}),
        )
        session.metadata["imported_from"] = session_data.get("id", "unknown")
        session.metadata["imported_at"] = datetime.now().isoformat()

        self._storage.create_session(session)

        # Import messages
        message_count = 0
        for msg_data in messages_data:
            message = self._import_message(msg_data, session_id)
            self._storage.add_message(message)
            message_count += 1

        # Import context blocks
        for block_data in context_blocks_data:
            block = self._import_context_block(block_data, session_id)
            self._storage.add_context_block(block)

        logger.info(
            f"Imported session {session_id} with {message_count} messages "
            f"and {len(context_blocks_data)} context blocks"
        )

        return ImportResult(
            success=True,
            session_id=session_id,
            message_count=message_count,
        )

    def export_to_markdown(
        self,
        session_id: str,
        path: Path | str | None = None,
    ) -> ExportResult:
        """
        Export a session to Markdown format.

        Args:
            session_id: Session to export
            path: Output path

        Returns:
            ExportResult
        """
        session = self._storage.get_session(session_id)
        if not session:
            return ExportResult(
                success=False,
                error=f"Session {session_id} not found",
            )

        messages = self._storage.get_messages(session_id)

        # Build markdown
        lines = [
            f"# {session.title}",
            "",
            f"**Created:** {session.created_at.isoformat()}",
            f"**Directory:** {session.directory}",
            "",
            "---",
            "",
        ]

        for msg in messages:
            role = msg.role.value.upper()
            lines.append(f"## {role}")
            lines.append("")

            for part in msg.parts:
                if part.type == PartType.TEXT:
                    lines.append(part.content.get("text", ""))
                elif part.type == PartType.TOOL_USE:
                    tool_name = part.content.get("name", "unknown")
                    args = json.dumps(part.content.get("arguments", {}), indent=2)
                    lines.append(f"**Tool Call:** `{tool_name}`")
                    lines.append("```json")
                    lines.append(args)
                    lines.append("```")
                elif part.type == PartType.TOOL_RESULT:
                    result = part.content.get("result", "")
                    lines.append("**Tool Result:**")
                    lines.append("```")
                    lines.append(result[:1000] + ("..." if len(result) > 1000 else ""))
                    lines.append("```")

            lines.append("")
            lines.append("---")
            lines.append("")

        content = "\n".join(lines)

        if path:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            return ExportResult(success=True, path=path)

        return ExportResult(success=True, data={"markdown": content})

    def _export_message(self, message: Message) -> dict[str, Any]:
        """Export a message to dict."""
        return {
            "id": message.id,
            "role": message.role.value,
            "parts": [self._export_part(p) for p in message.parts],
            "created_at": message.created_at.isoformat(),
            "metadata": message.metadata,
        }

    def _export_part(self, part: MessagePart) -> dict[str, Any]:
        """Export a message part to dict."""
        return {
            "id": part.id,
            "type": part.type.value,
            "content": part.content,
            "created_at": part.created_at.isoformat(),
        }

    def _export_context_block(self, block: ContextBlock) -> dict[str, Any]:
        """Export a context block to dict."""
        return {
            "id": block.id,
            "task_id": block.task_id,
            "task_description": block.task_description,
            "summary": block.summary,
            "content": block.content,
            "tokens": block.tokens,
            "created_at": block.created_at.isoformat(),
        }

    def _import_message(self, data: dict[str, Any], session_id: str) -> Message:
        """Import a message from dict."""
        message_id = f"msg_{uuid.uuid4().hex[:12]}"

        parts = []
        for part_data in data.get("parts", []):
            part = MessagePart(
                id=f"part_{uuid.uuid4().hex[:12]}",
                message_id=message_id,
                type=PartType(part_data.get("type", "text")),
                content=part_data.get("content", {}),
            )
            parts.append(part)

        return Message(
            id=message_id,
            session_id=session_id,
            role=MessageRole(data.get("role", "user")),
            parts=parts,
            metadata=data.get("metadata", {}),
        )

    def _import_context_block(
        self,
        data: dict[str, Any],
        session_id: str,
    ) -> ContextBlock:
        """Import a context block from dict."""
        return ContextBlock(
            id=f"ctx_{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            task_id=data.get("task_id"),
            task_description=data.get("task_description", ""),
            summary=data.get("summary", ""),
            content=data.get("content", ""),
            tokens=data.get("tokens", 0),
        )


# Global exporter instance
_exporter: SessionExporter | None = None


def get_exporter() -> SessionExporter:
    """Get the global session exporter."""
    global _exporter
    if _exporter is None:
        _exporter = SessionExporter()
    return _exporter


def export_session(
    session_id: str,
    path: Path | str,
    format: str = "json",
) -> ExportResult:
    """
    Export a session to file.

    Args:
        session_id: Session to export
        path: Output path
        format: Export format (json or markdown)

    Returns:
        ExportResult
    """
    exporter = get_exporter()
    if format == "markdown" or str(path).endswith(".md"):
        return exporter.export_to_markdown(session_id, path)
    return exporter.export_to_json(session_id, path)


def import_session(path: Path | str) -> ImportResult:
    """
    Import a session from file.

    Args:
        path: Path to import file

    Returns:
        ImportResult
    """
    return get_exporter().import_from_json(path)
