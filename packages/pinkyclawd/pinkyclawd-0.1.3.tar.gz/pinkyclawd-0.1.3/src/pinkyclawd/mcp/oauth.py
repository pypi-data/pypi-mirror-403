"""
OAuth2 flow implementation with PKCE support.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import secrets
import socket
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from pinkyclawd.mcp.auth import OAuth2Token, get_token_store


@dataclass
class OAuth2Config:
    """OAuth2 configuration."""

    client_id: str
    authorization_url: str
    token_url: str
    redirect_uri: str | None = None
    scope: str | None = None
    client_secret: str | None = None
    use_pkce: bool = True


class OAuth2Flow:
    """
    OAuth2 authorization flow with PKCE support.

    Handles browser-based authorization with a local callback server.
    """

    def __init__(self, config: OAuth2Config) -> None:
        self.config = config
        self._code_verifier: str | None = None
        self._state: str | None = None
        self._authorization_code: str | None = None

    def _generate_pkce(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge."""
        # Generate random verifier
        verifier = secrets.token_urlsafe(32)

        # Create challenge (S256)
        digest = hashlib.sha256(verifier.encode()).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

        return verifier, challenge

    def _find_available_port(self) -> int:
        """Find an available port for the callback server."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    def get_authorization_url(self, redirect_uri: str | None = None) -> str:
        """
        Get the authorization URL to open in the browser.

        Args:
            redirect_uri: Override redirect URI

        Returns:
            Authorization URL
        """
        # Generate state for CSRF protection
        self._state = secrets.token_urlsafe(16)

        params: dict[str, str] = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "state": self._state,
        }

        if redirect_uri or self.config.redirect_uri:
            params["redirect_uri"] = redirect_uri or self.config.redirect_uri or ""

        if self.config.scope:
            params["scope"] = self.config.scope

        # Add PKCE if enabled
        if self.config.use_pkce:
            self._code_verifier, code_challenge = self._generate_pkce()
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        return f"{self.config.authorization_url}?{urlencode(params)}"

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str | None = None,
    ) -> OAuth2Token:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback
            redirect_uri: Redirect URI used in authorization

        Returns:
            OAuth2Token
        """
        data: dict[str, str] = {
            "grant_type": "authorization_code",
            "client_id": self.config.client_id,
            "code": code,
        }

        if redirect_uri or self.config.redirect_uri:
            data["redirect_uri"] = redirect_uri or self.config.redirect_uri or ""

        if self.config.client_secret:
            data["client_secret"] = self.config.client_secret

        if self.config.use_pkce and self._code_verifier:
            data["code_verifier"] = self._code_verifier

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.token_url,
                data=data,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()

            return OAuth2Token.from_dict(response.json())

    async def refresh_token(self, token: OAuth2Token) -> OAuth2Token:
        """
        Refresh an expired token.

        Args:
            token: Token with refresh_token

        Returns:
            New OAuth2Token
        """
        if not token.refresh_token:
            raise ValueError("No refresh token available")

        data: dict[str, str] = {
            "grant_type": "refresh_token",
            "client_id": self.config.client_id,
            "refresh_token": token.refresh_token,
        }

        if self.config.client_secret:
            data["client_secret"] = self.config.client_secret

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.token_url,
                data=data,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()

            return OAuth2Token.from_dict(response.json())


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth2 callback."""

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress logging."""
        pass

    def do_GET(self) -> None:
        """Handle GET request (OAuth callback)."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            code = params["code"][0]
            state = params.get("state", [None])[0]

            # Store on server instance
            self.server.authorization_code = code  # type: ignore
            self.server.state = state  # type: ignore

            # Send success response
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""
                <html>
                <head><title>Authorization Successful</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to PinkyClawd.</p>
                </body>
                </html>
                """
            )
        elif "error" in params:
            error = params["error"][0]
            error_desc = params.get("error_description", [""])[0]

            self.server.error = f"{error}: {error_desc}"  # type: ignore

            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"""
                <html>
                <head><title>Authorization Failed</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>Authorization Failed</h1>
                    <p>{error}: {error_desc}</p>
                </body>
                </html>
                """.encode()
            )
        else:
            self.send_response(400)
            self.end_headers()


