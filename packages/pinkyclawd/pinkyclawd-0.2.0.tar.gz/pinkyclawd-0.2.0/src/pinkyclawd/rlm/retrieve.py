"""
Context retrieval system for RLM.

Proactively retrieves relevant archived context to inject into
the conversation, enabling coherent long-running sessions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from pinkyclawd.config.settings import get_config
from pinkyclawd.config.storage import ContextBlock, Message, PartType
from pinkyclawd.events import EventType, Event, get_event_bus
from pinkyclawd.rlm.search import ContextSearcher, SearchResult, get_searcher
from pinkyclawd.rlm.context import TokenCounter
from pinkyclawd.constants import (
    ANALYSIS_SIMILARITY_THRESHOLD,
    MAX_CONTEXT_BLOCKS,
)

logger = logging.getLogger(__name__)


@dataclass
class RetrievalContext:
    """Context to be injected into the conversation."""

    blocks: list[ContextBlock] = field(default_factory=list)
    total_tokens: int = 0
    trigger: str = ""  # What triggered the retrieval

    @property
    def is_empty(self) -> bool:
        return len(self.blocks) == 0

    def to_system_message(self) -> str:
        """Format as a system message for injection."""
        if self.is_empty:
            return ""

        parts = ["<archived-context>"]
        parts.append(
            f"The following is relevant context from earlier in this conversation or previous sessions:"
        )
        parts.append("")

        for block in self.blocks:
            parts.append(f"--- Context Block (Task: {block.task_description or 'General'}) ---")
            parts.append(block.content)
            parts.append("")

        parts.append("</archived-context>")
        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "blocks": [b.to_dict() for b in self.blocks],
            "total_tokens": self.total_tokens,
            "trigger": self.trigger,
        }


class ContextRetriever:
    """
    Retrieves relevant archived context for injection.

    Analyzes the current conversation and user query to determine
    what archived context might be relevant.
    """

    def __init__(self) -> None:
        self._searcher = get_searcher()
        self._counter = TokenCounter()
        self._event_bus = get_event_bus()

    def retrieve_for_query(
        self,
        query: str,
        session_id: str,
        max_tokens: int | None = None,
    ) -> RetrievalContext:
        """
        Retrieve context relevant to a user query.

        Args:
            query: User's query/message
            session_id: Current session ID
            max_tokens: Maximum tokens to retrieve

        Returns:
            RetrievalContext with relevant blocks
        """
        config = get_config()

        if not config.rlm.enabled or not config.rlm.auto_retrieve:
            return RetrievalContext()

        # Set default max tokens (10% of context limit)
        if max_tokens is None:
            max_tokens = int(self._counter.get_model_limit(config.model) * 0.1)

        # Search for relevant blocks
        results = self._searcher.search(
            query=query,
            session_id=None,  # Search across all sessions
            limit=20,
        )

        # Filter by threshold
        threshold = config.rlm.semantic_search.get(
            "proactive_threshold", ANALYSIS_SIMILARITY_THRESHOLD
        )
        relevant_results = [r for r in results if r.score >= threshold]

        if not relevant_results:
            return RetrievalContext()

        # Select blocks within token budget
        selected_blocks = self._select_within_budget(relevant_results, max_tokens)

        if not selected_blocks:
            return RetrievalContext()

        total_tokens = sum(b.tokens for b in selected_blocks)

        context = RetrievalContext(
            blocks=selected_blocks,
            total_tokens=total_tokens,
            trigger=f"query: {query[:50]}...",
        )

        # Emit event
        self._emit_retrieval_event(session_id, context)

        logger.info(
            f"Retrieved {len(selected_blocks)} context blocks ({total_tokens} tokens) for query"
        )

        return context

    def retrieve_for_task(
        self,
        task_description: str,
        session_id: str,
        max_tokens: int | None = None,
    ) -> RetrievalContext:
        """
        Retrieve context relevant to a task being worked on.

        Args:
            task_description: Description of the current task
            session_id: Current session ID
            max_tokens: Maximum tokens to retrieve

        Returns:
            RetrievalContext with relevant blocks
        """
        return self.retrieve_for_query(
            query=task_description,
            session_id=session_id,
            max_tokens=max_tokens,
        )

    def retrieve_for_message(
        self,
        message: Message,
        session_id: str,
        max_tokens: int | None = None,
    ) -> RetrievalContext:
        """
        Retrieve context based on a message's content.

        Args:
            message: Message to analyze
            session_id: Current session ID
            max_tokens: Maximum tokens to retrieve

        Returns:
            RetrievalContext with relevant blocks
        """
        # Extract text from message parts
        text_parts = []
        for part in message.parts:
            if part.type == PartType.TEXT:
                text_parts.append(part.content.get("text", ""))

        if not text_parts:
            return RetrievalContext()

        query = " ".join(text_parts)
        return self.retrieve_for_query(query, session_id, max_tokens)

    def retrieve_recent(
        self,
        session_id: str,
        limit: int = 5,
    ) -> RetrievalContext:
        """
        Retrieve most recent archived blocks for a session.

        Args:
            session_id: Session ID
            limit: Maximum blocks to retrieve

        Returns:
            RetrievalContext with recent blocks
        """
        blocks = self._searcher.get_recent(session_id=session_id, limit=limit)

        if not blocks:
            return RetrievalContext()

        total_tokens = sum(b.tokens for b in blocks)

        return RetrievalContext(
            blocks=blocks,
            total_tokens=total_tokens,
            trigger="recent",
        )

    def retrieve_by_task_id(self, task_id: str) -> RetrievalContext:
        """
        Retrieve context for a specific task.

        Args:
            task_id: Task ID to look up

        Returns:
            RetrievalContext with task's archived content
        """
        block = self._searcher.get_by_task(task_id)

        if not block:
            return RetrievalContext()

        return RetrievalContext(
            blocks=[block],
            total_tokens=block.tokens,
            trigger=f"task: {task_id}",
        )

    def _select_within_budget(
        self,
        results: list[SearchResult],
        max_tokens: int,
    ) -> list[ContextBlock]:
        """Select blocks that fit within token budget."""
        selected = []
        total_tokens = 0

        for result in results:
            if total_tokens + result.block.tokens > max_tokens:
                continue

            selected.append(result.block)
            total_tokens += result.block.tokens

        return selected

    def _emit_retrieval_event(
        self,
        session_id: str,
        context: RetrievalContext,
    ) -> None:
        """Emit context retrieved event."""
        self._event_bus.emit_sync(
            Event(
                type=EventType.RLM_CONTEXT_RETRIEVED,
                data={
                    "session_id": session_id,
                    "block_count": len(context.blocks),
                    "total_tokens": context.total_tokens,
                    "trigger": context.trigger,
                },
            )
        )


# Functions for the mcp_rlm_query tool


def search(query: str, limit: int = 10) -> list[dict]:
    """Search archived context by keywords."""
    searcher = get_searcher()
    results = searcher.search(query=query, limit=limit)
    return [r.to_dict() for r in results]


def get_recent(n: int = 10) -> list[dict]:
    """Get the N most recent context blocks."""
    searcher = get_searcher()
    blocks = searcher.get_recent(limit=n)
    return [b.to_dict() for b in blocks]


def get_by_task(task_id: str) -> dict | None:
    """Get context for a specific task ID."""
    searcher = get_searcher()
    block = searcher.get_by_task(task_id)
    return block.to_dict() if block else None


def get_by_session(session_id: str) -> list[dict]:
    """Get all blocks from a specific session."""
    searcher = get_searcher()
    blocks = searcher.get_recent(session_id=session_id, limit=MAX_CONTEXT_BLOCKS)
    return [b.to_dict() for b in blocks]


def list_tasks() -> list[dict]:
    """List all archived tasks."""
    searcher = get_searcher()
    blocks = searcher.get_recent(limit=MAX_CONTEXT_BLOCKS)
    tasks = []
    for block in blocks:
        if block.task_id:
            tasks.append(
                {
                    "task_id": block.task_id,
                    "description": block.task_description,
                    "session_id": block.session_id,
                    "tokens": block.tokens,
                    "created_at": block.created_at.isoformat(),
                }
            )
    return tasks


def list_sessions() -> list[dict]:
    """List all sessions with archived context."""
    searcher = get_searcher()
    blocks = searcher.get_recent(limit=MAX_CONTEXT_BLOCKS)

    sessions: dict[str, dict] = {}
    for block in blocks:
        if block.session_id not in sessions:
            sessions[block.session_id] = {
                "session_id": block.session_id,
                "block_count": 0,
                "total_tokens": 0,
                "latest": block.created_at.isoformat(),
            }
        sessions[block.session_id]["block_count"] += 1
        sessions[block.session_id]["total_tokens"] += block.tokens

    return list(sessions.values())


def get_retriever() -> ContextRetriever:
    """
    Get the global retriever instance.

    Prefer using pinkyclawd.core.get_retriever() for consistency.
    """
    from pinkyclawd.core.state import get_state_factory
    return get_state_factory().retriever
