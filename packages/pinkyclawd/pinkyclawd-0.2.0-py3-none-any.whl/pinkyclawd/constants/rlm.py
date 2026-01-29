"""
RLM (Recursive Language Model) constants.

Centralized configuration values for context management, archival,
and semantic search thresholds.
"""

from __future__ import annotations

# =============================================================================
# ARCHIVAL THRESHOLDS
# =============================================================================

# Default ratio of context window usage that triggers automatic archival
# When context usage exceeds this ratio, older messages are archived
ARCHIVAL_THRESHOLD_RATIO: float = 0.33

# Lower threshold for session-end archival (preserves context for future sessions)
SESSION_END_THRESHOLD_RATIO: float = 0.25

# Minimum message count required before session-end archival can trigger
SESSION_END_MIN_MESSAGES: int = 5

# Target tokens to preserve after archival (as ratio of model limit)
POST_ARCHIVAL_TARGET_RATIO: float = 0.25

# =============================================================================
# SEMANTIC SEARCH THRESHOLDS
# =============================================================================

# Default minimum similarity score for semantic search results
SEMANTIC_SIMILARITY_THRESHOLD: float = 0.45

# Higher threshold for proactive/automatic context injection
PROACTIVE_INJECTION_THRESHOLD: float = 0.65

# Threshold for analyze_with_threshold function
ANALYSIS_SIMILARITY_THRESHOLD: float = 0.4

# =============================================================================
# SEARCH LIMITS
# =============================================================================

# Maximum number of context blocks to retrieve in a single search
MAX_CONTEXT_BLOCKS: int = 1000

# Default number of search results to return
DEFAULT_SEARCH_RESULTS: int = 10

# Maximum search results allowed
MAX_SEARCH_RESULTS: int = 100

# =============================================================================
# TOKEN ESTIMATION
# =============================================================================

# Approximate characters per token for different content types
CHARS_PER_TOKEN_TEXT: float = 4.0
CHARS_PER_TOKEN_CODE: float = 3.5
CHARS_PER_TOKEN_JSON: float = 3.0
CHARS_PER_TOKEN_WHITESPACE: float = 6.0

# Overhead tokens for message roles
MESSAGE_ROLE_OVERHEAD: int = 4

# Overhead tokens for tool use
TOOL_USE_OVERHEAD: int = 10

# Overhead tokens for tool results
TOOL_RESULT_OVERHEAD: int = 5

# Default token estimate for images
IMAGE_TOKEN_ESTIMATE: int = 1000

# Default overhead for unknown part types
DEFAULT_PART_OVERHEAD: int = 10

# Special character token overhead multiplier
SPECIAL_CHAR_OVERHEAD_MULTIPLIER: float = 0.5

# =============================================================================
# SUMMARIZATION
# =============================================================================

# Maximum tokens for summary generation
SUMMARY_MAX_TOKENS: int = 1000

# Maximum text length before truncation for summarization
SUMMARY_TRUNCATION_LENGTH: int = 1000

# =============================================================================
# EMBEDDING DIMENSIONS
# =============================================================================

# Standard embedding dimensions by provider
EMBEDDING_DIM_OPENAI_SMALL: int = 1536
EMBEDDING_DIM_OPENAI_LARGE: int = 3072
EMBEDDING_DIM_VOYAGE: int = 1024
EMBEDDING_DIM_GOOGLE: int = 768
EMBEDDING_DIM_MISTRAL: int = 1024
EMBEDDING_DIM_LOCAL: int = 384

# Default embedding dimension
DEFAULT_EMBEDDING_DIM: int = 1536

# =============================================================================
# GRAPH PROCESSING
# =============================================================================

# Maximum chunk size for content chunking (characters)
MAX_CHUNK_SIZE: int = 1000

# Overlap between chunks (characters)
CHUNK_OVERLAP: int = 100

# Minimum chunk size to avoid tiny fragments
MIN_CHUNK_SIZE: int = 100
