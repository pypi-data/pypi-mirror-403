"""
Base agent definition and types.

Agents define different personalities and capabilities for the AI assistant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class AgentMode(str, Enum):
    """Mode in which an agent can operate."""

    PRIMARY = "primary"  # Can be selected as main agent
    SUBAGENT = "subagent"  # Only used as a subagent (e.g., Task tool)
    ALL = "all"  # Can be both primary and subagent


@dataclass
class AgentPermissions:
    """Permission configuration for an agent."""

    # File operations
    read: Literal["allow", "ask", "deny"] = "allow"
    write: Literal["allow", "ask", "deny"] = "ask"
    edit: Literal["allow", "ask", "deny"] = "ask"

    # System operations
    bash: Literal["allow", "ask", "deny"] = "ask"
    glob: Literal["allow", "ask", "deny"] = "allow"
    grep: Literal["allow", "ask", "deny"] = "allow"

    # External operations
    webfetch: Literal["allow", "ask", "deny"] = "ask"
    task: Literal["allow", "ask", "deny"] = "allow"

    # Special
    external_directory: Literal["allow", "ask", "deny"] = "ask"

    def to_dict(self) -> dict[str, str]:
        return {
            "read": self.read,
            "write": self.write,
            "edit": self.edit,
            "bash": self.bash,
            "glob": self.glob,
            "grep": self.grep,
            "webfetch": self.webfetch,
            "task": self.task,
            "external_directory": self.external_directory,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> AgentPermissions:
        return cls(
            read=data.get("read", "allow"),
            write=data.get("write", "ask"),
            edit=data.get("edit", "ask"),
            bash=data.get("bash", "ask"),
            glob=data.get("glob", "allow"),
            grep=data.get("grep", "allow"),
            webfetch=data.get("webfetch", "ask"),
            task=data.get("task", "allow"),
            external_directory=data.get("external_directory", "ask"),
        )

    @classmethod
    def read_only(cls) -> AgentPermissions:
        """Create read-only permissions."""
        return cls(
            read="allow",
            write="deny",
            edit="deny",
            bash="deny",
            glob="allow",
            grep="allow",
            webfetch="deny",
            task="allow",
            external_directory="deny",
        )

    @classmethod
    def full_access(cls) -> AgentPermissions:
        """Create full access permissions (still asks for dangerous ops)."""
        return cls(
            read="allow",
            write="ask",
            edit="ask",
            bash="ask",
            glob="allow",
            grep="allow",
            webfetch="ask",
            task="allow",
            external_directory="ask",
        )


@dataclass
class Agent:
    """
    An agent definition with personality and capabilities.

    Agents customize how the AI assistant behaves for different tasks.
    """

    # Identity
    id: str
    name: str
    description: str

    # Behavior
    system_prompt: str
    mode: AgentMode = AgentMode.PRIMARY
    permissions: AgentPermissions = field(default_factory=AgentPermissions)

    # Model configuration
    model: str | None = None  # Override default model
    temperature: float | None = None
    top_p: float | None = None
    max_steps: int = 100  # Max tool use iterations

    # Display
    color: str = "blue"
    icon: str = ""
    hidden: bool = False

    # Tools
    enabled_tools: list[str] | None = None  # None = all tools
    disabled_tools: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "mode": self.mode.value,
            "permissions": self.permissions.to_dict(),
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_steps": self.max_steps,
            "color": self.color,
            "icon": self.icon,
            "hidden": self.hidden,
            "enabled_tools": self.enabled_tools,
            "disabled_tools": self.disabled_tools,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Agent:
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            system_prompt=data.get("system_prompt", ""),
            mode=AgentMode(data.get("mode", "primary")),
            permissions=AgentPermissions.from_dict(data.get("permissions", {})),
            model=data.get("model"),
            temperature=data.get("temperature"),
            top_p=data.get("top_p"),
            max_steps=data.get("max_steps", 100),
            color=data.get("color", "blue"),
            icon=data.get("icon", ""),
            hidden=data.get("hidden", False),
            enabled_tools=data.get("enabled_tools"),
            disabled_tools=data.get("disabled_tools", []),
        )

    def can_use_tool(self, tool_name: str) -> bool:
        """Check if this agent can use a specific tool."""
        if tool_name in self.disabled_tools:
            return False
        if self.enabled_tools is not None:
            return tool_name in self.enabled_tools
        return True

    def get_permission(self, tool_category: str) -> str:
        """Get permission level for a tool category."""
        return getattr(self.permissions, tool_category, "ask")
