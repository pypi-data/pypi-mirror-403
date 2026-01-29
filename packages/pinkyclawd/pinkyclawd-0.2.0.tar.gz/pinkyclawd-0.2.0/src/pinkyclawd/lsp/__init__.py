"""
Language Server Protocol (LSP) integration for PinkyClawd.

Provides code intelligence features like go-to-definition, find references,
hover information, and symbol navigation.
"""

from pinkyclawd.lsp.client import LSPClient, get_lsp_client
from pinkyclawd.lsp.language import LANGUAGE_MAP, get_file_extension, get_language_id
from pinkyclawd.lsp.operations import (
    document_symbol,
    find_references,
    get_call_hierarchy,
    get_incoming_calls,
    get_outgoing_calls,
    get_symbol_kind_name,
    go_to_definition,
    go_to_implementation,
    hover,
    workspace_symbol,
)
from pinkyclawd.lsp.server import (
    LANGUAGE_SERVERS,
    LanguageServerConfig,
    get_server_for_language,
)

__all__ = [
    # Language utilities
    "get_language_id",
    "get_file_extension",
    "LANGUAGE_MAP",
    # Client
    "LSPClient",
    "get_lsp_client",
    # Server configuration
    "LanguageServerConfig",
    "get_server_for_language",
    "LANGUAGE_SERVERS",
    # Operations
    "go_to_definition",
    "find_references",
    "hover",
    "document_symbol",
    "workspace_symbol",
    "go_to_implementation",
    "get_call_hierarchy",
    "get_incoming_calls",
    "get_outgoing_calls",
    "get_symbol_kind_name",
]
