"""
Session management routes.

Provides full session lifecycle management including:
- CRUD operations
- Forking and branching
- Sharing and collaboration
- Message and part management
- Status tracking
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from pinkyclawd.config.storage import (
    Session,
    SessionStatus,
    Message,
    MessagePart,
    PartType,
    get_storage,
)
from pinkyclawd.session.manager import get_session_manager

router = APIRouter()


class SessionCreate(BaseModel):
    """Request body for creating a session."""

    title: str | None = None
    directory: str | None = None


class SessionUpdate(BaseModel):
    """Request body for updating a session."""

    title: str | None = None
    directory: str | None = None
    archived_at: datetime | None = None


class SessionFork(BaseModel):
    """Request body for forking a session."""

    message_id: str | None = None
    title: str | None = None


class PartUpdate(BaseModel):
    """Request body for updating a message part."""

    content: dict[str, Any]


class SessionResponse(BaseModel):
    """Session response model."""

    id: str
    title: str
    directory: str
    message_count: int
    created_at: datetime
    updated_at: datetime | None = None
    parent_id: str | None = None
    share_token: str | None = None
    status: str = "idle"


class SessionStatusResponse(BaseModel):
    """Status of a single session."""

    session_id: str
    status: str


class SessionListResponse(BaseModel):
    """Response for listing sessions."""

    sessions: list[SessionResponse]
    total: int
    offset: int
    limit: int


class TodoItem(BaseModel):
    """A todo item."""

    content: str
    status: str
    active_form: str | None = None


def _session_to_response(session: Session, message_count: int) -> SessionResponse:
    """Convert a Session to a SessionResponse."""
    return SessionResponse(
        id=session.id,
        title=session.title,
        directory=session.directory,
        message_count=message_count,
        created_at=session.created_at,
        updated_at=session.updated_at,
        parent_id=session.parent_id,
        share_token=session.share_token,
        status=session.status.value,
    )


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    directory: str | None = None,
):
    """List all sessions."""
    storage = get_storage()
    sessions = storage.list_sessions(limit=limit, offset=offset, directory=directory)

    session_responses = []
    for s in sessions:
        messages = storage.get_messages(s.id)
        session_responses.append(_session_to_response(s, len(messages)))

    return SessionListResponse(
        sessions=session_responses,
        total=len(sessions),
        offset=offset,
        limit=limit,
    )


@router.get("/status")
async def get_all_session_status():
    """Get status for all sessions."""
    storage = get_storage()
    sessions = storage.list_sessions(limit=1000)

    return {
        "statuses": [
            SessionStatusResponse(
                session_id=s.id,
                status=s.status.value,
            )
            for s in sessions
        ]
    }


@router.post("", response_model=SessionResponse)
async def create_session(body: SessionCreate):
    """Create a new session."""
    manager = get_session_manager()
    session = manager.create(
        title=body.title or "New Conversation",
        directory=body.directory or ".",
    )
    return _session_to_response(session, 0)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a specific session."""
    storage = get_storage()
    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = storage.get_messages(session_id)
    return _session_to_response(session, len(messages))


@router.get("/{session_id}/children")
async def get_session_children(session_id: str):
    """Get child sessions (forked from this session)."""
    storage = get_storage()
    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    children = storage.get_child_sessions(session_id)

    return {
        "children": [
            _session_to_response(child, len(storage.get_messages(child.id)))
            for child in children
        ]
    }


@router.get("/{session_id}/todo")
async def get_session_todos(session_id: str):
    """Get todos for a session."""
    storage = get_storage()
    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Todos are stored in session metadata
    todos = session.metadata.get("todos", [])

    return {"todos": todos}


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(session_id: str, body: SessionUpdate):
    """Update a session."""
    storage = get_storage()
    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update fields
    if body.title is not None:
        session.title = body.title
    if body.directory is not None:
        session.directory = body.directory
    if body.archived_at is not None:
        session.archived_at = body.archived_at
    session.updated_at = datetime.now()

    storage.update_session(session)
    messages = storage.get_messages(session_id)

    return _session_to_response(session, len(messages))


