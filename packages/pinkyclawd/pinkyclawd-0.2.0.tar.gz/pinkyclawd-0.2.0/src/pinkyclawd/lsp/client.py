"""
LSP client implementation with JSON-RPC communication.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pinkyclawd.lsp.language import get_language_id
from pinkyclawd.lsp.server import LanguageServerConfig, get_server_for_language


@dataclass
class Position:
    """A position in a text document."""

    line: int  # 0-indexed
    character: int  # 0-indexed

    def to_dict(self) -> dict[str, int]:
        return {"line": self.line, "character": self.character}

    @classmethod
    def from_dict(cls, d: dict[str, int]) -> Position:
        return cls(line=d["line"], character=d["character"])


@dataclass
class Range:
    """A range in a text document."""

    start: Position
    end: Position

    def to_dict(self) -> dict[str, Any]:
        return {"start": self.start.to_dict(), "end": self.end.to_dict()}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Range:
        return cls(
            start=Position.from_dict(d["start"]),
            end=Position.from_dict(d["end"]),
        )


@dataclass
class Location:
    """A location in a document."""

    uri: str
    range: Range

    def to_dict(self) -> dict[str, Any]:
        return {"uri": self.uri, "range": self.range.to_dict()}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Location:
        return cls(uri=d["uri"], range=Range.from_dict(d["range"]))

    @property
    def file_path(self) -> str:
        """Get the file path from the URI."""
        if self.uri.startswith("file://"):
            return self.uri[7:]
        return self.uri


@dataclass
class LSPServerState:
    """State of an LSP server connection."""

    config: LanguageServerConfig
    process: subprocess.Popen | None = None
    reader: asyncio.StreamReader | None = None
    writer: asyncio.StreamWriter | None = None
    request_id: int = 0
    pending_requests: dict[int, asyncio.Future] = field(default_factory=dict)
    initialized: bool = False
    root_uri: str = ""
    open_documents: set[str] = field(default_factory=set)


class LSPClient:
    """
    Language Server Protocol client.

    Manages connections to language servers and provides LSP operations.
    """

    def __init__(self) -> None:
        self._servers: dict[str, LSPServerState] = {}
        self._language_to_server: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def start_server(
        self,
        config: LanguageServerConfig,
        root_path: Path,
    ) -> bool:
        """
        Start a language server.

        Args:
            config: Server configuration
            root_path: Root directory for the workspace

        Returns:
            True if server started successfully
        """
        if config.name in self._servers:
            state = self._servers[config.name]
            if state.process and state.process.poll() is None:
                return True  # Already running

        exe = config.get_executable()
        if not exe:
            # Try to install
            installed = await config.install()
            if not installed:
                return False
            exe = config.get_executable()
            if not exe:
                return False

        # Start the server process
        cmd = [exe] + config.args
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception:
            return False

        state = LSPServerState(
            config=config,
            process=process,
            root_uri=root_path.as_uri(),
        )
        self._servers[config.name] = state

        # Map languages to this server
        for lang_id in config.language_ids:
            self._language_to_server[lang_id] = config.name

        # Initialize the server
        try:
            await self._initialize_server(state)
            return True
        except Exception:
            await self.stop_server(config.name)
            return False

    async def stop_server(self, name: str) -> None:
        """Stop a language server."""
        state = self._servers.get(name)
        if not state:
            return

        # Send shutdown request
        if state.initialized:
            try:
                await self._send_request(state, "shutdown", None)
                await self._send_notification(state, "exit", None)
            except Exception:
                pass

        # Kill the process
        if state.process:
            state.process.terminate()
            try:
                state.process.wait(timeout=5)
            except Exception:
                state.process.kill()

        # Remove from maps
        del self._servers[name]
        for lang_id in state.config.language_ids:
            if self._language_to_server.get(lang_id) == name:
                del self._language_to_server[lang_id]

    async def stop_all(self) -> None:
        """Stop all language servers."""
        for name in list(self._servers.keys()):
            await self.stop_server(name)

    def get_server_for_file(self, file_path: str | Path) -> LSPServerState | None:
        """Get the server for a file based on its language."""
        lang_id = get_language_id(file_path)
        if not lang_id:
            return None

        server_name = self._language_to_server.get(lang_id)
        if not server_name:
            return None

        return self._servers.get(server_name)

    async def ensure_server_for_file(
        self,
        file_path: str | Path,
        root_path: Path,
    ) -> LSPServerState | None:
        """Ensure a server is running for the file."""
        lang_id = get_language_id(file_path)
        if not lang_id:
            return None

        # Check if we have a running server
        state = self.get_server_for_file(file_path)
        if state and state.initialized:
            return state

        # Get server configuration
        config = get_server_for_language(lang_id)
        if not config:
            return None

        # Start the server
        if await self.start_server(config, root_path):
            return self._servers.get(config.name)

        return None

    async def open_document(
        self,
        file_path: str | Path,
        content: str | None = None,
    ) -> bool:
        """
        Open a document in the language server.

        Args:
            file_path: Path to the file
            content: Content of the file (reads from disk if not provided)

        Returns:
            True if successful
        """
        path = Path(file_path)
        state = self.get_server_for_file(path)
        if not state or not state.initialized:
            return False

        uri = path.as_uri()
        if uri in state.open_documents:
            return True

        if content is None:
            try:
                content = path.read_text()
            except Exception:
                return False

        lang_id = get_language_id(path) or "plaintext"

        await self._send_notification(
            state,
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": lang_id,
                    "version": 1,
                    "text": content,
                }
            },
        )

        state.open_documents.add(uri)
        return True

    async def close_document(self, file_path: str | Path) -> None:
        """Close a document in the language server."""
        path = Path(file_path)
        state = self.get_server_for_file(path)
        if not state or not state.initialized:
            return

        uri = path.as_uri()
        if uri not in state.open_documents:
            return

        await self._send_notification(
            state,
            "textDocument/didClose",
            {"textDocument": {"uri": uri}},
        )

        state.open_documents.discard(uri)

    async def _initialize_server(self, state: LSPServerState) -> None:
        """Initialize a language server."""
        result = await self._send_request(
            state,
            "initialize",
            {
                "processId": None,
                "rootUri": state.root_uri,
                "capabilities": {
                    "textDocument": {
                        "hover": {"contentFormat": ["markdown", "plaintext"]},
                        "completion": {
                            "completionItem": {"snippetSupport": True},
                        },
                        "definition": {"linkSupport": True},
                        "references": {},
                        "documentSymbol": {
                            "hierarchicalDocumentSymbolSupport": True,
                        },
                        "codeAction": {},
                        "formatting": {},
                    },
                    "workspace": {
                        "workspaceFolders": True,
                        "symbol": {},
                    },
                },
                "initializationOptions": state.config.initialization_options,
                "workspaceFolders": [
                    {"uri": state.root_uri, "name": Path(state.root_uri[7:]).name}
                ],
            },
        )

        # Send initialized notification
        await self._send_notification(state, "initialized", {})
        state.initialized = True

    async def _send_request(
        self,
        state: LSPServerState,
        method: str,
        params: dict[str, Any] | None,
    ) -> Any:
        """Send a request and wait for response."""
        if not state.process or not state.process.stdin or not state.process.stdout:
            raise RuntimeError("Server not running")

        async with self._lock:
            state.request_id += 1
            request_id = state.request_id

            message = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params or {},
            }

            content = json.dumps(message)
            header = f"Content-Length: {len(content)}\r\n\r\n"
            data = (header + content).encode("utf-8")

            state.process.stdin.write(data)
            state.process.stdin.flush()

            # Read response
            return await self._read_response(state, request_id)

    async def _read_response(self, state: LSPServerState, request_id: int) -> Any:
        """Read a response from the server."""
        if not state.process or not state.process.stdout:
            raise RuntimeError("Server not running")

        loop = asyncio.get_event_loop()

        while True:
            # Read header
            header_data = await loop.run_in_executor(
                None,
                lambda: state.process.stdout.readline(),  # type: ignore
            )

            if not header_data:
                raise RuntimeError("Server closed connection")

            header = header_data.decode("utf-8").strip()

            # Parse content length
            if header.startswith("Content-Length:"):
                content_length = int(header.split(":")[1].strip())

                # Read empty line
                await loop.run_in_executor(
                    None,
                    lambda: state.process.stdout.readline(),  # type: ignore
                )

                # Read content
                content_data = await loop.run_in_executor(
                    None,
                    lambda: state.process.stdout.read(content_length),  # type: ignore
                )

                message = json.loads(content_data.decode("utf-8"))

                # Check if this is our response
                if message.get("id") == request_id:
                    if "error" in message:
                        raise RuntimeError(message["error"].get("message", "Unknown error"))
                    return message.get("result")

                # Otherwise it's a notification, continue reading

    async def _send_notification(
        self,
        state: LSPServerState,
        method: str,
        params: dict[str, Any] | None,
    ) -> None:
        """Send a notification (no response expected)."""
        if not state.process or not state.process.stdin:
            raise RuntimeError("Server not running")

        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
        }

        content = json.dumps(message)
        header = f"Content-Length: {len(content)}\r\n\r\n"
        data = (header + content).encode("utf-8")

        state.process.stdin.write(data)
        state.process.stdin.flush()

    async def send_request(
        self,
        file_path: str | Path,
        method: str,
        params: dict[str, Any],
    ) -> Any:
        """
        Send an LSP request for a file.

        Args:
            file_path: Path to the file
            method: LSP method name
            params: Request parameters

        Returns:
            Response result
        """
        state = self.get_server_for_file(file_path)
        if not state or not state.initialized:
            raise RuntimeError(f"No server available for {file_path}")

        return await self._send_request(state, method, params)


# Global client instance
_client: LSPClient | None = None


def get_lsp_client() -> LSPClient:
    """Get the global LSP client."""
    global _client
    if _client is None:
        _client = LSPClient()
    return _client
