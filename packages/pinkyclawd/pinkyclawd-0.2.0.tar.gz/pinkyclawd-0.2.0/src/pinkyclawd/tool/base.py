"""
Base tool interface and common types.

Provides the abstract interface for all tools plus permission system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal
import fnmatch


class ToolPermission(str, Enum):
    """Permission levels for tools."""

    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


@dataclass
class PermissionRule:
    """A permission rule with optional pattern matching."""

    pattern: str = "*"
    permission: ToolPermission = ToolPermission.ASK

    def matches(self, value: str) -> bool:
        """Check if a value matches this rule's pattern."""
        return fnmatch.fnmatch(value, self.pattern)


@dataclass
class ToolContext:
    """Context provided to tools during execution."""

    session_id: str
    message_id: str
    working_directory: Path
    user_confirmed: bool = False

    # Callbacks
    on_output: Any = None  # Callable[[str], None]
    on_permission_request: Any = None  # Callable[[str, str], Awaitable[bool]]

    def __post_init__(self) -> None:
        if isinstance(self.working_directory, str):
            self.working_directory = Path(self.working_directory)


@dataclass
class ToolResult:
    """Result of a tool execution."""

    success: bool
    output: str
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # For truncation
    truncated: bool = False
    full_output_path: str | None = None

    @classmethod
    def ok(cls, output: str, **metadata: Any) -> ToolResult:
        """Create a successful result."""
        return cls(success=True, output=output, metadata=metadata)

    @classmethod
    def fail(cls, error: str, output: str = "") -> ToolResult:
        """Create a failed result."""
        return cls(success=False, output=output, error=error)


class Tool(ABC):
    """
    Abstract base class for tools.

    Each tool provides a specific capability (file reading, shell execution, etc.)
    that the AI can invoke during a conversation.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool identifier used in function calls."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description for the AI."""
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """JSON Schema for tool parameters."""
        ...

    @property
    def permission_category(self) -> str:
        """Category for permission checking (defaults to tool name)."""
        return self.name

    @property
    def requires_confirmation(self) -> bool:
        """Whether this tool requires user confirmation by default."""
        return False

    @abstractmethod
    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with given arguments.

        Args:
            ctx: Execution context
            **kwargs: Tool-specific arguments

        Returns:
            Tool result
        """
        ...

    def to_schema(self) -> dict[str, Any]:
        """Convert to OpenAI/Anthropic function schema."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    async def check_permission(
        self,
        ctx: ToolContext,
        rules: dict[str, PermissionRule],
        check_value: str = "",
    ) -> bool:
        """
        Check if tool execution is permitted.

        Args:
            ctx: Execution context
            rules: Permission rules for this tool category
            check_value: Value to check against patterns (e.g., file path)

        Returns:
            True if permitted
        """
        if ctx.user_confirmed:
            return True

        # Find matching rule
        for pattern, rule in rules.items():
            if rule.matches(check_value or "*"):
                if rule.permission == ToolPermission.ALLOW:
                    return True
                if rule.permission == ToolPermission.DENY:
                    return False
                # ASK - need confirmation
                if ctx.on_permission_request:
                    return await ctx.on_permission_request(
                        self.name,
                        f"Allow {self.name} on {check_value}?",
                    )
                return False

        # Default: ask
        if ctx.on_permission_request:
            return await ctx.on_permission_request(
                self.name,
                f"Allow {self.name}?",
            )
        return False


# Common parameter schemas
STRING_PARAM = {"type": "string"}
INTEGER_PARAM = {"type": "integer"}
BOOLEAN_PARAM = {"type": "boolean"}
ARRAY_PARAM = lambda item_type: {"type": "array", "items": item_type}


def make_schema(
    required: list[tuple[str, str, dict]],
    optional: list[tuple[str, str, dict]] | None = None,
) -> dict[str, Any]:
    """
    Helper to create a JSON Schema for tool parameters.

    Args:
        required: List of (name, description, type_schema) for required params
        optional: List of (name, description, type_schema) for optional params

    Returns:
        JSON Schema dict
    """
    properties = {}
    required_names = []

    for name, desc, schema in required:
        properties[name] = {**schema, "description": desc}
        required_names.append(name)

    for name, desc, schema in optional or []:
        properties[name] = {**schema, "description": desc}

    return {
        "type": "object",
        "properties": properties,
        "required": required_names,
        "additionalProperties": False,
    }
