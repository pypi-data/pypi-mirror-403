"""
Command palette dialog with fuzzy search.

Provides quick access to all commands and actions via Ctrl+P.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Awaitable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Static, ListView, ListItem, Label


@dataclass
class CommandItem:
    """A command that can be executed from the palette."""

    id: str
    label: str
    description: str
    shortcut: str | None = None
    category: str = "General"
    action: Callable[[], Any] | Callable[[], Awaitable[Any]] | None = None

    def matches(self, query: str) -> bool:
        """Check if this command matches a search query."""
        query = query.lower()
        return (
            query in self.label.lower()
            or query in self.description.lower()
            or query in self.id.lower()
            or query in self.category.lower()
        )

    def score(self, query: str) -> int:
        """Score how well this command matches the query."""
        query = query.lower()
        score = 0

        # Exact match in label
        if query == self.label.lower():
            score += 100

        # Starts with query
        if self.label.lower().startswith(query):
            score += 50

        # Contains in label
        if query in self.label.lower():
            score += 25

        # Contains in description
        if query in self.description.lower():
            score += 10

        # Contains in category
        if query in self.category.lower():
            score += 5

        return score


class CommandListItem(ListItem):
    """A list item for a command."""

    def __init__(self, command: CommandItem) -> None:
        super().__init__()
        self.command = command

    def compose(self) -> ComposeResult:
        with Container(classes="command-item"):
            yield Label(self.command.label, classes="command-label")
            if self.command.shortcut:
                yield Label(self.command.shortcut, classes="command-shortcut")
            yield Label(self.command.description, classes="command-description")


class CommandPalette(ModalScreen[CommandItem | None]):
    """
    Command palette modal for quick command access.

    Opened with Ctrl+P, provides fuzzy search across all commands.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select", "Select"),
        Binding("up", "cursor_up", "Up"),
        Binding("down", "cursor_down", "Down"),
    ]

    CSS = """
    CommandPalette {
        align: center middle;
    }

    CommandPalette > Container {
        width: 80;
        max-width: 90%;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: tall $primary;
        padding: 1;
    }

    CommandPalette Input {
        width: 100%;
        margin-bottom: 1;
    }

    CommandPalette ListView {
        height: auto;
        max-height: 20;
    }

    .command-item {
        layout: horizontal;
        width: 100%;
        padding: 0 1;
    }

    .command-label {
        width: 1fr;
        text-style: bold;
    }

    .command-shortcut {
        width: auto;
        color: $text-muted;
        margin-right: 2;
    }

    .command-description {
        width: 2fr;
        color: $text-muted;
    }

    CommandPalette ListItem {
        padding: 0;
    }

    CommandPalette ListItem:hover {
        background: $primary 20%;
    }

    CommandPalette ListItem.-selected {
        background: $primary 40%;
    }
    """

    def __init__(
        self,
        commands: list[CommandItem] | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self._commands = commands or []
        self._filtered_commands: list[CommandItem] = []

    def compose(self) -> ComposeResult:
        with Container():
            yield Input(placeholder="Type to search commands...", id="search")
            yield ListView(id="command-list")

    def on_mount(self) -> None:
        """Initialize the command list."""
        self._update_list("")
        self.query_one("#search", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        self._update_list(event.value)

    def _update_list(self, query: str) -> None:
        """Update the command list based on search query."""
        list_view = self.query_one("#command-list", ListView)
        list_view.clear()

        if query:
            # Filter and sort by score
            matches = [(cmd, cmd.score(query)) for cmd in self._commands if cmd.matches(query)]
            matches.sort(key=lambda x: x[1], reverse=True)
            self._filtered_commands = [cmd for cmd, _ in matches]
        else:
            # Show all commands grouped by category
            self._filtered_commands = sorted(
                self._commands,
                key=lambda c: (c.category, c.label),
            )

        for command in self._filtered_commands:
            list_view.append(CommandListItem(command))

        # Select first item
        if self._filtered_commands:
            list_view.index = 0

    def action_cancel(self) -> None:
        """Cancel and close the palette."""
        self.dismiss(None)

    def action_select(self) -> None:
        """Select the current command."""
        list_view = self.query_one("#command-list", ListView)
        if list_view.index is not None and self._filtered_commands:
            selected = self._filtered_commands[list_view.index]
            self.dismiss(selected)

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        list_view = self.query_one("#command-list", ListView)
        if list_view.index is not None and list_view.index > 0:
            list_view.index -= 1

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        list_view = self.query_one("#command-list", ListView)
        if list_view.index is not None:
            if list_view.index < len(self._filtered_commands) - 1:
                list_view.index += 1

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle list item selection."""
        if isinstance(event.item, CommandListItem):
            self.dismiss(event.item.command)


def get_default_commands() -> list[CommandItem]:
    """Get the default set of commands for the palette."""
    return [
        # Session commands
        CommandItem(
            id="session.new",
            label="New Session",
            description="Start a new conversation session",
            shortcut="Ctrl+N",
            category="Session",
        ),
        CommandItem(
            id="session.list",
            label="Session List",
            description="View and switch between sessions",
            shortcut="Ctrl+S",
            category="Session",
        ),
        CommandItem(
            id="session.export",
            label="Export Session",
            description="Export current session to file",
            category="Session",
        ),
        CommandItem(
            id="session.fork",
            label="Fork Session",
            description="Create a branch from current point",
            category="Session",
        ),
        # Model commands
        CommandItem(
            id="model.select",
            label="Select Model",
            description="Change the AI model",
            shortcut="Ctrl+M",
            category="Model",
        ),
        CommandItem(
            id="model.info",
            label="Model Info",
            description="Show current model information",
            category="Model",
        ),
        # Agent commands
        CommandItem(
            id="agent.select",
            label="Select Agent",
            description="Change the active agent",
            shortcut="Ctrl+A",
            category="Agent",
        ),
        CommandItem(
            id="agent.cycle",
            label="Cycle Agent",
            description="Switch to next agent",
            shortcut="Tab",
            category="Agent",
        ),
        # View commands
        CommandItem(
            id="view.theme",
            label="Change Theme",
            description="Select a different color theme",
            shortcut="Ctrl+T",
            category="View",
        ),
        CommandItem(
            id="view.sidebar",
            label="Toggle Sidebar",
            description="Show/hide the sidebar",
            shortcut="Ctrl+B",
            category="View",
        ),
        CommandItem(
            id="view.context",
            label="Show Context",
            description="View RLM context usage",
            category="View",
        ),
        # Edit commands
        CommandItem(
            id="edit.clear",
            label="Clear Messages",
            description="Clear the current conversation",
            category="Edit",
        ),
        CommandItem(
            id="edit.copy",
            label="Copy Last Response",
            description="Copy the last assistant response",
            shortcut="Ctrl+C",
            category="Edit",
        ),
        # Help commands
        CommandItem(
            id="help.docs",
            label="Open Documentation",
            description="View the documentation",
            shortcut="F1",
            category="Help",
        ),
        CommandItem(
            id="help.shortcuts",
            label="Keyboard Shortcuts",
            description="View all keyboard shortcuts",
            category="Help",
        ),
    ]
