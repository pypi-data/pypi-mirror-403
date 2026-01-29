"""TUI Widgets for PinkyClawd."""

from pinkyclawd.tui.widgets.prompt import PromptInput, PromptContainer, FrecencyScorer
from pinkyclawd.tui.widgets.message import MessageView, MessageList, MessageMetadata, ThinkingBlock
from pinkyclawd.tui.widgets.sidebar import (
    Sidebar,
    ContextUsage,
    MCPStatus,
    LSPStatus,
    TodoList,
    DiffSummary,
)
from pinkyclawd.tui.widgets.header import SessionHeader
from pinkyclawd.tui.widgets.footer import StatusFooter
from pinkyclawd.tui.widgets.context_bar import ContextBar
from pinkyclawd.tui.widgets.tool_view import (
    ToolView,
    BashToolView,
    GlobToolView,
    ReadToolView,
    GrepToolView,
    WriteToolView,
    EditToolView,
    TaskToolView,
    TodoWriteToolView,
    get_tool_view,
)
from pinkyclawd.tui.widgets.toast import Toast, ToastContainer, ToastMixin

__all__ = [
    # Prompt
    "PromptInput",
    "PromptContainer",
    "FrecencyScorer",
    # Message
    "MessageView",
    "MessageList",
    "MessageMetadata",
    "ThinkingBlock",
    # Sidebar
    "Sidebar",
    "ContextUsage",
    "MCPStatus",
    "LSPStatus",
    "TodoList",
    "DiffSummary",
    # Header/Footer
    "SessionHeader",
    "StatusFooter",
    "ContextBar",
    # Tool views
    "ToolView",
    "BashToolView",
    "GlobToolView",
    "ReadToolView",
    "GrepToolView",
    "WriteToolView",
    "EditToolView",
    "TaskToolView",
    "TodoWriteToolView",
    "get_tool_view",
    # Toast
    "Toast",
    "ToastContainer",
    "ToastMixin",
]
