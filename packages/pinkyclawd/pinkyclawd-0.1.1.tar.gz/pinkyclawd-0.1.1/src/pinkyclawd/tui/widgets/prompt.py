"""
Prompt input widget with autocomplete, history, and frecency.

Matches OpenCode's Prompt component with multi-line support,
file/command autocomplete, history navigation, and frecency scoring.
"""

from __future__ import annotations

import time
from collections import defaultdict
from pathlib import Path
from typing import Callable, Any

from textual.widgets import TextArea
from textual.message import Message
from textual.binding import Binding
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.widgets import Static
from rich.text import Text


class FrecencyScorer:
    """
    Frecency scoring for autocomplete suggestions.

    Combines frequency (how often) and recency (how recently)
    to prioritize suggestions.
    """

    def __init__(self, decay_rate: float = 0.99) -> None:
        self.decay_rate = decay_rate
        self.scores: dict[str, float] = defaultdict(float)
        self.last_access: dict[str, float] = {}

    def record(self, item: str) -> None:
        """Record an access to an item."""
        now = time.time()

        # Decay all scores
        for key in self.scores:
            if key in self.last_access:
                elapsed = now - self.last_access[key]
                self.scores[key] *= self.decay_rate ** (elapsed / 3600)  # Decay per hour

        # Boost the accessed item
        self.scores[item] += 1.0
        self.last_access[item] = now

    def get_score(self, item: str) -> float:
        """Get the current score for an item."""
        if item not in self.scores:
            return 0.0

        now = time.time()
        elapsed = now - self.last_access.get(item, now)
        return self.scores[item] * (self.decay_rate ** (elapsed / 3600))

    def get_sorted(self, items: list[str]) -> list[str]:
        """Sort items by frecency score (highest first)."""
        return sorted(items, key=lambda x: -self.get_score(x))


