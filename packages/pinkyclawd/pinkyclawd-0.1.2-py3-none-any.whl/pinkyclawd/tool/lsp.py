"""
LSP tool for code intelligence operations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pinkyclawd.tool.base import (
    INTEGER_PARAM,
    STRING_PARAM,
    Tool,
    ToolContext,
    ToolResult,
    make_schema,
)


class LSPTool(Tool):
    """Language Server Protocol operations for code intelligence."""

    @property
    def name(self) -> str:
        return "lsp"

    @property
    def description(self) -> str:
        return """Interact with Language Server Protocol (LSP) for code intelligence.

Supported operations:
- goToDefinition: Find where a symbol is defined
- findReferences: Find all references to a symbol
- hover: Get documentation/type info for a symbol
- documentSymbol: Get all symbols in a file
- workspaceSymbol: Search for symbols across the workspace
- goToImplementation: Find implementations of interface/abstract
- prepareCallHierarchy: Get call hierarchy at position
- incomingCalls: Find callers of a function
- outgoingCalls: Find functions called by a function

Line and character positions are 1-indexed (as shown in editors)."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                (
                    "operation",
                    "LSP operation to perform",
                    {
                        "type": "string",
                        "enum": [
                            "goToDefinition",
                            "findReferences",
                            "hover",
                            "documentSymbol",
                            "workspaceSymbol",
                            "goToImplementation",
                            "prepareCallHierarchy",
                            "incomingCalls",
                            "outgoingCalls",
                        ],
                    },
                ),
                ("filePath", "Path to the file", STRING_PARAM),
                ("line", "Line number (1-indexed)", INTEGER_PARAM),
                ("character", "Character offset (1-indexed)", INTEGER_PARAM),
            ],
            optional=[
                (
                    "query",
                    "Search query (for workspaceSymbol operation)",
                    STRING_PARAM,
                ),
            ],
        )

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Execute an LSP operation."""
        operation = kwargs.get("operation", "")
        file_path = kwargs.get("filePath", "")
        line = kwargs.get("line", 1)
        character = kwargs.get("character", 1)
        query = kwargs.get("query", "")

        if not operation:
            return ToolResult.fail("No operation specified")

        if not file_path:
            return ToolResult.fail("No file path specified")

        # Resolve path
        path = Path(file_path)
        if not path.is_absolute():
            path = ctx.working_directory / path

        if not path.exists():
            return ToolResult.fail(f"File not found: {path}")

        try:
            # Import here to avoid circular imports and allow lazy loading
            from pinkyclawd.lsp import (
                document_symbol,
                find_references,
                get_call_hierarchy,
                get_incoming_calls,
                get_lsp_client,
                get_outgoing_calls,
                go_to_definition,
                go_to_implementation,
                hover,
                workspace_symbol,
            )

            # Ensure server is running
            client = get_lsp_client()
            state = await client.ensure_server_for_file(path, ctx.working_directory)
            if not state:
                return ToolResult.fail(
                    f"No language server available for {path.suffix} files. "
                    "The server may need to be installed."
                )

            if operation == "goToDefinition":
                locations = await go_to_definition(path, line, character)
                return self._format_locations(locations, "definitions")

            elif operation == "findReferences":
                locations = await find_references(path, line, character)
                return self._format_locations(locations, "references")

            elif operation == "hover":
                result = await hover(path, line, character)
                if not result:
                    return ToolResult.ok("No hover information available")
                return ToolResult.ok(
                    result.contents,
                    has_range=result.range is not None,
                )

            elif operation == "documentSymbol":
                symbols = await document_symbol(path)
                return self._format_symbols(symbols)

            elif operation == "workspaceSymbol":
                if not query:
                    return ToolResult.fail("Query required for workspaceSymbol")
                symbols = await workspace_symbol(query, path)
                return self._format_workspace_symbols(symbols)

            elif operation == "goToImplementation":
                locations = await go_to_implementation(path, line, character)
                return self._format_locations(locations, "implementations")

            elif operation == "prepareCallHierarchy":
                items = await get_call_hierarchy(path, line, character)
                if not items:
                    return ToolResult.ok("No call hierarchy items found")
                lines = []
                for item in items:
                    lines.append(f"{item.name} ({item.detail or 'no detail'})")
                    lines.append(f"  {item.uri}:{item.range.start.line + 1}")
                return ToolResult.ok("\n".join(lines), count=len(items))

            elif operation == "incomingCalls":
                calls = await get_incoming_calls(path, line, character)
                if not calls:
                    return ToolResult.ok("No incoming calls found")
                lines = []
                for call in calls:
                    item = call.item
                    lines.append(f"Called by: {item.name}")
                    lines.append(f"  {item.uri}:{item.range.start.line + 1}")
                return ToolResult.ok("\n".join(lines), count=len(calls))

            elif operation == "outgoingCalls":
                calls = await get_outgoing_calls(path, line, character)
                if not calls:
                    return ToolResult.ok("No outgoing calls found")
                lines = []
                for call in calls:
                    item = call.item
                    lines.append(f"Calls: {item.name}")
                    lines.append(f"  {item.uri}:{item.range.start.line + 1}")
                return ToolResult.ok("\n".join(lines), count=len(calls))

            else:
                return ToolResult.fail(f"Unknown operation: {operation}")

        except Exception as e:
            return ToolResult.fail(f"LSP operation failed: {e}")

    def _format_locations(
        self,
        locations: list,
        label: str,
    ) -> ToolResult:
        """Format location results."""
        if not locations:
            return ToolResult.ok(f"No {label} found")

        lines = [f"Found {len(locations)} {label}:"]
        for loc in locations:
            path = loc.file_path
            line = loc.range.start.line + 1
            char = loc.range.start.character + 1
            lines.append(f"  {path}:{line}:{char}")

        return ToolResult.ok("\n".join(lines), count=len(locations))

    def _format_symbols(self, symbols: list) -> ToolResult:
        """Format document symbols."""
        if not symbols:
            return ToolResult.ok("No symbols found")

        from pinkyclawd.lsp.operations import get_symbol_kind_name

        lines = [f"Found {len(symbols)} symbols:"]

        def format_symbol(sym, indent: int = 0) -> None:
            prefix = "  " * indent
            kind = get_symbol_kind_name(sym.kind)
            detail = f" - {sym.detail}" if sym.detail else ""
            line = sym.range.start.line + 1
            lines.append(f"{prefix}{kind}: {sym.name}{detail} (line {line})")

            if sym.children:
                for child in sym.children:
                    format_symbol(child, indent + 1)

        for sym in symbols:
            format_symbol(sym)

        return ToolResult.ok("\n".join(lines), count=len(symbols))

    def _format_workspace_symbols(self, symbols: list) -> ToolResult:
        """Format workspace symbols."""
        if not symbols:
            return ToolResult.ok("No symbols found")

        from pinkyclawd.lsp.operations import get_symbol_kind_name

        lines = [f"Found {len(symbols)} symbols:"]
        for sym in symbols:
            kind = get_symbol_kind_name(sym.kind)
            container = f" in {sym.container_name}" if sym.container_name else ""
            path = sym.location.file_path
            line = sym.location.range.start.line + 1
            lines.append(f"  {kind}: {sym.name}{container}")
            lines.append(f"    {path}:{line}")

        return ToolResult.ok("\n".join(lines), count=len(symbols))
