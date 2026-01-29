"""
MCP transport implementations.

Provides stdio, HTTP, and SSE transports for MCP server communication.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


@dataclass
class MCPMessage:
    """An MCP protocol message."""

    jsonrpc: str = "2.0"
    id: int | str | None = None
    method: str | None = None
    params: dict[str, Any] | None = None
    result: Any = None
    error: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"jsonrpc": self.jsonrpc}
        if self.id is not None:
            d["id"] = self.id
        if self.method is not None:
            d["method"] = self.method
        if self.params is not None:
            d["params"] = self.params
        if self.result is not None:
            d["result"] = self.result
        if self.error is not None:
            d["error"] = self.error
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> MCPMessage:
        return cls(
            jsonrpc=d.get("jsonrpc", "2.0"),
            id=d.get("id"),
            method=d.get("method"),
            params=d.get("params"),
            result=d.get("result"),
            error=d.get("error"),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, s: str) -> MCPMessage:
        return cls.from_dict(json.loads(s))


class Transport(ABC):
    """Abstract base class for MCP transports."""

    @abstractmethod
    async def start(self) -> None:
        """Start the transport."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the transport."""
        ...

    @abstractmethod
    async def send(self, message: MCPMessage) -> None:
        """Send a message."""
        ...

    @abstractmethod
    async def receive(self) -> MCPMessage:
        """Receive a message."""
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        ...


class StdioTransport(Transport):
    """
    Stdio transport for local MCP servers.

    Communicates with MCP servers via stdin/stdout using JSON-RPC.
    """

    def __init__(
        self,
        command: list[str],
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> None:
        self.command = command
        self.env = env
        self.cwd = cwd
        self._process: subprocess.Popen | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the subprocess."""
        import os

        env = os.environ.copy()
        if self.env:
            env.update(self.env)

        self._process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=self.cwd,
        )

    async def stop(self) -> None:
        """Stop the subprocess."""
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

    async def send(self, message: MCPMessage) -> None:
        """Send a message via stdin."""
        if not self._process or not self._process.stdin:
            raise RuntimeError("Transport not started")

        async with self._lock:
            content = message.to_json()
            header = f"Content-Length: {len(content)}\r\n\r\n"
            data = (header + content).encode("utf-8")

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._process.stdin.write(data),  # type: ignore
            )
            await loop.run_in_executor(
                None,
                lambda: self._process.stdin.flush(),  # type: ignore
            )

    async def receive(self) -> MCPMessage:
        """Receive a message from stdout."""
        if not self._process or not self._process.stdout:
            raise RuntimeError("Transport not started")

        loop = asyncio.get_event_loop()

        while True:
            # Read header
            header_line = await loop.run_in_executor(
                None,
                lambda: self._process.stdout.readline(),  # type: ignore
            )

            if not header_line:
                raise RuntimeError("Connection closed")

            header = header_line.decode("utf-8").strip()

            if header.startswith("Content-Length:"):
                content_length = int(header.split(":")[1].strip())

                # Read empty line
                await loop.run_in_executor(
                    None,
                    lambda: self._process.stdout.readline(),  # type: ignore
                )

                # Read content
                content = await loop.run_in_executor(
                    None,
                    lambda: self._process.stdout.read(content_length),  # type: ignore
                )

                return MCPMessage.from_json(content.decode("utf-8"))

    @property
    def is_connected(self) -> bool:
        """Check if subprocess is running."""
        return self._process is not None and self._process.poll() is None


class HTTPTransport(Transport):
    """
    HTTP transport for remote MCP servers.

    Uses HTTP POST for request/response communication.
    """

    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.url = url
        self.headers = headers or {}
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._connected = False

    async def start(self) -> None:
        """Start the HTTP client."""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.headers,
        )
        self._connected = True

    async def stop(self) -> None:
        """Stop the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False

    async def send(self, message: MCPMessage) -> None:
        """Send a message via HTTP POST."""
        if not self._client:
            raise RuntimeError("Transport not started")

        # HTTP transport typically sends and receives in one call
        # Store the message for the receive call
        self._pending_message = message

    async def receive(self) -> MCPMessage:
        """Receive response from HTTP POST."""
        if not self._client:
            raise RuntimeError("Transport not started")

        if not hasattr(self, "_pending_message"):
            raise RuntimeError("No pending message")

        message = self._pending_message
        del self._pending_message

        response = await self._client.post(
            self.url,
            json=message.to_dict(),
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()

        return MCPMessage.from_dict(response.json())

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected


class SSETransport(Transport):
    """
    Server-Sent Events (SSE) transport for streaming MCP servers.

    Uses HTTP POST for requests and SSE for streaming responses.
    """

    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.url = url
        self.headers = headers or {}
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._connected = False
        self._message_queue: asyncio.Queue[MCPMessage] = asyncio.Queue()

    async def start(self) -> None:
        """Start the SSE client."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout, read=None),
            headers=self.headers,
        )
        self._connected = True

    async def stop(self) -> None:
        """Stop the SSE client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False

    async def send(self, message: MCPMessage) -> None:
        """Send a message via HTTP POST."""
        if not self._client:
            raise RuntimeError("Transport not started")

        # For SSE, we POST the request and stream the response
        async with self._client.stream(
            "POST",
            self.url,
            json=message.to_dict(),
            headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data:
                        msg = MCPMessage.from_json(data)
                        await self._message_queue.put(msg)

    async def receive(self) -> MCPMessage:
        """Receive a message from the SSE stream."""
        return await self._message_queue.get()

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected
