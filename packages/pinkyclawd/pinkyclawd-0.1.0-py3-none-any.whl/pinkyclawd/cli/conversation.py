"""
Conversation loop with full RLM integration.

This module provides the core conversation loop that integrates:
- Provider communication (Anthropic, OpenAI)
- RLM context management (archival, retrieval, injection)
- Token tracking and automatic compaction
- Task completion detection
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime
from typing import AsyncIterator

from pinkyclawd.config.settings import get_config
from pinkyclawd.config.storage import (
    Message,
    MessagePart,
    MessageRole,
    PartType,
    Session,
    get_storage,
)
from pinkyclawd.provider.registry import get_provider
from pinkyclawd.rlm import (
    prepare_messages_with_rlm,
    update_after_response,
    detect_task_completion,
    get_rlm_handler,
    display_context_status,
    register_event_handlers,
)


def create_message(
    session_id: str,
    role: MessageRole,
    text: str,
) -> Message:
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


def get_message_text(message: Message) -> str:
    """Extract text content from a message."""
    texts = []
    for part in message.parts:
        if part.type == PartType.TEXT:
            texts.append(part.content.get("text", ""))
    return " ".join(texts)


def convert_messages_for_provider(messages: list[Message]) -> list[Message]:
    """
    Convert internal Message objects to provider-compatible format.

    The providers expect Message objects with the same structure,
    so this is mostly a passthrough, but can handle any necessary
    transformations.
    """
    # For now, messages are already in the correct format
    # Future: handle any provider-specific transformations
    return messages


async def run_conversation(
    session_id: str | None = None,
    model: str | None = None,
    initial_prompt: str | None = None,
) -> None:
    """
    Run an interactive conversation loop with RLM integration.

    Args:
        session_id: Optional session ID to continue
        model: Model to use (defaults to config)
        initial_prompt: Optional initial prompt to send
    """
    config = get_config()
    storage = get_storage()
    rlm_handler = get_rlm_handler()

    # Register RLM event handlers for display
    register_event_handlers()

    # Create or load session
    if session_id:
        session = storage.get_session(session_id)
        if not session:
            print(f"Session {session_id} not found, creating new session")
            session_id = None

    if not session_id:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        session = Session(
            id=session_id,
            title="New Conversation",
            directory=str(config.working_directory or "."),
        )
        storage.create_session(session)
        print(f"Created session: {session_id}")

    # Load existing messages
    messages = storage.get_messages(session_id)
    print(f"Loaded {len(messages)} existing messages")

    # Get provider
    model = model or config.model
    provider = get_provider(model)
    print(f"Using model: {model}")
    print(f"RLM enabled: {config.rlm.enabled}")
    print("-" * 50)

    # Handle initial prompt if provided
    if initial_prompt:
        await process_turn(
            session_id=session_id,
            user_input=initial_prompt,
            messages=messages,
            provider=provider,
            model=model,
            storage=storage,
            rlm_handler=rlm_handler,
        )

    # Main conversation loop
    while True:
        try:
            # Get user input
            print()
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Handle special commands
            if user_input.lower() in ("exit", "quit", "/quit", "/exit"):
                # Archive on session end if threshold met
                rlm_handler.archive_on_session_end(session_id, messages)
                print("Goodbye!")
                break

            if user_input == "/context":
                state = rlm_handler.get_context_state(session_id)
                display_context_status(state)
                continue

            if user_input == "/compact":
                if rlm_handler.force_compact(session_id):
                    print("Session compacted successfully")
                else:
                    print("Nothing to compact")
                continue

            if user_input.startswith("/"):
                print(f"Unknown command: {user_input}")
                continue

            # Process the turn
            await process_turn(
                session_id=session_id,
                user_input=user_input,
                messages=messages,
                provider=provider,
                model=model,
                storage=storage,
                rlm_handler=rlm_handler,
            )

        except KeyboardInterrupt:
            print("\nInterrupted")
            break
        except EOFError:
            print("\nEnd of input")
            break


async def process_turn(
    session_id: str,
    user_input: str,
    messages: list[Message],
    provider,
    model: str,
    storage,
    rlm_handler,
) -> None:
    """Process a single conversation turn."""

    # 1. Create and store user message
    user_message = create_message(session_id, MessageRole.USER, user_input)
    messages.append(user_message)
    storage.add_message(user_message)

    # 2. RLM: Prepare messages with context injection
    # This will:
    # - Check for reference patterns that need archived context
    # - Search and retrieve relevant archived blocks
    # - Inject context as a system message
    # - Update token tracking
    print("\n[RLM] Preparing context...")
    augmented_messages, rlm_context = prepare_messages_with_rlm(
        session_id=session_id,
        user_query=user_input,
        messages=messages,
        model=model,
    )

    if rlm_context.has_retrieved_context:
        print(f"[RLM] Injected {len(rlm_context.retrieved_context.blocks)} context blocks")

    # 3. Send to provider and get response
    print("\nAssistant: ", end="", flush=True)

    try:
        # Convert messages to provider format
        provider_messages = convert_messages_for_provider(augmented_messages)

        # Stream the response
        full_response = ""
        async for chunk in provider.stream(
            messages=provider_messages,
            model=model,
        ):
            if chunk.type == "text" and chunk.text:
                print(chunk.text, end="", flush=True)
                full_response += chunk.text
            elif chunk.type == "done":
                break
        print()  # Newline after response

    except Exception as e:
        print(f"\nError: {e}")
        # Remove the user message on error
        messages.pop()
        return

    # 4. Create and store assistant message
    assistant_message = create_message(session_id, MessageRole.ASSISTANT, full_response)
    messages.append(assistant_message)
    storage.add_message(assistant_message)

    # 5. RLM: Update state after response
    # This will:
    # - Update token counts
    # - Trigger archival if threshold (33%) is reached
    context_state = update_after_response(
        session_id=session_id,
        assistant_message=assistant_message,
        model=model,
    )

    # 6. Check for task completion phrases
    # Phrases like "done", "finished", "that's all" trigger archival
    if detect_task_completion(user_input):
        print("[RLM] Task completion detected, archiving context...")
        rlm_handler.check_completion_and_archive(
            message=user_input,
            session_id=session_id,
            messages=messages[-10:],  # Archive recent messages
        )

    # 7. Show context status
    print(f"\n[Context: {context_state.usage_ratio:.1%} ({context_state.total_tokens:,}/{context_state.model_limit:,} tokens)]")


async def run_single_prompt(
    prompt: str,
    model: str | None = None,
    output_format: str = "default",
) -> str:
    """
    Run a single prompt (non-interactive mode).

    Args:
        prompt: The prompt to send
        model: Model to use
        output_format: Output format ("default" or "json")

    Returns:
        The assistant's response
    """
    config = get_config()
    storage = get_storage()

    # Create temporary session
    session_id = f"run_{uuid.uuid4().hex[:8]}"
    session = Session(
        id=session_id,
        title=f"Run: {prompt[:30]}...",
        directory=".",
    )
    storage.create_session(session)

    # Create user message
    messages = [create_message(session_id, MessageRole.USER, prompt)]

    # Get provider
    model = model or config.model
    provider = get_provider(model)

    # Prepare with RLM
    augmented_messages, rlm_context = prepare_messages_with_rlm(
        session_id=session_id,
        user_query=prompt,
        messages=messages,
        model=model,
    )

    # Convert and get response
    provider_messages = convert_messages_for_provider(augmented_messages)

    full_response = ""
    async for chunk in provider.stream(
        messages=provider_messages,
        model=model,
    ):
        if chunk.type == "text" and chunk.text:
            if output_format == "default":
                print(chunk.text, end="", flush=True)
            full_response += chunk.text
        elif chunk.type == "done":
            break

    if output_format == "default":
        print()

    return full_response


def main():
    """CLI entry point for conversation."""
    import argparse

    parser = argparse.ArgumentParser(description="Run PinkyClawd conversation")
    parser.add_argument("--session", "-s", help="Session ID to continue")
    parser.add_argument("--model", "-m", help="Model to use")
    parser.add_argument("--prompt", "-p", help="Initial prompt")
    parser.add_argument("--run", "-r", help="Run single prompt (non-interactive)")

    args = parser.parse_args()

    if args.run:
        # Non-interactive mode
        asyncio.run(run_single_prompt(args.run, args.model))
    else:
        # Interactive mode
        asyncio.run(run_conversation(args.session, args.model, args.prompt))


if __name__ == "__main__":
    main()