# Store pending OAuth flows for callback completion
_pending_flows: dict[str, tuple[OAuth2Flow, str]] = {}


async def start_oauth_flow(
    config: OAuth2Config,
    server_name: str,
    timeout: float = 120.0,
    open_browser: bool = True,
) -> OAuth2Token | None:
    """
    Start the OAuth2 authorization flow.

    Opens the browser for authorization and waits for callback.

    Args:
        config: OAuth2 configuration
        server_name: Name to identify the server for token storage
        timeout: Timeout in seconds for user to complete authorization

    Returns:
        OAuth2Token or None if failed
    """
    flow = OAuth2Flow(config)

    # Find available port for callback
    port = flow._find_available_port()
    redirect_uri = f"http://localhost:{port}/callback"

    # Get authorization URL
    auth_url = flow.get_authorization_url(redirect_uri)

    # Start callback server
    server = HTTPServer(("localhost", port), CallbackHandler)
    server.authorization_code = None  # type: ignore
    server.state = None  # type: ignore
    server.error = None  # type: ignore

    # Open browser
    print("Opening browser for authorization...")
    print(f"If browser doesn't open, visit: {auth_url}")
    webbrowser.open(auth_url)

    # Wait for callback
    loop = asyncio.get_event_loop()

    async def wait_for_callback() -> None:
        while server.authorization_code is None and server.error is None:  # type: ignore
            await loop.run_in_executor(None, server.handle_request)

    try:
        await asyncio.wait_for(wait_for_callback(), timeout=timeout)
    except TimeoutError:
        print("Authorization timed out")
        return None
    finally:
        server.server_close()

    if server.error:  # type: ignore
        print(f"Authorization error: {server.error}")  # type: ignore
        return None

    # Verify state
    if flow._state and server.state != flow._state:  # type: ignore
        print("State mismatch - possible CSRF attack")
        return None

    # Exchange code for token
    try:
        token = await flow.exchange_code(server.authorization_code, redirect_uri)  # type: ignore

        # Store token
        store = get_token_store()
        store.set(server_name, token)

        print("Authorization successful!")
        return token

    except Exception as e:
        print(f"Failed to exchange code: {e}")
        return None


async def complete_oauth_flow(
    server_name: str,
    code: str,
    state: str | None = None,
) -> OAuth2Token | None:
    """
    Complete an OAuth2 flow with the authorization code.

    This is called when receiving the OAuth callback with the code.

    Args:
        server_name: Name of the MCP server
        code: Authorization code from callback
        state: State parameter for verification

    Returns:
        OAuth2Token or None if failed
    """
    # Check if we have a pending flow for this server
    if server_name not in _pending_flows:
        raise ValueError(f"No pending OAuth flow for server: {server_name}")

    flow, redirect_uri = _pending_flows[server_name]

    # Verify state if provided
    if state and flow._state and state != flow._state:
        raise ValueError("State mismatch - possible CSRF attack")

    try:
        # Exchange code for token
        token = await flow.exchange_code(code, redirect_uri)

        # Store token
        store = get_token_store()
        store.set(server_name, token)

        # Clean up pending flow
        del _pending_flows[server_name]

        return token

    except Exception as e:
        # Clean up on error
        if server_name in _pending_flows:
            del _pending_flows[server_name]
        raise


def get_pending_flow(server_name: str) -> tuple[OAuth2Flow, str] | None:
    """Get a pending OAuth flow for a server."""
    return _pending_flows.get(server_name)


def register_pending_flow(server_name: str, flow: OAuth2Flow, redirect_uri: str) -> None:
    """Register a pending OAuth flow for callback completion."""
    _pending_flows[server_name] = (flow, redirect_uri)
