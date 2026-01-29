"""
RLM conversation handler.

Integrates RLM context management into the conversation flow:
- Injects relevant archived context before sending to provider
- Tracks token usage across messages
- Triggers archival when threshold is reached
- Detects task completion phrases to trigger automatic archival
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass
from typing import Any

from pinkyclawd.config.settings import get_config
from pinkyclawd.config.storage import Message, MessagePart, MessageRole, PartType
from pinkyclawd.rlm.context import get_context_manager, ContextState
from pinkyclawd.rlm.retrieve import get_retriever, RetrievalContext
from pinkyclawd.rlm.archive import get_archiver
from pinkyclawd.rlm.auto_inject import analyze_with_threshold, AutoInjectResult
from pinkyclawd.rlm.display import (
    display_retrieval_start,
    display_retrieval_result,
    display_injection,
    display_context_status,
)


# Task completion phrase patterns for automatic archival detection
# These patterns indicate that a task or topic has been completed
COMPLETION_PHRASES = [
    re.compile(r"\b(i'?m\s+)?done(\s+with|\s+here|\.|\!|\s*$)", re.IGNORECASE),
    re.compile(r"\b(we'?re\s+)?finished(\s+with|\s+here|\.|\!|\s*$)", re.IGNORECASE),
    re.compile(r"\b(that'?s\s+)?(all\s+)?complete(d)?(\s+now)?(\.|!|\s*$)", re.IGNORECASE),
    re.compile(r"\bthat'?s\s+(all|it|everything)(\s+for\s+now)?(\.|!|\s*$)", re.IGNORECASE),
    re.compile(r"\bmoving\s+on(\s+to|\s+now)?", re.IGNORECASE),
    re.compile(r"\bnext\s+task", re.IGNORECASE),
    re.compile(r"\blet'?s\s+(move|switch|go)\s+(on|to)", re.IGNORECASE),
    re.compile(r"\bwrap(ping)?\s+(this\s+)?up", re.IGNORECASE),
]


def detect_task_completion(message: str) -> bool:
    """
    Detect if a message indicates task completion.

    Args:
        message: The message text to analyze

    Returns:
        True if the message contains task completion phrases
    """
    return any(pattern.search(message) for pattern in COMPLETION_PHRASES)


logger = logging.getLogger(__name__)


@dataclass
class RLMContext:
    """RLM context state for a conversation turn."""

    session_id: str
    retrieved_context: RetrievalContext | None = None
    context_state: ContextState | None = None
    system_injection: str = ""

    @property
    def has_retrieved_context(self) -> bool:
        return self.retrieved_context is not None and not self.retrieved_context.is_empty


class RLMHandler:
    """
    Handles RLM integration for conversations.

    Call before sending messages to provider to:
    - Check if relevant context should be injected
    - Track token usage
    - Trigger archival when needed
    """

    _instance: RLMHandler | None = None

    def __new__(cls) -> RLMHandler:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._context_manager = get_context_manager()
        self._retriever = get_retriever()
        self._archiver = get_archiver()
        self._config = get_config()
        self._initialized = True

    def prepare_for_query(
        self,
        session_id: str,
        user_query: str,
        messages: list[Message],
        model: str | None = None,
    ) -> RLMContext:
        """
        Prepare RLM context for a user query.

        Call this before sending messages to the provider to:
        1. Retrieve relevant archived context
        2. Update token tracking
        3. Get any system message injection needed

        Args:
            session_id: Current session ID
            user_query: The user's query text
            messages: Current conversation messages
            model: Model being used (for token limits)

        Returns:
            RLMContext with retrieval info and system injection
        """
        rlm_context = RLMContext(session_id=session_id)

        if not self._config.rlm.enabled:
            return rlm_context

        # Update context state from current messages
        context_state = self._context_manager.update_from_messages(
            session_id=session_id,
            messages=messages,
            model=model or self._config.model,
        )
        rlm_context.context_state = context_state

        # Only retrieve if auto-retrieve is enabled
        if self._config.rlm.auto_retrieve:
            # Show retrieval is starting
            display_retrieval_start(user_query, session_id)

            retrieved = self._retriever.retrieve_for_query(
                query=user_query,
                session_id=session_id,
            )

            # Show retrieval result
            display_retrieval_result(retrieved)

            if not retrieved.is_empty:
                rlm_context.retrieved_context = retrieved
                rlm_context.system_injection = retrieved.to_system_message()
                logger.info(
                    f"Retrieved {len(retrieved.blocks)} context blocks "
                    f"({retrieved.total_tokens} tokens) for query"
                )

        return rlm_context

    def get_augmented_messages(
        self,
        messages: list[Message],
        rlm_context: RLMContext,
    ) -> list[Message]:
        """
        Get messages augmented with RLM context.

        Adds retrieved context as a system message if available.

        Args:
            messages: Original conversation messages
            rlm_context: RLM context from prepare_for_query

        Returns:
            Messages with context injection if applicable
        """
        if not rlm_context.has_retrieved_context:
            return messages

        # Display injection is happening
        display_injection(rlm_context.retrieved_context)

        # Create system message with archived context
        context_message = Message(
            id="rlm_context",
            session_id=rlm_context.session_id,
            role=MessageRole.SYSTEM,
            parts=[
                MessagePart(
                    id="rlm_context_part",
                    message_id="rlm_context",
                    type=PartType.TEXT,
                    content={"text": rlm_context.system_injection},
                )
            ],
        )

        # Insert after any existing system messages
        augmented = []
        system_added = False

        for msg in messages:
            augmented.append(msg)
            # Add context after last system message
            if msg.role == MessageRole.SYSTEM and not system_added:
                augmented.append(context_message)
                system_added = True

        # If no system messages, add at the beginning
        if not system_added:
            augmented.insert(0, context_message)

        return augmented

    def after_response(
        self,
        session_id: str,
        assistant_message: Message,
        model: str | None = None,
    ) -> ContextState:
        """
        Call after receiving a response from the provider.

        Updates token tracking with the new assistant message.

        Args:
            session_id: Session ID
            assistant_message: The assistant's response
            model: Model used

        Returns:
            Updated context state
        """
        return self._context_manager.add_message(
            session_id=session_id,
            message=assistant_message,
            model=model,
        )

    def force_compact(self, session_id: str) -> bool:
        """
        Force compaction of a session.

        Archives oldest messages immediately.

        Args:
            session_id: Session to compact

        Returns:
            True if compaction succeeded
        """
        result = self._archiver.archive_oldest(session_id)
        return result.success

    def get_context_state(self, session_id: str) -> ContextState:
        """Get current context state for a session."""
        return self._context_manager.get_state(session_id)

    def archive_task(
        self,
        session_id: str,
        task_id: str,
        task_description: str,
        messages: list[Message],
    ) -> bool:
        """
        Archive messages related to a completed task.

        Called when a todo item is marked as completed to preserve
        the task context for future retrieval.

        Args:
            session_id: Session ID
            task_id: Completed task/todo ID
            task_description: Description of the task
            messages: Messages related to the task

        Returns:
            True if archival succeeded
        """
        if not self._config.rlm.enabled:
            return False

        if not messages:
            logger.debug(f"No messages to archive for task {task_id}")
            return False

        result = self._archiver.archive_task(
            session_id=session_id,
            task_id=task_id,
            task_description=task_description,
            messages=messages,
        )

        if result.success:
            logger.info(
                f"Archived task '{task_description}': "
                f"{result.messages_archived} messages, {result.tokens_archived} tokens"
            )

        return result.success

    def archive_on_session_end(self, session_id: str, messages: list[Message]) -> bool:
        """
        Archive context when a session ends.

        Uses a lower threshold (25%) than incremental archival to
        preserve context that might be useful in future sessions.

        Args:
            session_id: Session ID
            messages: All session messages

        Returns:
            True if archival was performed
        """
        if not self._config.rlm.enabled:
            return False

        # Check if we should archive based on 25% threshold
        if not self._context_manager.check_session_end_archival(session_id):
            logger.debug(f"Session {session_id} below session-end archival threshold")
            return False

        result = self._archiver.archive_messages(
            session_id=session_id,
            messages=messages,
            task_description="Session end archival",
        )

        if result.success:
            logger.info(
                f"Session-end archival for {session_id}: "
                f"{result.messages_archived} messages, {result.tokens_archived} tokens"
            )

        return result.success

    def check_auto_inject(
        self,
        message: str,
        session_id: str,
    ) -> AutoInjectResult:
        """
        Check if a message should trigger auto-injection of archived context.

        Uses pattern-based detection and semantic relevance to determine
        if past context should be automatically retrieved.

        Args:
            message: User message to analyze
            session_id: Current session ID

        Returns:
            AutoInjectResult with injection decision and context
        """
        if not self._config.rlm.enabled:
            return AutoInjectResult(
                should_inject=False,
                query="",
                trigger="rlm_disabled",
            )

        return analyze_with_threshold(
            message=message,
            session_id=session_id,
            limit=self._config.rlm.max_blocks_to_retrieve,
        )

    def check_completion_and_archive(
        self,
        message: str,
        session_id: str,
        messages: list[Message],
        task_description: str | None = None,
    ) -> bool:
        """
        Check if a message indicates task completion and trigger archival.

        Detects phrases like "done", "finished", "that's all", "moving on"
        and automatically archives recent context when detected.

        Args:
            message: The message to check for completion phrases
            session_id: Current session ID
            messages: Recent messages to archive if completion detected
            task_description: Optional description of the completed task

        Returns:
            True if completion was detected and archival was triggered
        """
        if not self._config.rlm.enabled:
            return False

        if not detect_task_completion(message):
            return False

        if not messages:
            logger.debug("Completion phrase detected but no messages to archive")
            return False

        # Generate a task description if not provided
        if not task_description:
            task_description = "Auto-archived task (completion phrase detected)"

        result = self._archiver.archive_messages(
            session_id=session_id,
            messages=messages,
            task_description=task_description,
        )

        if result.success:
            logger.info(
                f"Auto-archived on completion phrase: "
                f"{result.messages_archived} messages, {result.tokens_archived} tokens"
            )

        return result.success

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None


def get_rlm_handler() -> RLMHandler:
    """Get the global RLM handler instance."""
    return RLMHandler()


# Convenience functions for common operations


def prepare_messages_with_rlm(
    session_id: str,
    user_query: str,
    messages: list[Message],
    model: str | None = None,
) -> tuple[list[Message], RLMContext]:
    """
    Prepare messages with RLM context injection.

    This is the main integration point for RLM in the conversation flow.

    Args:
        session_id: Current session ID
        user_query: User's query text
        messages: Current conversation messages
        model: Model being used

    Returns:
        Tuple of (augmented_messages, rlm_context)
    """
    handler = get_rlm_handler()
    rlm_context = handler.prepare_for_query(session_id, user_query, messages, model)
    augmented = handler.get_augmented_messages(messages, rlm_context)
    return augmented, rlm_context


def update_after_response(
    session_id: str,
    assistant_message: Message,
    model: str | None = None,
) -> ContextState:
    """
    Update RLM state after receiving a response.

    Args:
        session_id: Session ID
        assistant_message: The assistant's response
        model: Model used

    Returns:
        Updated context state
    """
    return get_rlm_handler().after_response(session_id, assistant_message, model)
