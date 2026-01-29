"""Tool system for PinkyClawd."""

from pinkyclawd.tool.base import (
    Tool,
    ToolContext,
    ToolResult,
    ToolPermission,
    PermissionRule,
)
from pinkyclawd.tool.registry import (
    ToolRegistry,
    get_tool_registry,
)

# Core tools
from pinkyclawd.tool.bash import BashTool
from pinkyclawd.tool.read import ReadTool
from pinkyclawd.tool.write import WriteTool
from pinkyclawd.tool.edit import EditTool
from pinkyclawd.tool.multiedit import MultiEditTool
from pinkyclawd.tool.list import ListTool
from pinkyclawd.tool.glob import GlobTool
from pinkyclawd.tool.grep import GrepTool
from pinkyclawd.tool.apply_patch import ApplyPatchTool
from pinkyclawd.tool.batch import BatchTool
from pinkyclawd.tool.todo import TodoWriteTool, TodoReadTool
from pinkyclawd.tool.task import TaskTool
from pinkyclawd.tool.webfetch import WebFetchTool
from pinkyclawd.tool.websearch import WebSearchTool
from pinkyclawd.tool.codesearch import CodeSearchTool
from pinkyclawd.tool.question import QuestionTool
from pinkyclawd.tool.plan import PlanEnterTool, PlanExitTool
from pinkyclawd.tool.skill import SkillTool
from pinkyclawd.tool.lsp import LSPTool
from pinkyclawd.tool.memory import MemoryTool, RLMQueryTool

# Error handling and utilities
from pinkyclawd.tool.invalid import InvalidTool
from pinkyclawd.tool.truncation import (
    truncate_output,
    apply_truncation,
    cleanup_old_outputs,
    TruncationResult,
    MAX_LINES,
    MAX_BYTES,
)
from pinkyclawd.tool.external_directory import (
    assert_external_directory,
    is_within_project,
    check_external_path,
    get_project_root,
)

__all__ = [
    # Base classes
    "Tool",
    "ToolContext",
    "ToolResult",
    "ToolPermission",
    "PermissionRule",
    "ToolRegistry",
    "get_tool_registry",
    # Core file operations
    "BashTool",
    "ReadTool",
    "WriteTool",
    "EditTool",
    "MultiEditTool",
    "ListTool",
    "GlobTool",
    "GrepTool",
    # Patch and batch
    "ApplyPatchTool",
    "BatchTool",
    # Task management
    "TodoWriteTool",
    "TodoReadTool",
    "TaskTool",
    # Web operations
    "WebFetchTool",
    "WebSearchTool",
    "CodeSearchTool",
    # User interaction
    "QuestionTool",
    # Mode switching
    "PlanEnterTool",
    "PlanExitTool",
    "SkillTool",
    # LSP
    "LSPTool",
    # RLM memory
    "MemoryTool",
    "RLMQueryTool",
    # Error handling
    "InvalidTool",
    # Truncation utilities
    "truncate_output",
    "apply_truncation",
    "cleanup_old_outputs",
    "TruncationResult",
    "MAX_LINES",
    "MAX_BYTES",
    # External directory utilities
    "assert_external_directory",
    "is_within_project",
    "check_external_path",
    "get_project_root",
]
