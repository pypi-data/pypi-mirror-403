"""
Slash command system for PinkyClawd.

Provides command registration, parsing, and execution for user-entered
slash commands like /help, /models, /clear, etc.
"""

from pinkyclawd.commands.registry import (
    Command,
    CommandArg,
    CommandContext,
    CommandResult,
    CommandRegistry,
    get_command_registry,
    register_command,
    execute_command,
)
from pinkyclawd.commands.builtins import register_builtin_commands

__all__ = [
    "Command",
    "CommandArg",
    "CommandContext",
    "CommandResult",
    "CommandRegistry",
    "get_command_registry",
    "register_command",
    "execute_command",
    "register_builtin_commands",
]