# Keep PUT for backwards compatibility
@router.put("/{session_id}", response_model=SessionResponse)
async def update_session_put(session_id: str, body: SessionUpdate):
    """Update a session (PUT method for backwards compatibility)."""
    return await update_session(session_id, body)


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    manager = get_session_manager()
    deleted = manager.delete(session_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"status": "deleted", "session_id": session_id}


@router.post("/{session_id}/init")
async def init_session(session_id: str):
    """Initialize a session with AGENTS.md content if present."""
    storage = get_storage()
    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Look for AGENTS.md in the session directory
    from pathlib import Path

    agents_file = Path(session.directory) / "AGENTS.md"
    content = None

    if agents_file.exists():
        content = agents_file.read_text()
    else:
        # Check for .claude/AGENTS.md
        claude_agents = Path(session.directory) / ".claude" / "AGENTS.md"
        if claude_agents.exists():
            content = claude_agents.read_text()

    if content:
        # Store the agents content in session metadata
        session.metadata["agents_md"] = content
        storage.update_session(session)

        return {
            "status": "initialized",
            "session_id": session_id,
            "agents_loaded": True,
        }

    return {
        "status": "initialized",
        "session_id": session_id,
        "agents_loaded": False,
    }


@router.post("/{session_id}/fork", response_model=SessionResponse)
async def fork_session(session_id: str, body: SessionFork):
    """Fork a session at a specific message point."""
    manager = get_session_manager()
    forked = manager.fork(
        session_id=session_id,
        from_message_id=body.message_id,
        title=body.title,
    )

    if not forked:
        raise HTTPException(status_code=404, detail="Session not found")

    return _session_to_response(forked, len(get_storage().get_messages(forked.id)))


@router.post("/{session_id}/abort")
async def abort_session(session_id: str):
    """Abort an active session."""
    storage = get_storage()
    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update status to aborted
    session.status = SessionStatus.ABORTED
    storage.update_session(session)

    return {"status": "aborted", "session_id": session_id}


@router.post("/{session_id}/share")
async def share_session(session_id: str):
    """Create a shareable link for a session."""
    storage = get_storage()
    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Generate a share token if not already present
    if not session.share_token:
        session.share_token = secrets.token_urlsafe(16)
        storage.update_session(session)

    return {
        "status": "shared",
        "session_id": session_id,
        "share_token": session.share_token,
    }


@router.delete("/{session_id}/share")
async def unshare_session(session_id: str):
    """Remove the shareable link from a session."""
    storage = get_storage()
    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.share_token = None
    storage.update_session(session)

    return {"status": "unshared", "session_id": session_id}


@router.get("/{session_id}/diff")
async def get_session_diff(
    session_id: str,
    message_id: str | None = Query(None, description="Message ID to get diff from"),
):
    """Get file changes from a specific message or session."""
    storage = get_storage()
    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = storage.get_messages(session_id)

    # Filter to the specific message if provided
    if message_id:
        messages = [m for m in messages if m.id == message_id]
        if not messages:
            raise HTTPException(status_code=404, detail="Message not found")

    # Extract file changes from tool results
    file_changes = []
    for msg in messages:
        for part in msg.parts:
            if part.type == PartType.TOOL_RESULT:
                content = part.content
                tool_name = content.get("tool_name", "")
                if tool_name in ("Write", "Edit", "MultiEdit"):
                    file_changes.append({
                        "tool": tool_name,
                        "file": content.get("file_path", content.get("path", "")),
                        "success": content.get("success", True),
                    })

    return {"changes": file_changes}


@router.post("/{session_id}/summarize")
async def summarize_session(session_id: str):
    """Generate a summary of the session (compaction)."""
    manager = get_session_manager()
    result = manager.compact(session_id)

    if not result:
        raise HTTPException(status_code=404, detail="Session not found or compaction failed")

    return {"status": "summarized", "session_id": session_id}


