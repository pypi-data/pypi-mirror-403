"""
MCP client implementation.

Manages connections to MCP servers and provides tool discovery/execution.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pinkyclawd.mcp.auth import get_token_store
from pinkyclawd.mcp.transport import (
    HTTPTransport,
    MCPMessage,
    StdioTransport,
    Transport,
)


@dataclass
class MCPTool:
    """A tool provided by an MCP server."""

    name: str
    description: str
    input_schema: dict[str, Any]
    server_name: str

    def to_function_schema(self) -> dict[str, Any]:
        """Convert to function calling schema."""
        return {
            "name": f"mcp_{self.server_name}_{self.name}",
            "description": f"[{self.server_name}] {self.description}",
            "parameters": self.input_schema,
        }


@dataclass
class MCPResource:
    """A resource provided by an MCP server."""

    uri: str
    name: str
    description: str | None = None
    mime_type: str | None = None


@dataclass
class MCPServer:
    """Configuration and state for an MCP server."""

    name: str
    transport: Transport
    tools: list[MCPTool] = field(default_factory=list)
    resources: list[MCPResource] = field(default_factory=list)
    capabilities: dict[str, Any] = field(default_factory=dict)
    initialized: bool = False
    _request_id: int = 0


class MCPClient:
    """
    Client for interacting with MCP servers.

    Manages multiple server connections and provides unified access to tools.
    """

    def __init__(self) -> None:
        self._servers: dict[str, MCPServer] = {}
        self._lock = asyncio.Lock()

    async def add_server(
        self,
        name: str,
        transport: Transport,
    ) -> bool:
        """
        Add and initialize an MCP server.

        Args:
            name: Server name
            transport: Transport to use for communication

        Returns:
            True if server was added successfully
        """
        if name in self._servers:
            return True  # Already added

        server = MCPServer(name=name, transport=transport)

        try:
            await transport.start()
            await self._initialize_server(server)
            self._servers[name] = server
            return True
        except Exception as e:
            print(f"Failed to add server {name}: {e}")
            await transport.stop()
            return False

    async def add_stdio_server(
        self,
        name: str,
        command: list[str],
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> bool:
        """Add a stdio-based MCP server."""
        transport = StdioTransport(command, env, cwd)
        return await self.add_server(name, transport)

    async def add_http_server(
        self,
        name: str,
        url: str,
        headers: dict[str, str] | None = None,
        use_auth: bool = False,
    ) -> bool:
        """Add an HTTP-based MCP server."""
        # Add authentication if available
        headers = headers or {}
        if use_auth:
            store = get_token_store()
            token = store.get(name)
            if token and not token.is_expired:
                headers["Authorization"] = token.authorization_header()

        transport = HTTPTransport(url, headers)
        return await self.add_server(name, transport)

    async def remove_server(self, name: str) -> None:
        """Remove an MCP server."""
        if name not in self._servers:
            return

        server = self._servers[name]
        await server.transport.stop()
        del self._servers[name]

    async def connect_server(self, name: str) -> bool:
        """
        Connect or reconnect to an MCP server.

        Args:
            name: Server name

        Returns:
            True if connected successfully
        """
        server = self._servers.get(name)
        if not server:
            return False

        # If already connected, do nothing
        if server.transport.is_connected:
            return True

        try:
            await server.transport.start()

            # Re-initialize if needed
            if not server.initialized:
                await self._initialize_server(server)

            return True
        except Exception as e:
            print(f"Failed to connect to {name}: {e}")
            return False

    async def disconnect_server(self, name: str) -> bool:
        """
        Disconnect from an MCP server.

        Keeps the server configuration but closes the connection.

        Args:
            name: Server name

        Returns:
            True if disconnected successfully
        """
        server = self._servers.get(name)
        if not server:
            return False

        try:
            await server.transport.stop()
            server.initialized = False
            return True
        except Exception as e:
            print(f"Failed to disconnect from {name}: {e}")
            return False

    async def remove_all(self) -> None:
        """Remove all servers."""
        for name in list(self._servers.keys()):
            await self.remove_server(name)

    def get_server(self, name: str) -> MCPServer | None:
        """Get a server by name."""
        return self._servers.get(name)

    def list_servers(self) -> list[str]:
        """List all server names."""
        return list(self._servers.keys())

    def get_all_tools(self) -> list[MCPTool]:
        """Get all tools from all servers."""
        tools = []
        for server in self._servers.values():
            tools.extend(server.tools)
        return tools

    def get_tool(self, server_name: str, tool_name: str) -> MCPTool | None:
        """Get a specific tool."""
        server = self._servers.get(server_name)
        if not server:
            return None

        for tool in server.tools:
            if tool.name == tool_name:
                return tool
        return None

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """
        Call a tool on a server.

        Args:
            server_name: Name of the server
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Tool result
        """
        server = self._servers.get(server_name)
        if not server:
            raise ValueError(f"Server not found: {server_name}")

        if not server.initialized:
            raise RuntimeError(f"Server not initialized: {server_name}")

        result = await self._send_request(
            server,
            "tools/call",
            {"name": tool_name, "arguments": arguments},
        )

        return result

    async def list_resources(self, server_name: str) -> list[MCPResource]:
        """List resources from a server."""
        server = self._servers.get(server_name)
        if not server:
            return []

        if not server.capabilities.get("resources"):
            return []

        result = await self._send_request(server, "resources/list", {})
        resources = []
        for r in result.get("resources", []):
            resources.append(
                MCPResource(
                    uri=r["uri"],
                    name=r.get("name", r["uri"]),
                    description=r.get("description"),
                    mime_type=r.get("mimeType"),
                )
            )
        server.resources = resources
        return resources

    async def read_resource(self, server_name: str, uri: str) -> dict[str, Any]:
        """Read a resource from a server."""
        server = self._servers.get(server_name)
        if not server:
            raise ValueError(f"Server not found: {server_name}")

        return await self._send_request(
            server,
            "resources/read",
            {"uri": uri},
        )

    async def _initialize_server(self, server: MCPServer) -> None:
        """Initialize an MCP server."""
        # Send initialize request
        result = await self._send_request(
            server,
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                },
                "clientInfo": {
                    "name": "pinkyclawd",
                    "version": "1.0.0",
                },
            },
        )

        server.capabilities = result.get("capabilities", {})

        # Send initialized notification
        await self._send_notification(server, "notifications/initialized", {})

        # List tools if supported
        if server.capabilities.get("tools"):
            tools_result = await self._send_request(server, "tools/list", {})
            for tool_data in tools_result.get("tools", []):
                server.tools.append(
                    MCPTool(
                        name=tool_data["name"],
                        description=tool_data.get("description", ""),
                        input_schema=tool_data.get("inputSchema", {}),
                        server_name=server.name,
                    )
                )

        server.initialized = True

    async def _send_request(
        self,
        server: MCPServer,
        method: str,
        params: dict[str, Any],
    ) -> Any:
        """Send a request and wait for response."""
        async with self._lock:
            server._request_id += 1
            request_id = server._request_id

            message = MCPMessage(
                id=request_id,
                method=method,
                params=params,
            )

            await server.transport.send(message)
            response = await server.transport.receive()

            if response.error:
                raise RuntimeError(
                    response.error.get("message", "Unknown error")
                )

            return response.result

    async def _send_notification(
        self,
        server: MCPServer,
        method: str,
        params: dict[str, Any],
    ) -> None:
        """Send a notification (no response expected)."""
        message = MCPMessage(method=method, params=params)
        await server.transport.send(message)


# Global client instance
_client: MCPClient | None = None


def get_mcp_client() -> MCPClient:
    """Get the global MCP client."""
    global _client
    if _client is None:
        _client = MCPClient()
    return _client
