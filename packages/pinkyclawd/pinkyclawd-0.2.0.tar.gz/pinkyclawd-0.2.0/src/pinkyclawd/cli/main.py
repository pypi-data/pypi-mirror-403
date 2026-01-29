"""
Main CLI entry point for PinkyClawd.

Provides the command-line interface for the PinkyClawd development tool.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Sequence


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="pinkyclawd",
        description="PinkyClawd - AI-powered development tool",
    )

    parser.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="Show version number",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Default TUI command (no subcommand)
    parser.add_argument(
        "project",
        nargs="?",
        help="Project directory to open",
    )

    parser.add_argument(
        "--continue",
        "-c",
        dest="continue_session",
        action="store_true",
        help="Continue the last session",
    )

    parser.add_argument(
        "--session",
        "-s",
        dest="session_id",
        help="Continue a specific session",
    )

    parser.add_argument(
        "--model",
        "-m",
        help="Model to use (provider/model)",
    )

    parser.add_argument(
        "--agent",
        default="build",
        help="Agent to use (default: build)",
    )

    parser.add_argument(
        "--prompt",
        "-p",
        help="Initial prompt to send",
    )

    parser.add_argument(
        "--port",
        type=int,
        help="Server port (for server mode)",
    )

    # Run command (non-interactive)
    run_parser = subparsers.add_parser(
        "run",
        help="Run with a message (non-interactive)",
    )
    run_parser.add_argument(
        "message",
        nargs="*",
        help="Message to send",
    )
    run_parser.add_argument(
        "--model",
        "-m",
        help="Model to use",
    )
    run_parser.add_argument(
        "--agent",
        default="build",
        help="Agent to use",
    )
    run_parser.add_argument(
        "--format",
        choices=["default", "json"],
        default="default",
        help="Output format",
    )
    run_parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming output",
    )
    run_parser.add_argument(
        "--output",
        "-o",
        help="Output file path",
    )
    run_parser.add_argument(
        "--max-turns",
        type=int,
        default=50,
        help="Maximum agent turns (default: 50)",
    )
    run_parser.add_argument(
        "--dir",
        "-d",
        help="Working directory",
    )

    # Serve command
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start the server in background mode",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=4096,
        help="Server port",
    )

    # Models command
    subparsers.add_parser(
        "models",
        help="List available models",
    )

    # Sessions command
    sessions_parser = subparsers.add_parser(
        "session",
        help="Session management",
    )
    sessions_parser.add_argument(
        "action",
        choices=["list", "delete", "export", "import"],
        nargs="?",
        default="list",
        help="Session action",
    )
    sessions_parser.add_argument(
        "session_id",
        nargs="?",
        help="Session ID (for delete/export)",
    )
    sessions_parser.add_argument(
        "--output",
        "-o",
        help="Output file path (for export)",
    )
    sessions_parser.add_argument(
        "--file",
        "-f",
        help="Input file path (for import)",
    )

    # Auth command
    auth_parser = subparsers.add_parser(
        "auth",
        help="Manage provider authentication",
    )
    auth_parser.add_argument(
        "provider",
        nargs="?",
        help="Provider to authenticate",
    )

    # MCP command
    mcp_parser = subparsers.add_parser(
        "mcp",
        help="MCP server management",
    )
    mcp_parser.add_argument(
        "action",
        choices=["list", "add", "remove", "auth", "logout", "debug"],
        nargs="?",
        default="list",
        help="MCP action",
    )
    mcp_parser.add_argument(
        "name",
        nargs="?",
        help="Server name",
    )
    mcp_parser.add_argument(
        "--type",
        choices=["stdio", "http"],
        default="stdio",
        help="Server type (for add)",
    )
    mcp_parser.add_argument(
        "--command",
        help="Command to run (for stdio servers)",
    )
    mcp_parser.add_argument(
        "--url",
        help="Server URL (for HTTP servers)",
    )

    # Upgrade command
    subparsers.add_parser(
        "upgrade",
        help="Upgrade to latest version",
    )

    return parser


def main(args: Sequence[str] | None = None) -> int:
    """Main entry point."""
    parser = create_parser()
    parsed = parser.parse_args(args)

    if parsed.version:
        from pinkyclawd import __version__

        print(f"pinkyclawd {__version__}")
        return 0

    if parsed.command == "run":
        return run_command(parsed)
    elif parsed.command == "serve":
        return serve_command(parsed)
    elif parsed.command == "models":
        return models_command(parsed)
    elif parsed.command == "session":
        return session_command(parsed)
    elif parsed.command == "auth":
        return auth_command(parsed)
    elif parsed.command == "upgrade":
        return upgrade_command(parsed)
    elif parsed.command == "mcp":
        return mcp_command(parsed)
    else:
        # Default: launch TUI
        return tui_command(parsed)


def tui_command(args: argparse.Namespace) -> int:
    """Launch the TUI."""
    from pinkyclawd.tui import run_app

    project = Path(args.project) if args.project else Path.cwd()

    run_app(
        working_directory=project,
        session_id=args.session_id,
        model=args.model,
        agent=args.agent,
    )

    return 0


def run_command(args: argparse.Namespace) -> int:
    """Run a non-interactive session with full tool execution."""
    message = " ".join(args.message) if args.message else None

    if not message:
        print("Error: No message provided", file=sys.stderr)
        return 1

    from pinkyclawd.cli.conversation import run_single_prompt

    try:
        result = asyncio.run(
            run_single_prompt(
                prompt=message,
                model=args.model,
                output_format=args.format,
                max_turns=args.max_turns,
                no_stream=args.no_stream,
                output_file=args.output,
                working_directory=args.dir,
            )
        )

        return 0 if result.get("success", False) else 1

    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def serve_command(args: argparse.Namespace) -> int:
    """Start the server."""
    from pinkyclawd.server import run_server

    print(f"Starting PinkyClawd server on port {args.port}...")
    print(f"API: http://localhost:{args.port}")
    print(f"Health: http://localhost:{args.port}/health")

    try:
        run_server(
            host="127.0.0.1",
            port=args.port,
            working_directory=Path.cwd(),
        )
        return 0
    except KeyboardInterrupt:
        print("\nServer stopped")
        return 0
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        return 1


def models_command(args: argparse.Namespace) -> int:
    """List available models."""
    print("Available models:")
    print()
    print("Anthropic:")
    print("  - anthropic/claude-sonnet-4-20250514 (Claude Sonnet 4)")
    print("  - anthropic/claude-opus-4-20250514 (Claude Opus 4)")
    print("  - anthropic/claude-3-5-sonnet-20241022 (Claude 3.5 Sonnet)")
    print()
    print("OpenAI:")
    print("  - openai/gpt-4o (GPT-4o)")
    print("  - openai/gpt-4o-mini (GPT-4o Mini)")
    print("  - openai/o1 (o1)")
    print()
    return 0


def session_command(args: argparse.Namespace) -> int:
    """Session management."""
    from pinkyclawd.config.storage import get_storage
    from pinkyclawd.session.export import export_session, import_session

    action = args.action
    storage = get_storage()

    if action == "list":
        sessions = storage.list_sessions(limit=20)

        if not sessions:
            print("No sessions found.")
            return 0

        print("Recent sessions:")
        print()
        for s in sessions:
            messages = storage.get_messages(s.id)
            created = s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "Unknown"
            print(f"  {s.id}")
            print(f"    Title: {s.title}")
            print(f"    Messages: {len(messages)}")
            print(f"    Created: {created}")
            print(f"    Directory: {s.directory}")
            print()

    elif action == "delete":
        session_id = getattr(args, "session_id", None)
        if not session_id:
            print("Error: Session ID required for delete", file=sys.stderr)
            print("Usage: pinkyclawd session delete <session_id>")
            return 1

        session = storage.get_session(session_id)
        if not session:
            print(f"Session not found: {session_id}", file=sys.stderr)
            return 1

        storage.delete_session(session_id)
        print(f"Deleted session: {session_id}")

    elif action == "export":
        session_id = getattr(args, "session_id", None)
        output_path = getattr(args, "output", None)

        if not session_id:
            print("Error: Session ID required for export", file=sys.stderr)
            print("Usage: pinkyclawd session export <session_id> [--output file]")
            return 1

        if not output_path:
            output_path = f"{session_id}.json"

        result = export_session(session_id, output_path)
        if result.success:
            print(f"Exported to: {result.path}")
        else:
            print(f"Export failed: {result.error}", file=sys.stderr)
            return 1

    elif action == "import":
        input_path = getattr(args, "file", None)

        if not input_path:
            print("Error: File path required for import", file=sys.stderr)
            print("Usage: pinkyclawd session import <file>")
            return 1

        result = import_session(input_path)
        if result.success:
            print(f"Imported session: {result.session_id}")
            print(f"Messages imported: {result.message_count}")
        else:
            print(f"Import failed: {result.error}", file=sys.stderr)
            return 1

    return 0


def auth_command(args: argparse.Namespace) -> int:
    """Manage authentication."""
    provider = args.provider

    if provider:
        print(f"Authenticating with {provider}...")
        print("(Auth not fully implemented yet)")
    else:
        print("Providers:")
        print("  - anthropic (ANTHROPIC_API_KEY)")
        print("  - openai (OPENAI_API_KEY)")
        print()
        print("Set API keys as environment variables.")

    return 0


def mcp_command(args: argparse.Namespace) -> int:
    """MCP server management."""
    action = args.action

    if action == "list":
        return asyncio.run(_mcp_list())
    elif action == "add":
        name = args.name
        if not name:
            print("Error: Server name required", file=sys.stderr)
            return 1
        return asyncio.run(_mcp_add(name, args.type, args.command, args.url))
    elif action == "remove":
        name = args.name
        if not name:
            print("Error: Server name required", file=sys.stderr)
            return 1
        return asyncio.run(_mcp_remove(name))
    elif action == "auth":
        name = args.name
        if not name:
            print("Error: Server name required", file=sys.stderr)
            return 1
        return asyncio.run(_mcp_auth(name))
    elif action == "logout":
        name = args.name
        if not name:
            print("Error: Server name required", file=sys.stderr)
            return 1
        return _mcp_logout(name)
    elif action == "debug":
        name = args.name
        if not name:
            print("Error: Server name required", file=sys.stderr)
            return 1
        return asyncio.run(_mcp_debug(name))

    return 0


async def _mcp_list() -> int:
    """List configured MCP servers."""
    from pinkyclawd.mcp import get_mcp_client

    client = get_mcp_client()
    servers = client.list_servers()

    if not servers:
        print("No MCP servers configured.")
        print()
        print("Add a server with: pinkyclawd mcp add <name> --type stdio --command <cmd>")
        return 0

    print("Configured MCP servers:")
    print()
    for name in servers:
        server = client.get_server(name)
        if server:
            status = "connected" if server.transport.is_connected else "disconnected"
            tools = [t.name for t in server.tools]
            print(f"  {name}")
            print(f"    Status: {status}")
            print(f"    Tools: {', '.join(tools) if tools else 'None'}")
            print()

    return 0


async def _mcp_add(name: str, server_type: str, command: str | None, url: str | None) -> int:
    """Add an MCP server."""
    from pinkyclawd.mcp import get_mcp_client

    client = get_mcp_client()

    if server_type == "stdio":
        if not command:
            print("Error: --command required for stdio servers", file=sys.stderr)
            return 1
        cmd_list = command.split()
        success = await client.add_stdio_server(name, cmd_list)
    else:
        if not url:
            print("Error: --url required for HTTP servers", file=sys.stderr)
            return 1
        success = await client.add_http_server(name, url)

    if success:
        server = client.get_server(name)
        if server:
            print(f"Added server: {name}")
            print(f"Tools available: {len(server.tools)}")
            for tool in server.tools:
                print(f"  - {tool.name}: {tool.description[:50]}...")
        return 0
    else:
        print(f"Failed to add server: {name}", file=sys.stderr)
        return 1


async def _mcp_remove(name: str) -> int:
    """Remove an MCP server."""
    from pinkyclawd.mcp import get_mcp_client

    client = get_mcp_client()

    if name not in client.list_servers():
        print(f"Server not found: {name}", file=sys.stderr)
        return 1

    await client.remove_server(name)
    print(f"Removed server: {name}")
    return 0


async def _mcp_auth(name: str) -> int:
    """Start OAuth flow for an MCP server."""
    from pinkyclawd.mcp import OAuth2Config, start_oauth_flow

    # For now, just show instructions
    print(f"OAuth authentication for {name}")
    print()
    print("To configure OAuth, you need to provide:")
    print("  - Client ID")
    print("  - Authorization URL")
    print("  - Token URL")
    print()
    print("Use the server API to configure OAuth settings.")
    return 0


def _mcp_logout(name: str) -> int:
    """Remove credentials for an MCP server."""
    from pinkyclawd.mcp import get_token_store

    store = get_token_store()

    if store.delete(name):
        print(f"Logged out from: {name}")
        return 0
    else:
        print(f"No credentials found for: {name}", file=sys.stderr)
        return 1


async def _mcp_debug(name: str) -> int:
    """Debug MCP server connection."""
    from pinkyclawd.mcp import get_mcp_client

    client = get_mcp_client()

    server = client.get_server(name)
    if not server:
        print(f"Server not found: {name}", file=sys.stderr)
        return 1

    print(f"Server: {name}")
    print(f"Connected: {server.transport.is_connected}")
    print(f"Initialized: {server.initialized}")
    print()
    print("Capabilities:")
    for key, value in server.capabilities.items():
        print(f"  {key}: {value}")
    print()
    print("Tools:")
    for tool in server.tools:
        print(f"  {tool.name}")
        print(f"    {tool.description}")
        print()

    return 0


def upgrade_command(args: argparse.Namespace) -> int:
    """Upgrade to latest version."""
    print("Checking for updates...")
    print("pip install --upgrade pinkyclawd")
    return 0


def cli() -> None:
    """CLI entry point for setuptools."""
    sys.exit(main())


if __name__ == "__main__":
    cli()
