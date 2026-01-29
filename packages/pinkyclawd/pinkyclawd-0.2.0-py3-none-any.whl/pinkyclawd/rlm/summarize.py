"""
LLM-based summarization for RLM context archival.

Generates detailed summaries of archived conversations using
a compaction agent, enabling better context continuation.
"""

from __future__ import annotations

import logging
from typing import Any

from pinkyclawd.config.settings import get_config
from pinkyclawd.config.storage import Message, MessagePart, PartType
from pinkyclawd.rlm.display import get_console

logger = logging.getLogger(__name__)


# Prompt for generating context summaries
SUMMARY_PROMPT = """Provide a detailed summary of this conversation for context continuation. Focus on:

1. **What was accomplished**: Files modified, features implemented, bugs fixed
2. **Current state**: Where the work stands, any pending items
3. **Key decisions**: Important choices made and their rationale
4. **Important locations**: File paths, function names, code locations mentioned
5. **Errors & resolutions**: Any issues encountered and how they were resolved

Keep the summary concise but comprehensive enough to continue the conversation in a new context window."""


async def generate_summary(
    messages: list[Message],
    model: str | None = None,
) -> str:
    """
    Generate an LLM-based summary of conversation messages.

    Uses a lightweight model to create a detailed summary suitable
    for context continuation.

    Args:
        messages: Messages to summarize
        model: Optional model override (defaults to config model)

    Returns:
        Generated summary text
    """
    if not messages:
        return "No messages to summarize"

    config = get_config()
    model = model or config.model

    # Build conversation text for summarization
    conversation_text = _serialize_messages(messages)

    if not conversation_text.strip():
        return "No content to summarize"

    console = get_console()
    console.print(
        f"[bold yellow]RLM[/bold yellow] [dim]Generating context summary...[/dim]"
    )

    try:
        # Try to use provider for summarization
        summary = await _call_llm_for_summary(conversation_text, model)

        if summary:
            logger.info(f"Generated summary: {len(summary)} chars")
            console.print(
                f"[bold green]RLM[/bold green] [dim]Summary generated ({len(summary)} chars)[/dim]"
            )
            return summary

    except Exception as e:
        logger.warning(f"LLM summarization failed: {e}, using fallback")

    # Fallback to extractive summary
    return _generate_fallback_summary(messages)


async def _call_llm_for_summary(conversation_text: str, model: str) -> str | None:
    """
    Call an LLM to generate a summary.

    Args:
        conversation_text: Serialized conversation
        model: Model to use

    Returns:
        Generated summary or None if failed
    """
    try:
        from pinkyclawd.provider.registry import get_provider_registry

        registry = get_provider_registry()
        provider = registry.get_provider_for_model(model)

        if not provider:
            logger.warning(f"No provider found for model {model}")
            return None

        # Create a simple completion request
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes technical conversations concisely.",
            },
            {
                "role": "user",
                "content": f"{SUMMARY_PROMPT}\n\n---\n\n{conversation_text}",
            },
        ]

        # Use a small response for efficiency
        response = await provider.complete(
            messages=messages,
            model=model,
            max_tokens=1000,
        )

        return response.get("content", "").strip()

    except ImportError:
        logger.debug("Provider registry not available for summarization")
        return None
    except Exception as e:
        logger.warning(f"LLM call failed: {e}")
        return None


def _generate_fallback_summary(messages: list[Message]) -> str:
    """
    Generate a fallback extractive summary when LLM is unavailable.

    Extracts key information from messages without using an LLM.

    Args:
        messages: Messages to summarize

    Returns:
        Extractive summary text
    """
    parts = []

    # Find key information
    files_mentioned = set()
    tools_used = set()
    errors_found = []

    for msg in messages:
        for part in msg.parts:
            if part.type == PartType.TEXT:
                text = part.content.get("text", "")

                # Extract file paths
                import re
                file_matches = re.findall(r'[./\w]+\.[a-z]{1,4}', text)
                files_mentioned.update(file_matches[:10])

            elif part.type == PartType.TOOL_USE:
                tool_name = part.content.get("name", "")
                if tool_name:
                    tools_used.add(tool_name)

            elif part.type == PartType.TOOL_RESULT:
                result = part.content.get("result", "")
                if "error" in result.lower() or "failed" in result.lower():
                    errors_found.append(result[:200])

    # Build summary
    parts.append("## Conversation Summary (Auto-generated)")
    parts.append("")

    if tools_used:
        parts.append(f"**Tools used**: {', '.join(sorted(tools_used))}")

    if files_mentioned:
        parts.append(f"**Files involved**: {', '.join(sorted(list(files_mentioned)[:10]))}")

    if errors_found:
        parts.append(f"**Errors encountered**: {len(errors_found)}")

    parts.append("")
    parts.append(f"**Message count**: {len(messages)}")

    # Add first and last user messages as context
    user_messages = [m for m in messages if m.role.value == "user"]
    if user_messages:
        first_user = _get_text_from_message(user_messages[0])
        if first_user:
            parts.append(f"\n**Started with**: {first_user[:200]}...")

        if len(user_messages) > 1:
            last_user = _get_text_from_message(user_messages[-1])
            if last_user:
                parts.append(f"\n**Ended with**: {last_user[:200]}...")

    return "\n".join(parts)


def _serialize_messages(messages: list[Message]) -> str:
    """
    Serialize messages to text format for summarization.

    Args:
        messages: Messages to serialize

    Returns:
        Serialized text
    """
    parts = []

    for msg in messages:
        role = msg.role.value.upper()
        parts.append(f"[{role}]")

        for part in msg.parts:
            if part.type == PartType.TEXT:
                text = part.content.get("text", "")
                if text:
                    # Truncate very long text
                    if len(text) > 1000:
                        text = text[:1000] + "...[truncated]"
                    parts.append(text)

            elif part.type == PartType.TOOL_USE:
                tool_name = part.content.get("name", "unknown")
                parts.append(f"[Tool: {tool_name}]")

            elif part.type == PartType.TOOL_RESULT:
                result = part.content.get("result", "")
                if len(result) > 500:
                    result = result[:500] + "...[truncated]"
                parts.append(f"[Result: {result}]")

        parts.append("")

    return "\n".join(parts)


def _get_text_from_message(message: Message) -> str:
    """Extract text content from a message."""
    for part in message.parts:
        if part.type == PartType.TEXT:
            return part.content.get("text", "")
    return ""


def generate_task_summary(
    task_description: str,
    messages: list[Message],
) -> str:
    """
    Generate a quick summary for task-based archival.

    Synchronous version that doesn't use LLM, suitable for
    immediate task completion archival.

    Args:
        task_description: Description of the completed task
        messages: Messages related to the task

    Returns:
        Task summary text
    """
    parts = [f"Task: {task_description}"]

    # Count what was done
    tool_uses = 0
    files_modified = set()

    for msg in messages:
        for part in msg.parts:
            if part.type == PartType.TOOL_USE:
                tool_uses += 1
                tool_name = part.content.get("name", "")
                args = part.content.get("arguments", {})

                # Track file modifications
                if tool_name in ("write", "edit"):
                    file_path = args.get("file_path", args.get("filePath", ""))
                    if file_path:
                        files_modified.add(file_path)

    if tool_uses:
        parts.append(f"Tool executions: {tool_uses}")

    if files_modified:
        parts.append(f"Files modified: {', '.join(sorted(files_modified))}")

    parts.append(f"Messages: {len(messages)}")

    return " | ".join(parts)
