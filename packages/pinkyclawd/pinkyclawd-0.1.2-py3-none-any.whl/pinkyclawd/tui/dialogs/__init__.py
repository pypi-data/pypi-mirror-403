"""
TUI dialog components for PinkyClawd.

Provides modal dialogs for command palette, model selection,
agent selection, session management, theme selection, and help.
"""

from pinkyclawd.tui.dialogs.command import CommandPalette, CommandItem, get_default_commands
from pinkyclawd.tui.dialogs.model import ModelSelector
from pinkyclawd.tui.dialogs.agent import AgentSelector
from pinkyclawd.tui.dialogs.session import (
    SessionDialog,
    SessionRenameDialog,
    SessionShareDialog,
    SessionExportDialog,
    TimelineDialog,
)
from pinkyclawd.tui.dialogs.theme import ThemeSelector
from pinkyclawd.tui.dialogs.help import HelpDialog, StatusDialog

__all__ = [
    # Command palette
    "CommandPalette",
    "CommandItem",
    "get_default_commands",
    # Model/Agent
    "ModelSelector",
    "AgentSelector",
    # Session
    "SessionDialog",
    "SessionRenameDialog",
    "SessionShareDialog",
    "SessionExportDialog",
    "TimelineDialog",
    # Theme
    "ThemeSelector",
    # Help
    "HelpDialog",
    "StatusDialog",
]