@router.post("/{session_id}/revert")
async def revert_message(session_id: str, message_id: str = Query(...)):
    """Revert a message (mark it as reverted)."""
    storage = get_storage()
    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    message = storage.get_message(message_id)
    if not message or message.session_id != session_id:
        raise HTTPException(status_code=404, detail="Message not found")

    # Mark as reverted in metadata
    message.metadata["reverted"] = True
    message.metadata["reverted_at"] = datetime.now().isoformat()

    # We need to update the message - add a method if needed
    # For now, store in session metadata
    reverted = session.metadata.get("reverted_messages", [])
    if message_id not in reverted:
        reverted.append(message_id)
        session.metadata["reverted_messages"] = reverted
        storage.update_session(session)

    return {"status": "reverted", "message_id": message_id}


@router.post("/{session_id}/unrevert")
async def unrevert_message(session_id: str, message_id: str = Query(...)):
    """Unrevert a message (restore it)."""
    storage = get_storage()
    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Remove from reverted list
    reverted = session.metadata.get("reverted_messages", [])
    if message_id in reverted:
        reverted.remove(message_id)
        session.metadata["reverted_messages"] = reverted
        storage.update_session(session)

    return {"status": "unreverted", "message_id": message_id}


@router.get("/{session_id}/message")
async def get_session_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get messages for a session."""
    storage = get_storage()
    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = storage.get_messages(session_id)
    reverted = session.metadata.get("reverted_messages", [])

    # Apply pagination
    paginated = messages[offset : offset + limit]

    return {
        "messages": [
            {
                "id": m.id,
                "role": m.role.value,
                "parts": [
                    {
                        "id": p.id,
                        "type": p.type.value,
                        "content": p.content,
                    }
                    for p in m.parts
                ],
                "created_at": m.created_at.isoformat(),
                "reverted": m.id in reverted,
            }
            for m in paginated
        ],
        "total": len(messages),
        "offset": offset,
        "limit": limit,
    }


# Keep old endpoint for backwards compatibility
@router.get("/{session_id}/messages")
async def get_session_messages_compat(
    session_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get messages for a session (backwards compatible endpoint)."""
    return await get_session_messages(session_id, limit, offset)


@router.get("/{session_id}/message/{message_id}")
async def get_message(session_id: str, message_id: str):
    """Get a specific message."""
    storage = get_storage()
    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    message = storage.get_message(message_id)
    if not message or message.session_id != session_id:
        raise HTTPException(status_code=404, detail="Message not found")

    reverted = session.metadata.get("reverted_messages", [])

    return {
        "id": message.id,
        "role": message.role.value,
        "parts": [
            {
                "id": p.id,
                "type": p.type.value,
                "content": p.content,
            }
            for p in message.parts
        ],
        "created_at": message.created_at.isoformat(),
        "reverted": message.id in reverted,
    }


@router.delete("/{session_id}/message/{message_id}/part/{part_id}")
async def delete_message_part(session_id: str, message_id: str, part_id: str):
    """Delete a message part."""
    storage = get_storage()
    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    message = storage.get_message(message_id)
    if not message or message.session_id != session_id:
        raise HTTPException(status_code=404, detail="Message not found")

    part = storage.get_message_part(part_id)
    if not part or part.message_id != message_id:
        raise HTTPException(status_code=404, detail="Part not found")

    deleted = storage.delete_message_part(part_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete part")

    return {"status": "deleted", "part_id": part_id}


@router.patch("/{session_id}/message/{message_id}/part/{part_id}")
async def update_message_part(
    session_id: str,
    message_id: str,
    part_id: str,
    body: PartUpdate,
):
    """Update a message part's content."""
    storage = get_storage()
    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    message = storage.get_message(message_id)
    if not message or message.session_id != session_id:
        raise HTTPException(status_code=404, detail="Message not found")

    part = storage.get_message_part(part_id)
    if not part or part.message_id != message_id:
        raise HTTPException(status_code=404, detail="Part not found")

    # Update the part content
    part.content = body.content
    storage.update_message_part(part)

    return {
        "status": "updated",
        "part": {
            "id": part.id,
            "type": part.type.value,
            "content": part.content,
        },
    }
