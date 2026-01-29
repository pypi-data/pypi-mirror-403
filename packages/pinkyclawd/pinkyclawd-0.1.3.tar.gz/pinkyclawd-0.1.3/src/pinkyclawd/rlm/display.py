"""
RLM display module for visible context retrieval and injection output.

Provides formatted console output showing when:
- Context is being retrieved from archives
- Context is being injected into the conversation
- Archival is triggered
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TextIO

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.box import ROUNDED

from pinkyclawd.events import EventType, Event, get_event_bus
from pinkyclawd.rlm.retrieve import RetrievalContext


# Default console for RLM output
_console: Console | None = None


def get_console() -> Console:
    """Get the RLM console for output."""
    global _console
    if _console is None:
        _console = Console(stderr=True, force_terminal=True)
    return _console


def set_console(console: Console) -> None:
    """Set the console to use for RLM output."""
    global _console
    _console = console


@dataclass
class RLMDisplayConfig:
    """Configuration for RLM display output."""

    enabled: bool = True
    show_retrieval: bool = True
    show_injection: bool = True
    show_archival: bool = True
    verbose: bool = False  # Show full content vs summary
    color: str = "cyan"


_display_config = RLMDisplayConfig()


def configure_display(
    enabled: bool | None = None,
    show_retrieval: bool | None = None,
    show_injection: bool | None = None,
    show_archival: bool | None = None,
    verbose: bool | None = None,
    color: str | None = None,
) -> None:
    """Configure RLM display settings."""
    if enabled is not None:
        _display_config.enabled = enabled
    if show_retrieval is not None:
        _display_config.show_retrieval = show_retrieval
    if show_injection is not None:
        _display_config.show_injection = show_injection
    if show_archival is not None:
        _display_config.show_archival = show_archival
    if verbose is not None:
        _display_config.verbose = verbose
    if color is not None:
        _display_config.color = color


def display_retrieval_start(query: str, session_id: str) -> None:
    """Display that context retrieval is starting."""
    if not _display_config.enabled or not _display_config.show_retrieval:
        return

    console = get_console()
    text = Text()
    text.append("RLM ", style="bold cyan")
    text.append("Searching archived context for: ", style="dim")
    text.append(query[:60] + "..." if len(query) > 60 else query, style="italic")

    console.print(text)


def display_retrieval_result(context: RetrievalContext) -> None:
    """Display the result of context retrieval."""
    if not _display_config.enabled or not _display_config.show_retrieval:
        return

    console = get_console()

    if context.is_empty:
        text = Text()
        text.append("RLM ", style="bold cyan")
        text.append("No relevant archived context found", style="dim")
        console.print(text)
        return

    # Summary line
    text = Text()
    text.append("RLM ", style="bold cyan")
    text.append("Context retrieved: ", style="green")
    text.append(f"{len(context.blocks)} blocks ", style="bold green")
    text.append(f"({context.total_tokens:,} tokens)", style="dim green")
    console.print(text)

    # Show block summaries if verbose
    if _display_config.verbose:
        table = Table(box=ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("Task", style="cyan", max_width=40)
        table.add_column("Tokens", justify="right", style="green")
        table.add_column("Summary", max_width=50)

        for block in context.blocks:
            task = block.task_description or "General"
            if len(task) > 40:
                task = task[:37] + "..."

            summary = block.summary
            if len(summary) > 50:
                summary = summary[:47] + "..."

            table.add_row(task, str(block.tokens), summary)

        console.print(table)


def display_injection(context: RetrievalContext) -> None:
    """Display that context is being injected into the conversation."""
    if not _display_config.enabled or not _display_config.show_injection:
        return

    if context.is_empty:
        return

    console = get_console()

    # Create a panel showing the injection
    text = Text()
    text.append(f"Injecting {len(context.blocks)} archived context blocks ", style="bold")
    text.append(f"({context.total_tokens:,} tokens)\n", style="dim")

    for i, block in enumerate(context.blocks, 1):
        task = block.task_description or "General context"
        text.append(f"\n  {i}. ", style="cyan")
        text.append(task[:50], style="italic")
        if len(task) > 50:
            text.append("...", style="dim italic")

    panel = Panel(
        text,
        title="[bold cyan]Context Injection[/bold cyan]",
        border_style="cyan",
        box=ROUNDED,
    )
    console.print(panel)


def display_archival_start(session_id: str, message_count: int) -> None:
    """Display that archival is starting."""
    if not _display_config.enabled or not _display_config.show_archival:
        return

    console = get_console()
    text = Text()
    text.append("RLM ", style="bold yellow")
    text.append("Archiving ", style="yellow")
    text.append(f"{message_count} messages", style="bold yellow")
    text.append(" from session...", style="dim yellow")

    console.print(text)


def display_archival_complete(
    tokens_archived: int,
    messages_archived: int,
    summary: str | None = None,
) -> None:
    """Display that archival is complete."""
    if not _display_config.enabled or not _display_config.show_archival:
        return

    console = get_console()
    text = Text()
    text.append("RLM ", style="bold green")
    text.append("Archived ", style="green")
    text.append(f"{messages_archived} messages ", style="bold green")
    text.append(f"({tokens_archived:,} tokens)", style="dim green")

    console.print(text)

    if summary and _display_config.verbose:
        console.print(f"    Summary: {summary[:100]}...", style="dim italic")


def display_context_status(
    total_tokens: int,
    token_limit: int,
    archived_count: int,
) -> None:
    """Display current context status."""
    if not _display_config.enabled:
        return

    console = get_console()

    usage_pct = (total_tokens / token_limit * 100) if token_limit > 0 else 0

    # Color based on usage
    if usage_pct >= 80:
        color = "red"
    elif usage_pct >= 60:
        color = "yellow"
    else:
        color = "green"

    text = Text()
    text.append("RLM ", style="bold cyan")
    text.append("Context: ", style="dim")
    text.append(f"{total_tokens:,}/{token_limit:,} ", style=f"bold {color}")
    text.append(f"({usage_pct:.1f}%) ", style=color)
    text.append(f"| {archived_count} archived blocks", style="dim")

    console.print(text)


# Event handlers for automatic display


def _handle_rlm_event(event: Event) -> None:
    """Handle RLM events and display output."""
    if event.type == EventType.RLM_CONTEXT_RETRIEVED:
        # Build a minimal context object for display
        block_count = event.data.get("block_count", 0)
        total_tokens = event.data.get("total_tokens", 0)
        trigger = event.data.get("trigger", "")

        console = get_console()
        text = Text()
        text.append("RLM ", style="bold cyan")
        text.append("Context retrieved: ", style="green")
        text.append(f"{block_count} blocks ", style="bold green")
        text.append(f"({total_tokens:,} tokens) ", style="dim green")
        if trigger:
            text.append(f"[{trigger}]", style="dim italic")
        console.print(text)

    elif event.type == EventType.RLM_ARCHIVE_STARTED:
        session_id = event.data.get("session_id", "")
        message_count = event.data.get("message_count", 0)
        display_archival_start(session_id, message_count)

    elif event.type == EventType.RLM_ARCHIVE_COMPLETED:
        tokens = event.data.get("tokens_archived", 0)
        messages = event.data.get("messages_archived", 0)
        summary = event.data.get("summary")
        display_archival_complete(tokens, messages, summary)


def register_event_handlers() -> None:
    """Register event handlers for RLM display output."""
    bus = get_event_bus()
    bus.subscribe(_handle_rlm_event, EventType.RLM_CONTEXT_RETRIEVED)
    bus.subscribe(_handle_rlm_event, EventType.RLM_ARCHIVE_STARTED)
    bus.subscribe(_handle_rlm_event, EventType.RLM_ARCHIVE_COMPLETED)


# Initialize handlers on import
register_event_handlers()
