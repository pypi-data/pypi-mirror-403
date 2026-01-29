"""
Chat routes for message handling.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from pinkyclawd.config.storage import (
    Message,
    MessagePart,
    MessageRole,
    PartType,
    Session,
    get_storage,
)
from pinkyclawd.provider.registry import get_provider
from pinkyclawd.rlm import prepare_messages_with_rlm, update_after_response
from pinkyclawd.tool import ToolContext, get_tool_registry

router = APIRouter()


class ChatMessage(BaseModel):
    """A chat message."""

    role: str
    content: str


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    message: str
    session_id: str | None = None
    model: str | None = None
    stream: bool = True
    max_turns: int = 50


class ChatResponse(BaseModel):
    """Response from chat endpoint."""

    session_id: str
    message_id: str
    response: str
    tool_calls: list[dict]
    turns: int


def create_message(session_id: str, role: MessageRole, text: str) -> Message:
    """Create a message with text content."""
    msg_id = f"msg_{uuid.uuid4().hex[:12]}"
    return Message(
        id=msg_id,
        session_id=session_id,
        role=role,
        parts=[
            MessagePart(
                id=f"part_{uuid.uuid4().hex[:8]}",
                message_id=msg_id,
                type=PartType.TEXT,
                content={"text": text},
            )
        ],
        created_at=datetime.now(),
    )


@router.post("", response_model=ChatResponse)
async def send_message(request: Request, body: ChatRequest):
    """
    Send a message and get a response.

    Creates a new session if session_id is not provided.
    """
    storage = get_storage()
    tool_registry = get_tool_registry()

    # Get or create session
    if body.session_id:
        session = storage.get_session(body.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session_id = body.session_id
    else:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        session = Session(
            id=session_id,
            title=f"Chat: {body.message[:30]}...",
            directory=str(request.app.state.working_directory),
        )
        storage.create_session(session)

    # Load existing messages
    messages = storage.get_messages(session_id)

    # Create user message
    user_message = create_message(session_id, MessageRole.USER, body.message)
    messages.append(user_message)
    storage.add_message(user_message)

    # Get model and provider
    model = body.model or "anthropic/claude-3-5-sonnet-20241022"
    provider = get_provider(model)

    # Get tool schemas
    tools = tool_registry.get_schemas()

    # Agent loop
    full_response = ""
    all_tool_calls = []
    turn = 0

    while turn < body.max_turns:
        turn += 1

        # Prepare with RLM
        augmented_messages, rlm_context = prepare_messages_with_rlm(
            session_id=session_id,
            user_query=body.message if turn == 1 else "",
            messages=messages,
            model=model,
        )

        # Get response
        response_text = ""
        pending_tool_calls = []

        async for chunk in provider.stream(
            messages=augmented_messages,
            model=model,
            tools=tools,
        ):
            if chunk.type == "text" and chunk.text:
                response_text += chunk.text
            elif chunk.type == "tool_call_start":
                pending_tool_calls.append({
                    "id": chunk.tool_call_id,
                    "name": chunk.tool_name,
                    "arguments": "",
                })
            elif chunk.type == "tool_call_delta":
                if pending_tool_calls:
                    pending_tool_calls[-1]["arguments"] += chunk.tool_arguments or ""
            elif chunk.type == "done":
                break

        full_response = response_text

        # Store assistant message
        assistant_message = create_message(session_id, MessageRole.ASSISTANT, response_text)
        messages.append(assistant_message)
        storage.add_message(assistant_message)

        # Update RLM
        update_after_response(
            session_id=session_id,
            assistant_message=assistant_message,
            model=model,
        )

        # No tool calls means we're done
        if not pending_tool_calls:
            break

        # Execute tool calls
        tool_results = []
        work_dir = request.app.state.working_directory

        for tc in pending_tool_calls:
            tool_name = tc["name"]
            try:
                tool_args = json.loads(tc["arguments"]) if tc["arguments"] else {}
            except json.JSONDecodeError:
                tool_args = {}

            ctx = ToolContext(
                session_id=session_id,
                message_id=assistant_message.id,
                working_directory=work_dir,
                user_confirmed=True,
            )

            try:
                result = await tool_registry.execute(tool_name, ctx, tool_args)
                tool_results.append({
                    "tool_call_id": tc["id"],
                    "output": result.output,
                    "error": result.error,
                })
                all_tool_calls.append({
                    "name": tool_name,
                    "arguments": tool_args,
                    "success": result.success,
                })
            except Exception as e:
                tool_results.append({
                    "tool_call_id": tc["id"],
                    "output": "",
                    "error": str(e),
                })

        # Create tool result message
        tool_parts = []
        for tr in tool_results:
            tool_parts.append(
                MessagePart(
                    id=f"part_{uuid.uuid4().hex[:8]}",
                    message_id=f"tool_{uuid.uuid4().hex[:8]}",
                    type=PartType.TOOL_RESULT,
                    content={
                        "tool_call_id": tr["tool_call_id"],
                        "output": tr["output"],
                        "error": tr["error"],
                    },
                )
            )

        tool_message = Message(
            id=f"msg_tool_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            role=MessageRole.TOOL,
            parts=tool_parts,
            created_at=datetime.now(),
        )
        messages.append(tool_message)
        storage.add_message(tool_message)

    return ChatResponse(
        session_id=session_id,
        message_id=user_message.id,
        response=full_response,
        tool_calls=all_tool_calls,
        turns=turn,
    )


@router.post("/stream")
async def stream_message(request: Request, body: ChatRequest):
    """
    Stream a chat response using Server-Sent Events.
    """
    storage = get_storage()

    # Get or create session
    if body.session_id:
        session = storage.get_session(body.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session_id = body.session_id
    else:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        session = Session(
            id=session_id,
            title=f"Chat: {body.message[:30]}...",
            directory=str(request.app.state.working_directory),
        )
        storage.create_session(session)

    async def generate():
        """Generate SSE events."""
        messages = storage.get_messages(session_id)

        # Create user message
        user_message = create_message(session_id, MessageRole.USER, body.message)
        messages.append(user_message)
        storage.add_message(user_message)

        # Get model and provider
        model = body.model or "anthropic/claude-3-5-sonnet-20241022"
        provider = get_provider(model)

        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

        # Prepare with RLM
        augmented_messages, rlm_context = prepare_messages_with_rlm(
            session_id=session_id,
            user_query=body.message,
            messages=messages,
            model=model,
        )

        # Stream response
        full_response = ""
        async for chunk in provider.stream(
            messages=augmented_messages,
            model=model,
        ):
            if chunk.type == "text" and chunk.text:
                full_response += chunk.text
                yield f"data: {json.dumps({'type': 'text', 'content': chunk.text})}\n\n"
            elif chunk.type == "done":
                break

        # Store assistant message
        assistant_message = create_message(session_id, MessageRole.ASSISTANT, full_response)
        messages.append(assistant_message)
        storage.add_message(assistant_message)

        # Update RLM
        update_after_response(
            session_id=session_id,
            assistant_message=assistant_message,
            model=model,
        )

        yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message.id})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time chat.
    """
    await websocket.accept()

    storage = get_storage()
    tool_registry = get_tool_registry()

    session = storage.get_session(session_id)
    if not session:
        await websocket.send_json({"type": "error", "message": "Session not found"})
        await websocket.close()
        return

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            if data.get("type") == "message":
                message_text = data.get("content", "")
                model = data.get("model", "anthropic/claude-3-5-sonnet-20241022")

                # Load messages
                messages = storage.get_messages(session_id)

                # Create user message
                user_message = create_message(session_id, MessageRole.USER, message_text)
                messages.append(user_message)
                storage.add_message(user_message)

                # Get provider
                provider = get_provider(model)

                # Prepare with RLM
                augmented_messages, rlm_context = prepare_messages_with_rlm(
                    session_id=session_id,
                    user_query=message_text,
                    messages=messages,
                    model=model,
                )

                # Stream response
                full_response = ""
                async for chunk in provider.stream(
                    messages=augmented_messages,
                    model=model,
                ):
                    if chunk.type == "text" and chunk.text:
                        full_response += chunk.text
                        await websocket.send_json({
                            "type": "text",
                            "content": chunk.text,
                        })
                    elif chunk.type == "done":
                        break

                # Store assistant message
                assistant_message = create_message(
                    session_id, MessageRole.ASSISTANT, full_response
                )
                messages.append(assistant_message)
                storage.add_message(assistant_message)

                # Update RLM
                update_after_response(
                    session_id=session_id,
                    assistant_message=assistant_message,
                    model=model,
                )

                await websocket.send_json({
                    "type": "done",
                    "message_id": assistant_message.id,
                })

            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
