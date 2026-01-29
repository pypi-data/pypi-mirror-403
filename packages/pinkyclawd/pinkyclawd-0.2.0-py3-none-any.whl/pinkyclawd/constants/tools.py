"""
Tool-related constants.

Configuration values for tool execution, file operations,
timeouts, and output formatting.
"""

from __future__ import annotations

from typing import Final

# =============================================================================
# FILE READING
# =============================================================================

# Default number of lines to read from files
READ_DEFAULT_LIMIT: Final[int] = 2000

# Maximum line length before truncation
READ_MAX_LINE_LENGTH: Final[int] = 2000

# Maximum file size to read (in bytes)
READ_MAX_FILE_SIZE: Final[int] = 10_000_000  # 10MB

# =============================================================================
# OUTPUT TRUNCATION
# =============================================================================

# Maximum output length for tool results
TOOL_OUTPUT_MAX_LENGTH: Final[int] = 30_000

# Truncation length for display purposes
DISPLAY_TRUNCATION_LENGTH: Final[int] = 1000

# Maximum lines in truncated output
TRUNCATED_OUTPUT_MAX_LINES: Final[int] = 100

# =============================================================================
# TIMEOUTS
# =============================================================================

# Default tool execution timeout (in seconds)
TOOL_DEFAULT_TIMEOUT: Final[int] = 120

# Extended timeout for long-running operations (in seconds)
TOOL_EXTENDED_TIMEOUT: Final[int] = 600

# Bash command timeout (in milliseconds)
BASH_TIMEOUT_MS: Final[int] = 120_000

# Maximum bash timeout allowed (in milliseconds)
BASH_MAX_TIMEOUT_MS: Final[int] = 600_000

# =============================================================================
# SEARCH AND GREP
# =============================================================================

# Default number of context lines for grep
GREP_DEFAULT_CONTEXT: Final[int] = 2

# Maximum matches to return from grep
GREP_MAX_MATCHES: Final[int] = 500

# Maximum file count for glob results
GLOB_MAX_FILES: Final[int] = 1000

# =============================================================================
# SESSION LIMITS
# =============================================================================

# Maximum sessions to list
SESSION_LIST_LIMIT: Final[int] = 1000

# Maximum messages per session to display
SESSION_MAX_MESSAGES: Final[int] = 1000

# =============================================================================
# BATCH OPERATIONS
# =============================================================================

# Maximum concurrent operations in batch
BATCH_MAX_CONCURRENT: Final[int] = 10

# Batch operation timeout (in seconds)
BATCH_TIMEOUT: Final[int] = 300

# =============================================================================
# WEB OPERATIONS
# =============================================================================

# Web fetch timeout (in seconds)
WEB_FETCH_TIMEOUT: Final[int] = 30

# Maximum response size for web fetch (in bytes)
WEB_FETCH_MAX_SIZE: Final[int] = 5_000_000  # 5MB

# Web search result limit
WEB_SEARCH_MAX_RESULTS: Final[int] = 10

# =============================================================================
# LSP OPERATIONS
# =============================================================================

# LSP operation timeout (in seconds)
LSP_TIMEOUT: Final[int] = 30

# Maximum references to return from LSP
LSP_MAX_REFERENCES: Final[int] = 100

# =============================================================================
# PERMISSION FLAGS
# =============================================================================

# File operation permission flags
PERMISSION_READ: Final[str] = "read"
PERMISSION_WRITE: Final[str] = "write"
PERMISSION_EXECUTE: Final[str] = "execute"
PERMISSION_NETWORK: Final[str] = "network"
