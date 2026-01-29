"""
MCP server management routes.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pinkyclawd.mcp import (
    OAuth2Config,
    get_mcp_client,
    start_oauth_flow,
    complete_oauth_flow,
)

router = APIRouter()


class MCPServerConfig(BaseModel):
    """Configuration for adding an MCP server."""

    name: str
    type: str = "stdio"  # "stdio" or "http"
    command: list[str] | None = None  # For stdio
    url: str | None = None  # For http
    env: dict[str, str] | None = None
    headers: dict[str, str] | None = None


class MCPServerStatus(BaseModel):
    """Status of an MCP server."""

    name: str
    connected: bool
    tools: list[str]
    capabilities: dict


class MCPToolCall(BaseModel):
    """Request to call an MCP tool."""

    server: str
    tool: str
    arguments: dict


@router.get("")
async def list_mcp_servers():
    """List all configured MCP servers."""
    client = get_mcp_client()
    servers = []

    for name in client.list_servers():
        server = client.get_server(name)
        if server:
            servers.append(
                MCPServerStatus(
                    name=name,
                    connected=server.transport.is_connected,
                    tools=[t.name for t in server.tools],
                    capabilities=server.capabilities,
                )
            )

    return {"servers": servers}


@router.post("")
async def add_mcp_server(config: MCPServerConfig):
    """Add a new MCP server."""
    client = get_mcp_client()

    if config.type == "stdio":
        if not config.command:
            raise HTTPException(
                status_code=400,
                detail="Command is required for stdio servers",
            )

        success = await client.add_stdio_server(
            name=config.name,
            command=config.command,
            env=config.env,
        )
    elif config.type == "http":
        if not config.url:
            raise HTTPException(
                status_code=400,
                detail="URL is required for HTTP servers",
            )

        success = await client.add_http_server(
            name=config.name,
            url=config.url,
            headers=config.headers,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown server type: {config.type}")

    if not success:
        raise HTTPException(status_code=500, detail="Failed to add server")

    server = client.get_server(config.name)
    if not server:
        raise HTTPException(status_code=500, detail="Server not found after adding")

    return MCPServerStatus(
        name=config.name,
        connected=server.transport.is_connected,
        tools=[t.name for t in server.tools],
        capabilities=server.capabilities,
    )


@router.delete("/{name}")
async def remove_mcp_server(name: str):
    """Remove an MCP server."""
    client = get_mcp_client()

    server = client.get_server(name)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    await client.remove_server(name)

    return {"status": "removed", "name": name}


@router.get("/{name}/tools")
async def list_mcp_tools(name: str):
    """List tools provided by an MCP server."""
    client = get_mcp_client()

    server = client.get_server(name)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    return {
        "server": name,
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in server.tools
        ],
    }


@router.post("/{name}/tools/{tool_name}")
async def call_mcp_tool(name: str, tool_name: str, body: dict):
    """Call a tool on an MCP server."""
    client = get_mcp_client()

    server = client.get_server(name)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    # Check if tool exists
    tool = client.get_tool(name, tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    try:
        result = await client.call_tool(name, tool_name, body)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/{name}/resources")
async def list_mcp_resources(name: str):
    """List resources provided by an MCP server."""
    client = get_mcp_client()

    server = client.get_server(name)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    resources = await client.list_resources(name)

    return {
        "server": name,
        "resources": [
            {
                "uri": r.uri,
                "name": r.name,
                "description": r.description,
                "mime_type": r.mime_type,
            }
            for r in resources
        ],
    }


@router.get("/{name}/resources/{resource_uri:path}")
async def read_mcp_resource(name: str, resource_uri: str):
    """Read a resource from an MCP server."""
    client = get_mcp_client()

    server = client.get_server(name)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        result = await client.read_resource(name, resource_uri)
        return {"success": True, "content": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


class OAuthConfig(BaseModel):
    """OAuth configuration for MCP server authentication."""

    client_id: str
    authorization_url: str
    token_url: str
    scope: str | None = None


@router.post("/{name}/auth")
async def start_mcp_auth(name: str, config: OAuthConfig):
    """
    Start OAuth flow for an MCP server.

    This initiates the browser-based OAuth flow and returns when complete.
    """
    oauth_config = OAuth2Config(
        client_id=config.client_id,
        authorization_url=config.authorization_url,
        token_url=config.token_url,
        scope=config.scope,
    )

    token = await start_oauth_flow(oauth_config, name)

    if not token:
        raise HTTPException(status_code=400, detail="OAuth flow failed")

    return {
        "status": "authenticated",
        "server": name,
        "expires_at": token.expires_at.isoformat() if token.expires_at else None,
    }


@router.delete("/{name}/auth")
async def logout_mcp_server(name: str):
    """Remove OAuth credentials for an MCP server."""
    from pinkyclawd.mcp import get_token_store

    store = get_token_store()
    deleted = store.delete(name)

    if not deleted:
        raise HTTPException(status_code=404, detail="No credentials found")

    return {"status": "logged_out", "server": name}


class OAuthCallback(BaseModel):
    """OAuth callback with authorization code."""

    code: str
    state: str | None = None


@router.post("/{name}/auth/callback")
async def oauth_callback(name: str, body: OAuthCallback):
    """
    Complete OAuth flow with authorization code.

    This is called by the OAuth redirect handler to complete the flow.
    """
    from pinkyclawd.mcp import complete_oauth_flow

    try:
        token = await complete_oauth_flow(name, body.code, body.state)

        if not token:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")

        return {
            "status": "authenticated",
            "server": name,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{name}/auth/authenticate")
async def authenticate_mcp_server(name: str, config: OAuthConfig):
    """
    Start OAuth and wait for callback (opens browser).

    This is a combined endpoint that initiates OAuth and waits for
    the callback to complete.
    """
    import webbrowser

    oauth_config = OAuth2Config(
        client_id=config.client_id,
        authorization_url=config.authorization_url,
        token_url=config.token_url,
        scope=config.scope,
    )

    # Start the OAuth flow (this will open the browser)
    token = await start_oauth_flow(oauth_config, name, open_browser=True)

    if not token:
        raise HTTPException(status_code=400, detail="OAuth flow failed or was cancelled")

    return {
        "status": "authenticated",
        "server": name,
        "expires_at": token.expires_at.isoformat() if token.expires_at else None,
    }


@router.post("/{name}/connect")
async def connect_mcp_server(name: str):
    """
    Explicitly connect to an MCP server.

    Use this to reconnect a previously disconnected server or
    to establish an initial connection.
    """
    client = get_mcp_client()

    server = client.get_server(name)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        await client.connect_server(name)
        return {
            "status": "connected",
            "server": name,
            "tools": [t.name for t in server.tools],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect: {e}")


@router.post("/{name}/disconnect")
async def disconnect_mcp_server(name: str):
    """
    Disconnect from an MCP server.

    This closes the connection but keeps the server configuration.
    Use connect to re-establish the connection later.
    """
    client = get_mcp_client()

    server = client.get_server(name)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        await client.disconnect_server(name)
        return {"status": "disconnected", "server": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {e}")
