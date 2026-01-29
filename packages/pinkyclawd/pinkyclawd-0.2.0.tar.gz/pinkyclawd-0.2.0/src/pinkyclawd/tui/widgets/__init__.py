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
from pinkyclawd.tui.widgets.file_tree import (
    FileTree,
    FileTreePanel,
    FileTreeNode,
    get_file_icon,
    get_dir_icon,
)
from pinkyclawd.tui.widgets.diff_view import (
    DiffView,
    DiffPanel,
    DiffMode,
    FileDiff,
    DiffLine,
    UnifiedDiffView,
    SplitDiffView,
    create_file_diff,
    compute_diff,
)
from pinkyclawd.tui.widgets.terminal import (
    Terminal,
    TerminalPanel,
    TerminalOutput,
    TerminalInput,
    TerminalSize,
)
from pinkyclawd.tui.widgets.session_tabs import (
    SessionTab,
    SessionTabBar,
    SessionTabInfo,
    SessionManager,
)
from pinkyclawd.tui.widgets.layout import (
    FlexLayout,
    Panel,
    PanelPosition,
    PanelState,
    ResizeHandle,
)

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
    # File tree
    "FileTree",
    "FileTreePanel",
    "FileTreeNode",
    "get_file_icon",
    "get_dir_icon",
    # Diff view
    "DiffView",
    "DiffPanel",
    "DiffMode",
    "FileDiff",
    "DiffLine",
    "UnifiedDiffView",
    "SplitDiffView",
    "create_file_diff",
    "compute_diff",
    # Terminal
    "Terminal",
    "TerminalPanel",
    "TerminalOutput",
    "TerminalInput",
    "TerminalSize",
    # Session tabs
    "SessionTab",
    "SessionTabBar",
    "SessionTabInfo",
    "SessionManager",
    # Layout
    "FlexLayout",
    "Panel",
    "PanelPosition",
    "PanelState",
    "ResizeHandle",
]
