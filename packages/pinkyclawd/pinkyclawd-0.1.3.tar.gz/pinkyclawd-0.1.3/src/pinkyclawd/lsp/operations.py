"""
LSP operations for code intelligence.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pinkyclawd.lsp.client import Location, Range, get_lsp_client


@dataclass
class HoverResult:
    """Result of a hover request."""

    contents: str
    range: Range | None = None


@dataclass
class DocumentSymbol:
    """A symbol in a document."""

    name: str
    kind: int
    range: Range
    selection_range: Range
    children: list[DocumentSymbol] | None = None
    detail: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DocumentSymbol:
        children = None
        if "children" in d:
            children = [DocumentSymbol.from_dict(c) for c in d["children"]]
        return cls(
            name=d["name"],
            kind=d["kind"],
            range=Range.from_dict(d["range"]),
            selection_range=Range.from_dict(d["selectionRange"]),
            children=children,
            detail=d.get("detail"),
        )


@dataclass
class SymbolInformation:
    """Symbol information from workspace search."""

    name: str
    kind: int
    location: Location
    container_name: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SymbolInformation:
        return cls(
            name=d["name"],
            kind=d["kind"],
            location=Location.from_dict(d["location"]),
            container_name=d.get("containerName"),
        )


@dataclass
class CallHierarchyItem:
    """An item in the call hierarchy."""

    name: str
    kind: int
    uri: str
    range: Range
    selection_range: Range
    detail: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CallHierarchyItem:
        return cls(
            name=d["name"],
            kind=d["kind"],
            uri=d["uri"],
            range=Range.from_dict(d["range"]),
            selection_range=Range.from_dict(d["selectionRange"]),
            detail=d.get("detail"),
        )


@dataclass
class CallHierarchyCall:
    """A call in the call hierarchy."""

    item: CallHierarchyItem
    from_ranges: list[Range]

    @classmethod
    def from_dict(cls, d: dict[str, Any], key: str) -> CallHierarchyCall:
        return cls(
            item=CallHierarchyItem.from_dict(d[key]),
            from_ranges=[Range.from_dict(r) for r in d["fromRanges"]],
        )


# Symbol kind mapping
SYMBOL_KINDS = {
    1: "File",
    2: "Module",
    3: "Namespace",
    4: "Package",
    5: "Class",
    6: "Method",
    7: "Property",
    8: "Field",
    9: "Constructor",
    10: "Enum",
    11: "Interface",
    12: "Function",
    13: "Variable",
    14: "Constant",
    15: "String",
    16: "Number",
    17: "Boolean",
    18: "Array",
    19: "Object",
    20: "Key",
    21: "Null",
    22: "EnumMember",
    23: "Struct",
    24: "Event",
    25: "Operator",
    26: "TypeParameter",
}


def get_symbol_kind_name(kind: int) -> str:
    """Get the human-readable name for a symbol kind."""
    return SYMBOL_KINDS.get(kind, f"Unknown({kind})")


async def go_to_definition(
    file_path: str | Path,
    line: int,
    character: int,
) -> list[Location]:
    """
    Go to the definition of the symbol at position.

    Args:
        file_path: Path to the file
        line: Line number (1-indexed, converts to 0-indexed for LSP)
        character: Character offset (1-indexed, converts to 0-indexed)

    Returns:
        List of definition locations
    """
    client = get_lsp_client()
    path = Path(file_path)
    uri = path.as_uri()

    await client.open_document(path)

    result = await client.send_request(
        path,
        "textDocument/definition",
        {
            "textDocument": {"uri": uri},
            "position": {"line": line - 1, "character": character - 1},
        },
    )

    if not result:
        return []

    # Result can be Location, Location[], or LocationLink[]
    if isinstance(result, dict):
        return [Location.from_dict(result)]
    elif isinstance(result, list):
        locations = []
        for item in result:
            if "targetUri" in item:
                # LocationLink
                locations.append(
                    Location(
                        uri=item["targetUri"],
                        range=Range.from_dict(item["targetRange"]),
                    )
                )
            else:
                # Location
                locations.append(Location.from_dict(item))
        return locations

    return []


async def find_references(
    file_path: str | Path,
    line: int,
    character: int,
    include_declaration: bool = True,
) -> list[Location]:
    """
    Find all references to the symbol at position.

    Args:
        file_path: Path to the file
        line: Line number (1-indexed)
        character: Character offset (1-indexed)
        include_declaration: Include the declaration itself

    Returns:
        List of reference locations
    """
    client = get_lsp_client()
    path = Path(file_path)
    uri = path.as_uri()

    await client.open_document(path)

    result = await client.send_request(
        path,
        "textDocument/references",
        {
            "textDocument": {"uri": uri},
            "position": {"line": line - 1, "character": character - 1},
            "context": {"includeDeclaration": include_declaration},
        },
    )

    if not result:
        return []

    return [Location.from_dict(loc) for loc in result]


async def hover(
    file_path: str | Path,
    line: int,
    character: int,
) -> HoverResult | None:
    """
    Get hover information at position.

    Args:
        file_path: Path to the file
        line: Line number (1-indexed)
        character: Character offset (1-indexed)

    Returns:
        Hover result or None
    """
    client = get_lsp_client()
    path = Path(file_path)
    uri = path.as_uri()

    await client.open_document(path)

    result = await client.send_request(
        path,
        "textDocument/hover",
        {
            "textDocument": {"uri": uri},
            "position": {"line": line - 1, "character": character - 1},
        },
    )

    if not result:
        return None

    # Parse contents
    contents = result.get("contents", "")
    if isinstance(contents, dict):
        # MarkedString or MarkupContent
        if "value" in contents:
            contents = contents["value"]
        elif "language" in contents:
            contents = f"```{contents['language']}\n{contents.get('value', '')}\n```"
    elif isinstance(contents, list):
        # Array of MarkedString
        parts = []
        for item in contents:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if "value" in item:
                    parts.append(item["value"])
        contents = "\n\n".join(parts)

    hover_range = None
    if "range" in result:
        hover_range = Range.from_dict(result["range"])

    return HoverResult(contents=contents, range=hover_range)


async def document_symbol(file_path: str | Path) -> list[DocumentSymbol]:
    """
    Get all symbols in a document.

    Args:
        file_path: Path to the file

    Returns:
        List of document symbols
    """
    client = get_lsp_client()
    path = Path(file_path)
    uri = path.as_uri()

    await client.open_document(path)

    result = await client.send_request(
        path,
        "textDocument/documentSymbol",
        {"textDocument": {"uri": uri}},
    )

    if not result:
        return []

    # Result can be DocumentSymbol[] or SymbolInformation[]
    symbols = []
    for item in result:
        if "selectionRange" in item:
            # DocumentSymbol
            symbols.append(DocumentSymbol.from_dict(item))
        else:
            # SymbolInformation - convert to DocumentSymbol
            loc = item.get("location", {})
            range_data = loc.get("range", {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 0}})
            symbols.append(
                DocumentSymbol(
                    name=item["name"],
                    kind=item["kind"],
                    range=Range.from_dict(range_data),
                    selection_range=Range.from_dict(range_data),
                    detail=item.get("containerName"),
                )
            )

    return symbols


async def workspace_symbol(query: str, file_path: str | Path) -> list[SymbolInformation]:
    """
    Search for symbols in the workspace.

    Args:
        query: Search query
        file_path: Any file in the workspace (for server lookup)

    Returns:
        List of matching symbols
    """
    client = get_lsp_client()

    result = await client.send_request(
        file_path,
        "workspace/symbol",
        {"query": query},
    )

    if not result:
        return []

    return [SymbolInformation.from_dict(item) for item in result]


async def go_to_implementation(
    file_path: str | Path,
    line: int,
    character: int,
) -> list[Location]:
    """
    Go to implementations of the symbol at position.

    Args:
        file_path: Path to the file
        line: Line number (1-indexed)
        character: Character offset (1-indexed)

    Returns:
        List of implementation locations
    """
    client = get_lsp_client()
    path = Path(file_path)
    uri = path.as_uri()

    await client.open_document(path)

    result = await client.send_request(
        path,
        "textDocument/implementation",
        {
            "textDocument": {"uri": uri},
            "position": {"line": line - 1, "character": character - 1},
        },
    )

    if not result:
        return []

    if isinstance(result, dict):
        return [Location.from_dict(result)]
    elif isinstance(result, list):
        return [Location.from_dict(loc) for loc in result]

    return []


async def get_call_hierarchy(
    file_path: str | Path,
    line: int,
    character: int,
) -> list[CallHierarchyItem]:
    """
    Get call hierarchy item at position.

    Args:
        file_path: Path to the file
        line: Line number (1-indexed)
        character: Character offset (1-indexed)

    Returns:
        List of call hierarchy items
    """
    client = get_lsp_client()
    path = Path(file_path)
    uri = path.as_uri()

    await client.open_document(path)

    result = await client.send_request(
        path,
        "textDocument/prepareCallHierarchy",
        {
            "textDocument": {"uri": uri},
            "position": {"line": line - 1, "character": character - 1},
        },
    )

    if not result:
        return []

    return [CallHierarchyItem.from_dict(item) for item in result]


async def get_incoming_calls(
    file_path: str | Path,
    line: int,
    character: int,
) -> list[CallHierarchyCall]:
    """
    Get incoming calls to the function at position.

    Args:
        file_path: Path to the file
        line: Line number (1-indexed)
        character: Character offset (1-indexed)

    Returns:
        List of incoming calls
    """
    items = await get_call_hierarchy(file_path, line, character)
    if not items:
        return []

    client = get_lsp_client()

    result = await client.send_request(
        file_path,
        "callHierarchy/incomingCalls",
        {"item": items[0].__dict__},
    )

    if not result:
        return []

    return [CallHierarchyCall.from_dict(call, "from") for call in result]


async def get_outgoing_calls(
    file_path: str | Path,
    line: int,
    character: int,
) -> list[CallHierarchyCall]:
    """
    Get outgoing calls from the function at position.

    Args:
        file_path: Path to the file
        line: Line number (1-indexed)
        character: Character offset (1-indexed)

    Returns:
        List of outgoing calls
    """
    items = await get_call_hierarchy(file_path, line, character)
    if not items:
        return []

    client = get_lsp_client()

    result = await client.send_request(
        file_path,
        "callHierarchy/outgoingCalls",
        {"item": items[0].__dict__},
    )

    if not result:
        return []

    return [CallHierarchyCall.from_dict(call, "to") for call in result]
