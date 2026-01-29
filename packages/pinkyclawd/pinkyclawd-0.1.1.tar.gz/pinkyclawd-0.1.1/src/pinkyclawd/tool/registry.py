"""
Tool registry for managing available tools.
"""

from __future__ import annotations

from typing import Any

from pinkyclawd.tool.base import (
    Tool,
    ToolContext,
    ToolResult,
    PermissionRule,
    ToolPermission,
)
from pinkyclawd.tool.bash import BashTool
from pinkyclawd.tool.read import ReadTool
from pinkyclawd.tool.write import WriteTool
from pinkyclawd.tool.edit import EditTool
from pinkyclawd.tool.glob import GlobTool
from pinkyclawd.tool.grep import GrepTool
from pinkyclawd.tool.todo import TodoWriteTool, TodoReadTool
from pinkyclawd.tool.webfetch import WebFetchTool
from pinkyclawd.tool.question import QuestionTool
from pinkyclawd.tool.task import TaskTool
from pinkyclawd.tool.memory import MemoryTool, RLMQueryTool
from pinkyclawd.tool.list import ListTool
from pinkyclawd.tool.multiedit import MultiEditTool
from pinkyclawd.tool.batch import BatchTool
from pinkyclawd.tool.apply_patch import ApplyPatchTool
from pinkyclawd.tool.websearch import WebSearchTool
from pinkyclawd.tool.codesearch import CodeSearchTool
from pinkyclawd.tool.skill import SkillTool
from pinkyclawd.tool.plan import PlanEnterTool, PlanExitTool
from pinkyclawd.tool.lsp import LSPTool


class ToolRegistry:
    """
    Registry for all available tools.

    Manages tool registration, permission checking, and execution.
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._permissions: dict[str, dict[str, PermissionRule]] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register built-in tools."""
        builtins = [
            # Core file operations
            BashTool(),
            ReadTool(),
            WriteTool(),
            EditTool(),
            MultiEditTool(),
            ListTool(),
            GlobTool(),
            GrepTool(),
            # Patch and batch operations
            ApplyPatchTool(),
            BatchTool(),
            # Task management
            TodoWriteTool(),
            TodoReadTool(),
            TaskTool(),
            # Web operations
            WebFetchTool(),
            WebSearchTool(),
            CodeSearchTool(),
            # User interaction
            QuestionTool(),
            # Mode switching
            PlanEnterTool(),
            PlanExitTool(),
            SkillTool(),
            # LSP
            LSPTool(),
            # RLM memory
            MemoryTool(),
            RLMQueryTool(),
        ]

        for tool in builtins:
            self.register(tool)

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        self._tools.pop(name, None)

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_schemas(self) -> list[dict[str, Any]]:
        """Get schemas for all tools (for function calling)."""
        return [tool.to_schema() for tool in self._tools.values()]

    def set_permissions(
        self,
        tool_name: str,
        rules: dict[str, PermissionRule],
    ) -> None:
        """Set permission rules for a tool."""
        self._permissions[tool_name] = rules

    def set_permission_from_config(self, config: dict[str, Any]) -> None:
        """Set permissions from config format."""
        for tool_name, rule_config in config.items():
            if isinstance(rule_config, str):
                # Simple rule: "allow", "ask", "deny"
                self._permissions[tool_name] = {
                    "*": PermissionRule("*", ToolPermission(rule_config))
                }
            elif isinstance(rule_config, dict):
                # Pattern-based rules: {"*.py": "allow", "*": "ask"}
                rules = {}
                for pattern, permission in rule_config.items():
                    rules[pattern] = PermissionRule(pattern, ToolPermission(permission))
                self._permissions[tool_name] = rules

    def get_permissions(self, tool_name: str) -> dict[str, PermissionRule]:
        """Get permission rules for a tool."""
        return self._permissions.get(
            tool_name, {"*": PermissionRule("*", ToolPermission.ASK)}
        )

    async def execute(
        self,
        tool_name: str,
        ctx: ToolContext,
        arguments: dict[str, Any],
    ) -> ToolResult:
        """
        Execute a tool with permission checking.

        Args:
            tool_name: Name of the tool to execute
            ctx: Execution context
            arguments: Tool arguments

        Returns:
            Tool result
        """
        tool = self.get(tool_name)
        if not tool:
            return ToolResult.fail(f"Unknown tool: {tool_name}")

        # Check permissions
        if tool.requires_confirmation and not ctx.user_confirmed:
            permissions = self.get_permissions(tool.permission_category)

            # Determine what value to check (e.g., file path, command)
            check_value = arguments.get("filePath") or arguments.get("command") or "*"

            if not await tool.check_permission(ctx, permissions, check_value):
                return ToolResult.fail(f"Permission denied for {tool_name}")

        try:
            return await tool.execute(ctx, **arguments)
        except Exception as e:
            return ToolResult.fail(f"Tool execution failed: {e}")


# Global registry
_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