class AutocompletePopup(Vertical):
    """Popup showing autocomplete suggestions."""

    DEFAULT_CSS = """
    AutocompletePopup {
        width: 50;
        height: auto;
        max-height: 8;
        background: $surface;
        border: solid $border;
        padding: 0;
        layer: autocomplete;
        display: none;
    }

    AutocompletePopup.visible {
        display: block;
    }

    .suggestion {
        padding: 0 1;
        height: 1;
    }

    .suggestion:hover {
        background: $primary 20%;
    }

    .suggestion.selected {
        background: $primary 40%;
    }

    .suggestion-text {
        width: 1fr;
    }

    .suggestion-type {
        color: $text-muted;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.suggestions: list[tuple[str, str]] = []  # (text, type)
        self.selected_index = 0

    def compose(self) -> ComposeResult:
        for i, (text, type_) in enumerate(self.suggestions[:6]):
            classes = "suggestion selected" if i == self.selected_index else "suggestion"
            rich_text = Text()
            rich_text.append(text)
            rich_text.append(f" ({type_})", style="dim")
            yield Static(rich_text, classes=classes)

    def update_suggestions(self, suggestions: list[tuple[str, str]]) -> None:
        """Update the suggestions list."""
        self.suggestions = suggestions
        self.selected_index = 0
        if suggestions:
            self.add_class("visible")
            self.refresh(recompose=True)
        else:
            self.remove_class("visible")

    def select_next(self) -> None:
        """Select the next suggestion."""
        if self.suggestions:
            self.selected_index = (self.selected_index + 1) % len(self.suggestions[:6])
            self.refresh(recompose=True)

    def select_prev(self) -> None:
        """Select the previous suggestion."""
        if self.suggestions:
            self.selected_index = (self.selected_index - 1) % len(self.suggestions[:6])
            self.refresh(recompose=True)

    def get_selected(self) -> str | None:
        """Get the selected suggestion."""
        if self.suggestions and 0 <= self.selected_index < len(self.suggestions):
            return self.suggestions[self.selected_index][0]
        return None

    def hide(self) -> None:
        """Hide the popup."""
        self.suggestions = []
        self.remove_class("visible")


class PromptInput(TextArea):
    """
    Multi-line prompt input with autocomplete and frecency.

    Features:
    - Multi-line text input
    - File/command/agent autocomplete
    - History navigation (up/down)
    - Frecency-based suggestions
    - Shell mode (! prefix)
    - External editor support
    """

    BINDINGS = [
        Binding("enter", "submit", "Submit", show=False),
        Binding("shift+enter", "newline", "New Line", show=False),
        Binding("ctrl+enter", "newline", "New Line", show=False),
        Binding("up", "history_prev", "Previous", show=False),
        Binding("down", "history_next", "Next", show=False),
        Binding("ctrl+c", "clear", "Clear", show=False),
        Binding("tab", "autocomplete", "Autocomplete", show=False),
        Binding("escape", "cancel_autocomplete", "Cancel", show=False),
    ]

    DEFAULT_CSS = """
    PromptInput {
        height: auto;
        min-height: 1;
        max-height: 10;
    }
    """

    class Submitted(Message):
        """Message sent when prompt is submitted."""

        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value

    class HistoryNavigated(Message):
        """Message sent when navigating history."""

        def __init__(self, direction: int) -> None:
            super().__init__()
            self.direction = direction

    def __init__(
        self,
        placeholder: str = "Type your message...",
        prompt_history: list[str] | None = None,
        on_submit: Callable[[str], Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.placeholder_text = placeholder
        self.prompt_history = prompt_history or []
        self.prompt_history_index = len(self.prompt_history)
        self.stash = ""  # Stashed input when navigating history
        self.on_submit_callback = on_submit

        # Frecency scoring
        self.frecency = FrecencyScorer()
        self._autocomplete_active = False

        # Load history into frecency
        for item in self.prompt_history:
            self.frecency.record(item)

    def on_mount(self) -> None:
        """Set up the widget."""
        self.focus()

    def action_submit(self) -> None:
        """Submit the prompt."""
        value = self.text.strip()
        if not value:
            return

        # Add to history with frecency
        if not self.prompt_history or self.prompt_history[-1] != value:
            self.prompt_history.append(value)
            self.frecency.record(value)

        self.prompt_history_index = len(self.prompt_history)

        # Clear and notify
        self.clear()

        if self.on_submit_callback:
            self.on_submit_callback(value)

        self.post_message(self.Submitted(value))

    def action_newline(self) -> None:
        """Insert a newline."""
        self.insert("\n")

    def action_clear(self) -> None:
        """Clear the input."""
        self.clear()

    def action_history_prev(self) -> None:
        """Navigate to previous history entry."""
        if self._autocomplete_active:
            # Navigate autocomplete instead
            return

        if not self.prompt_history:
            return

        # Stash current input if at end
        if self.prompt_history_index == len(self.prompt_history):
            self.stash = self.text

        if self.prompt_history_index > 0:
            self.prompt_history_index -= 1
            self.text = self.prompt_history[self.prompt_history_index]
            self.move_cursor_to_end()

        self.post_message(self.HistoryNavigated(-1))

    def action_history_next(self) -> None:
        """Navigate to next history entry."""
        if self._autocomplete_active:
            # Navigate autocomplete instead
            return

        if self.prompt_history_index < len(self.prompt_history):
            self.prompt_history_index += 1

            if self.prompt_history_index == len(self.prompt_history):
                self.text = self.stash
            else:
                self.text = self.prompt_history[self.prompt_history_index]

            self.move_cursor_to_end()

        self.post_message(self.HistoryNavigated(1))

    def action_autocomplete(self) -> None:
        """Trigger autocomplete."""
        text = self.text
        cursor = self.cursor_location

        # Find word start
        line = text.split("\n")[cursor[0]] if text else ""
        word_start = cursor[1]
        while word_start > 0 and line[word_start - 1] not in " \t":
            word_start -= 1

        prefix = line[word_start:cursor[1]]

        # Determine autocomplete type
        if prefix.startswith("/"):
            self._complete_command(prefix[1:])
        elif prefix.startswith("@"):
            self._complete_agent(prefix[1:])
        elif "/" in prefix or prefix.startswith("."):
            self._complete_file(prefix)
        else:
            self._complete_history(prefix)

    def action_cancel_autocomplete(self) -> None:
        """Cancel autocomplete."""
        self._autocomplete_active = False

    def _complete_file(self, prefix: str) -> None:
        """Complete file path."""
        try:
            path = Path(prefix).expanduser()
            if path.is_absolute():
                parent = path.parent if not path.exists() else path
            else:
                parent = Path.cwd() / path.parent

            if parent.exists():
                matches = list(parent.glob(path.name + "*"))[:10]
                if len(matches) == 1:
                    self._insert_completion(prefix, str(matches[0]))
        except Exception:
            pass

    def _complete_agent(self, prefix: str) -> None:
        """Complete agent name."""
        agents = ["build", "plan", "explore", "general", "test"]
        matches = [a for a in agents if a.startswith(prefix)]
        # Sort by frecency
        matches = self.frecency.get_sorted(matches)
        if len(matches) == 1:
            self._insert_completion("@" + prefix, "@" + matches[0])

    def _complete_command(self, prefix: str) -> None:
        """Complete slash command."""
        commands = [
            "help", "new", "clear", "compact", "context",
            "model", "agent", "theme", "export", "share",
            "fork", "rename", "sessions", "quit", "timeline",
        ]
        matches = [c for c in commands if c.startswith(prefix)]
        if len(matches) == 1:
            self._insert_completion("/" + prefix, "/" + matches[0])

    def _complete_history(self, prefix: str) -> None:
        """Complete from history using frecency."""
        if not prefix:
            return

        matches = [
            h for h in self.prompt_history
            if h.lower().startswith(prefix.lower()) and h != prefix
        ]
        # Sort by frecency
        matches = self.frecency.get_sorted(matches)
        if matches:
            self._insert_completion(prefix, matches[0])

    def _insert_completion(self, old: str, new: str) -> None:
        """Insert a completion, replacing the prefix."""
        text = self.text
        cursor = self.cursor_location

        # Find and replace
        lines = text.split("\n")
        line = lines[cursor[0]]

        # Find the prefix in the line
        idx = line.rfind(old, 0, cursor[1])
        if idx >= 0:
            lines[cursor[0]] = line[:idx] + new + line[cursor[1]:]
            self.text = "\n".join(lines)
            # Move cursor to end of completion
            new_col = idx + len(new)
            self.move_cursor((cursor[0], new_col))

    def move_cursor_to_end(self) -> None:
        """Move cursor to end of text."""
        lines = self.text.split("\n")
        if lines:
            self.move_cursor((len(lines) - 1, len(lines[-1])))

    def get_history_suggestions(self, prefix: str, limit: int = 5) -> list[str]:
        """Get history suggestions sorted by frecency."""
        if not prefix:
            # Return recent items
            return self.frecency.get_sorted(self.prompt_history[-20:])[:limit]

        matches = [
            h for h in self.prompt_history
            if prefix.lower() in h.lower()
        ]
        return self.frecency.get_sorted(matches)[:limit]


class PromptContainer(Vertical):
    """Container for prompt with file badges and autocomplete."""

    DEFAULT_CSS = """
    PromptContainer {
        height: auto;
        min-height: 3;
        max-height: 15;
        border-top: solid $primary;
        padding: 1;
    }

    .file-badges {
        height: auto;
        margin-bottom: 1;
    }

    .file-badge {
        background: $primary 30%;
        padding: 0 1;
        margin-right: 1;
    }

    .prompt-info {
        height: 1;
        margin-bottom: 1;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        placeholder: str = "Type your message...",
        prompt_history: list[str] | None = None,
        files: list[str] | None = None,
        agent: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.placeholder = placeholder
        self.prompt_history = prompt_history or []
        self.files = files or []
        self.agent = agent
        self.model = model

    def compose(self) -> ComposeResult:
        # Info line (agent/model)
        if self.agent or self.model:
            info_text = Text()
            if self.agent:
                info_text.append(f"@{self.agent}", style="cyan")
            if self.model:
                if self.agent:
                    info_text.append(" | ", style="dim")
                info_text.append(self.model, style="dim")
            yield Static(info_text, classes="prompt-info")

        # File badges
        if self.files:
            with Vertical(classes="file-badges"):
                for f in self.files:
                    name = Path(f).name
                    yield Static(f"[file] {name}", classes="file-badge")

        # Prompt input
        yield PromptInput(
            placeholder=self.placeholder,
            prompt_history=self.prompt_history,
            id="prompt-input",
        )

    def add_file(self, path: str) -> None:
        """Add a file attachment."""
        if path not in self.files:
            self.files.append(path)
            self.refresh(recompose=True)

    def remove_file(self, path: str) -> None:
        """Remove a file attachment."""
        if path in self.files:
            self.files.remove(path)
            self.refresh(recompose=True)

    def clear_files(self) -> None:
        """Clear all file attachments."""
        self.files.clear()
        self.refresh(recompose=True)
