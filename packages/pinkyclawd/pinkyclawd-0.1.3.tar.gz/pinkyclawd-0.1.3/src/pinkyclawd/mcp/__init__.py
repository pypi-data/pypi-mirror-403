"""
Model Context Protocol (MCP) integration for PinkyClawd.

Provides integration with external MCP servers for extended tool capabilities.
Supports both stdio and HTTP transports with OAuth2 authentication.
"""

from pinkyclawd.mcp.auth import (
    OAuth2Token,
    TokenStore,
    get_token_store,
)
from pinkyclawd.mcp.client import (
    MCPClient,
    MCPServer,
    MCPTool,
    get_mcp_client,
)
from pinkyclawd.mcp.oauth import (
    OAuth2Config,
    OAuth2Flow,
    start_oauth_flow,
    complete_oauth_flow,
)
from pinkyclawd.mcp.transport import (
    HTTPTransport,
    SSETransport,
    StdioTransport,
    Transport,
)

__all__ = [
    # Transport
    "Transport",
    "StdioTransport",
    "HTTPTransport",
    "SSETransport",
    # Auth
    "TokenStore",
    "get_token_store",
    "OAuth2Token",
    # OAuth
    "OAuth2Config",
    "OAuth2Flow",
    "start_oauth_flow",
    "complete_oauth_flow",
    # Client
    "MCPClient",
    "MCPServer",
    "MCPTool",
    "get_mcp_client",
]
