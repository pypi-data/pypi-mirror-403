"""
Context management and token counting for RLM.

Tracks token usage across the conversation and triggers archival
when the threshold is reached.
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from pinkyclawd.config.settings import get_config
from pinkyclawd.config.storage import Message, MessagePart, PartType
from pinkyclawd.constants import (
    CHARS_PER_TOKEN_TEXT,
    CHARS_PER_TOKEN_CODE,
    CHARS_PER_TOKEN_JSON,
    CHARS_PER_TOKEN_WHITESPACE,
    MESSAGE_ROLE_OVERHEAD,
    TOOL_USE_OVERHEAD,
    TOOL_RESULT_OVERHEAD,
    IMAGE_TOKEN_ESTIMATE,
    DEFAULT_PART_OVERHEAD,
    SPECIAL_CHAR_OVERHEAD_MULTIPLIER,
    SESSION_END_THRESHOLD_RATIO,
    SESSION_END_MIN_MESSAGES,
)
from pinkyclawd.constants.models import MODEL_LIMITS, DEFAULT_CONTEXT_LIMIT

logger = logging.getLogger(__name__)


@dataclass
class TokenEstimate:
    """Token usage estimate for a piece of content."""

    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def effective(self) -> int:
        """Tokens counting toward context limit (cached don't count)."""
        return self.total - self.cached_tokens


class TokenCounter:
    """
    Estimates token counts for various content types.

    Uses character-based heuristics since we don't have direct
    access to the tokenizer. Errs on the side of overestimation.
    """

    # Approximate characters per token for different content types
    CHARS_PER_TOKEN = {
        "text": CHARS_PER_TOKEN_TEXT,
        "code": CHARS_PER_TOKEN_CODE,
        "json": CHARS_PER_TOKEN_JSON,
        "whitespace": CHARS_PER_TOKEN_WHITESPACE,
    }

    def count_text(self, text: str) -> int:
        """Estimate tokens in plain text."""
        if not text:
            return 0

        # Detect content type
        code_indicators = ["{", "}", "()", "=>", "def ", "class ", "import ", "function"]
        is_code = any(ind in text for ind in code_indicators)

        chars_per_token = self.CHARS_PER_TOKEN["code" if is_code else "text"]

        # Count tokens
        base_count = len(text) / chars_per_token

        # Add overhead for special characters and formatting
        special_chars = len(re.findall(r"[^\w\s]", text))
        overhead = special_chars * SPECIAL_CHAR_OVERHEAD_MULTIPLIER

        return int(base_count + overhead)

    def count_message(self, message: Message) -> TokenEstimate:
        """Estimate tokens in a message."""
        total = 0

        # Role overhead
        total += MESSAGE_ROLE_OVERHEAD

        for part in message.parts:
            total += self.count_part(part)

        return TokenEstimate(
            input_tokens=total if message.role.value in ("user", "system") else 0,
            output_tokens=total if message.role.value == "assistant" else 0,
        )

    def count_part(self, part: MessagePart) -> int:
        """Estimate tokens in a message part."""
        if part.type == PartType.TEXT:
            return self.count_text(part.content.get("text", ""))

        if part.type == PartType.TOOL_USE:
            # Tool name + arguments
            name = part.content.get("name", "")
            args = str(part.content.get("arguments", {}))
            return self.count_text(name) + self.count_text(args) + TOOL_USE_OVERHEAD

        if part.type == PartType.TOOL_RESULT:
            result = str(part.content.get("result", ""))
            return self.count_text(result) + TOOL_RESULT_OVERHEAD

        if part.type == PartType.IMAGE:
            # Images have fixed token costs based on size
            return IMAGE_TOKEN_ESTIMATE

        return DEFAULT_PART_OVERHEAD

    def count_messages(self, messages: list[Message]) -> TokenEstimate:
        """Estimate total tokens across all messages."""
        estimate = TokenEstimate()
        for msg in messages:
            msg_estimate = self.count_message(msg)
            estimate.input_tokens += msg_estimate.input_tokens
            estimate.output_tokens += msg_estimate.output_tokens
        return estimate

    def get_model_limit(self, model: str) -> int:
        """Get context limit for a model."""
        # Extract base model name
        for key, limit in MODEL_LIMITS.items():
            if key in model.lower():
                return limit
        return DEFAULT_CONTEXT_LIMIT


@dataclass
class ContextState:
    """Current state of context usage."""

    session_id: str
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    model_limit: int = DEFAULT_CONTEXT_LIMIT
    message_count: int = 0
    archived_count: int = 0

    @property
    def usage_ratio(self) -> float:
        """Current context usage as a ratio (0.0 to 1.0)."""
        if self.model_limit == 0:
            return 0.0
        return self.total_tokens / self.model_limit

    @property
    def available_tokens(self) -> int:
        """Tokens available before hitting limit."""
        return max(0, self.model_limit - self.total_tokens)

    @property
    def should_archive(self) -> bool:
        """Whether archival should be triggered."""
        config = get_config()
        return self.usage_ratio >= config.rlm.threshold_ratio

    @property
    def should_archive_on_session_end(self) -> bool:
        """
        Whether to archive on session end.

        Uses a lower threshold than normal archival to preserve context that might
        be useful in future sessions, even if not yet at the archival threshold.
        """
        return (
            self.usage_ratio >= SESSION_END_THRESHOLD_RATIO
            and self.message_count > SESSION_END_MIN_MESSAGES
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "total_tokens": self.total_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_tokens": self.cached_tokens,
            "model_limit": self.model_limit,
            "message_count": self.message_count,
            "archived_count": self.archived_count,
            "usage_ratio": self.usage_ratio,
            "available_tokens": self.available_tokens,
        }


class ContextManager:
    """
    Manages context state and triggers archival.

    Tracks token usage across messages and determines when to
    archive older context to make room for new messages.

    Note: This class is managed by the StateFactory. Use get_context_manager()
    from pinkyclawd.core to get the singleton instance.
    """

    def __init__(self) -> None:
        self._counter = TokenCounter()
        self._states: dict[str, ContextState] = {}
        self._archive_callbacks: list[Callable[[str], None]] = []

    def get_state(self, session_id: str, model: str | None = None) -> ContextState:
        """Get or create context state for a session."""
        if session_id not in self._states:
            config = get_config()
            model = model or config.model
            self._states[session_id] = ContextState(
                session_id=session_id,
                model_limit=self._counter.get_model_limit(model),
            )
        return self._states[session_id]

    def update_from_messages(
        self,
        session_id: str,
        messages: list[Message],
        model: str | None = None,
    ) -> ContextState:
        """Update context state from current messages."""
        state = self.get_state(session_id, model)

        estimate = self._counter.count_messages(messages)
        state.total_tokens = estimate.total
        state.input_tokens = estimate.input_tokens
        state.output_tokens = estimate.output_tokens
        state.message_count = len(messages)

        # Check if archival is needed
        if state.should_archive:
            self._trigger_archive(session_id, state)

        return state

    def add_message(
        self,
        session_id: str,
        message: Message,
        model: str | None = None,
    ) -> ContextState:
        """Add a single message and update state."""
        state = self.get_state(session_id, model)

        estimate = self._counter.count_message(message)
        state.total_tokens += estimate.total
        state.input_tokens += estimate.input_tokens
        state.output_tokens += estimate.output_tokens
        state.message_count += 1

        if state.should_archive:
            self._trigger_archive(session_id, state)

        return state

    def mark_archived(self, session_id: str, tokens_archived: int) -> None:
        """Mark tokens as archived (removed from active context)."""
        state = self.get_state(session_id)
        state.total_tokens = max(0, state.total_tokens - tokens_archived)
        state.archived_count += 1
        logger.info(
            f"Archived {tokens_archived} tokens from session {session_id}, "
            f"now at {state.total_tokens}/{state.model_limit}"
        )

    def on_archive_needed(self, callback: Callable[[str], None]) -> None:
        """Register callback for when archival is needed."""
        self._archive_callbacks.append(callback)

    def _trigger_archive(self, session_id: str, state: ContextState) -> None:
        """Trigger archival callbacks."""
        logger.info(
            f"Context threshold reached for session {session_id}: "
            f"{state.usage_ratio:.1%} ({state.total_tokens}/{state.model_limit})"
        )
        for callback in self._archive_callbacks:
            try:
                callback(session_id)
            except Exception as e:
                logger.error(f"Archive callback error: {e}")

    def reset_session(self, session_id: str) -> None:
        """Reset state for a session."""
        if session_id in self._states:
            del self._states[session_id]

    def check_session_end_archival(self, session_id: str) -> bool:
        """
        Check if session-end archival should happen.

        Returns True if there's enough context to archive on session end,
        using a lower threshold than incremental archival.

        Args:
            session_id: Session to check

        Returns:
            True if session-end archival should occur
        """
        state = self.get_state(session_id)
        if state.should_archive_on_session_end:
            logger.info(
                f"Session-end archival triggered for session {session_id}: "
                f"{state.usage_ratio:.1%} ({state.total_tokens} tokens, "
                f"{state.message_count} messages)"
            )
            return True
        return False

    def reset(self, session_id: str | None = None) -> None:
        """
        Reset state.

        Args:
            session_id: If provided, only reset that session.
                       If None, reset all sessions.
        """
        if session_id is not None:
            self.reset_session(session_id)
        else:
            self._states.clear()
            self._archive_callbacks.clear()


def get_context_manager() -> ContextManager:
    """
    Get the global context manager.

    Prefer using pinkyclawd.core.get_context_manager() for consistency.
    """
    from pinkyclawd.core.state import get_state_factory
    return get_state_factory().context_manager
