"""
Model-related constants.

Defines context window limits, output token limits, and other
model-specific configuration values.
"""

from __future__ import annotations

from typing import Final

# =============================================================================
# CONTEXT WINDOW LIMITS
# =============================================================================

# Claude 3 family context limits
CLAUDE_3_CONTEXT_LIMIT: Final[int] = 200_000
CLAUDE_SONNET_4_CONTEXT_LIMIT: Final[int] = 200_000
CLAUDE_OPUS_4_CONTEXT_LIMIT: Final[int] = 200_000
CLAUDE_HAIKU_CONTEXT_LIMIT: Final[int] = 200_000

# GPT-4 family context limits
GPT_4_CONTEXT_LIMIT: Final[int] = 128_000
GPT_4_TURBO_CONTEXT_LIMIT: Final[int] = 128_000
GPT_4O_CONTEXT_LIMIT: Final[int] = 128_000
GPT_4O_MINI_CONTEXT_LIMIT: Final[int] = 128_000

# Other model context limits
GEMINI_PRO_CONTEXT_LIMIT: Final[int] = 1_000_000
GEMINI_FLASH_CONTEXT_LIMIT: Final[int] = 1_000_000
MISTRAL_LARGE_CONTEXT_LIMIT: Final[int] = 128_000
LLAMA_3_CONTEXT_LIMIT: Final[int] = 128_000

# Default context limit for unknown models
DEFAULT_CONTEXT_LIMIT: Final[int] = 128_000

# Model limit lookup table
MODEL_LIMITS: dict[str, int] = {
    # Claude models
    "claude-3-opus": CLAUDE_3_CONTEXT_LIMIT,
    "claude-3-sonnet": CLAUDE_3_CONTEXT_LIMIT,
    "claude-3-haiku": CLAUDE_HAIKU_CONTEXT_LIMIT,
    "claude-sonnet-4": CLAUDE_SONNET_4_CONTEXT_LIMIT,
    "claude-opus-4": CLAUDE_OPUS_4_CONTEXT_LIMIT,
    "claude-haiku": CLAUDE_HAIKU_CONTEXT_LIMIT,
    # GPT models
    "gpt-4": GPT_4_CONTEXT_LIMIT,
    "gpt-4-turbo": GPT_4_TURBO_CONTEXT_LIMIT,
    "gpt-4o": GPT_4O_CONTEXT_LIMIT,
    "gpt-4o-mini": GPT_4O_MINI_CONTEXT_LIMIT,
    # Gemini models
    "gemini-pro": GEMINI_PRO_CONTEXT_LIMIT,
    "gemini-flash": GEMINI_FLASH_CONTEXT_LIMIT,
    # Other models
    "mistral-large": MISTRAL_LARGE_CONTEXT_LIMIT,
    "llama-3": LLAMA_3_CONTEXT_LIMIT,
    # Default
    "default": DEFAULT_CONTEXT_LIMIT,
}

# =============================================================================
# OUTPUT TOKEN LIMITS
# =============================================================================

# Default max output tokens
DEFAULT_MAX_OUTPUT_TOKENS: Final[int] = 4096

# Extended output limits for certain models
CLAUDE_MAX_OUTPUT_TOKENS: Final[int] = 8192
GPT_4_MAX_OUTPUT_TOKENS: Final[int] = 4096
GEMINI_MAX_OUTPUT_TOKENS: Final[int] = 8192

# =============================================================================
# MODEL IDENTIFIERS
# =============================================================================

# Default model identifiers
DEFAULT_ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
DEFAULT_OPENAI_MODEL: str = "gpt-4o"
DEFAULT_GOOGLE_MODEL: str = "gemini-1.5-pro"

# Embedding model identifiers
DEFAULT_OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
DEFAULT_VOYAGE_EMBEDDING_MODEL: str = "voyage-code-2"
DEFAULT_GOOGLE_EMBEDDING_MODEL: str = "text-embedding-004"
DEFAULT_MISTRAL_EMBEDDING_MODEL: str = "mistral-embed"

# =============================================================================
# API CONFIGURATION
# =============================================================================

# Default API base URLs
ANTHROPIC_API_BASE: str = "https://api.anthropic.com"
OPENAI_API_BASE: str = "https://api.openai.com/v1"
GOOGLE_API_BASE: str = "https://generativelanguage.googleapis.com/v1beta"

# Default timeout values (in seconds)
API_TIMEOUT_DEFAULT: int = 120
API_TIMEOUT_STREAM: int = 300

# Retry configuration
API_MAX_RETRIES: int = 3
API_RETRY_DELAY: float = 1.0
API_RETRY_BACKOFF: float = 2.0


def get_model_limit(model: str) -> int:
    """
    Get context window limit for a model.

    Args:
        model: Model identifier string

    Returns:
        Context window size in tokens
    """
    model_lower = model.lower()
    for key, limit in MODEL_LIMITS.items():
        if key in model_lower:
            return limit
    return DEFAULT_CONTEXT_LIMIT
