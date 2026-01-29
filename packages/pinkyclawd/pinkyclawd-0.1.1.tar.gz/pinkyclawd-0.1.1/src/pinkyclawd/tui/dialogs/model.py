"""
Model selector dialog.

Allows users to switch between different AI models grouped by provider.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Static, ListView, ListItem, Label


@dataclass
class ModelInfo:
    """Information about an AI model."""

    id: str
    name: str
    provider: str
    context_window: int
    description: str = ""
    is_current: bool = False

    @property
    def display_name(self) -> str:
        return f"{self.provider}/{self.name}"

    @property
    def context_display(self) -> str:
        if self.context_window >= 1_000_000:
            return f"{self.context_window // 1_000_000}M"
        if self.context_window >= 1_000:
            return f"{self.context_window // 1_000}K"
        return str(self.context_window)


class ModelListItem(ListItem):
    """A list item for a model."""

    def __init__(self, model: ModelInfo) -> None:
        super().__init__()
        self.model = model

    def compose(self) -> ComposeResult:
        with Container(classes="model-item"):
            with Horizontal():
                yield Label(self.model.name, classes="model-name")
                if self.model.is_current:
                    yield Label("(current)", classes="model-current")
                yield Label(self.model.context_display, classes="model-context")
            if self.model.description:
                yield Label(self.model.description, classes="model-description")


class ProviderHeader(Static):
    """Header for a provider group."""

    def __init__(self, provider: str) -> None:
        super().__init__(provider)
        self.add_class("provider-header")


class ModelSelector(ModalScreen[ModelInfo | None]):
    """
    Model selector modal dialog.

    Shows available models grouped by provider with context window info.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select", "Select"),
        Binding("up", "cursor_up", "Up"),
        Binding("down", "cursor_down", "Down"),
    ]

    CSS = """
    ModelSelector {
        align: center middle;
    }

    ModelSelector > Container {
        width: 70;
        max-width: 90%;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: tall $primary;
        padding: 1;
    }

    ModelSelector .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    ModelSelector ListView {
        height: auto;
        max-height: 25;
    }

    .provider-header {
        background: $primary 30%;
        padding: 0 1;
        text-style: bold;
        margin-top: 1;
    }

    .model-item {
        padding: 0 1;
    }

    .model-item Horizontal {
        height: 1;
    }

    .model-name {
        width: 1fr;
    }

    .model-current {
        color: $success;
        margin: 0 1;
    }

    .model-context {
        width: auto;
        color: $text-muted;
    }

    .model-description {
        color: $text-muted;
        text-style: italic;
    }

    ModelSelector ListItem {
        padding: 0;
    }

    ModelSelector ListItem:hover {
        background: $primary 20%;
    }

    ModelSelector ListItem.-selected {
        background: $primary 40%;
    }
    """

    def __init__(
        self,
        models: list[ModelInfo] | None = None,
        current_model: str | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self._models = models or get_default_models()
        self._current_model = current_model

        # Mark current model
        if current_model:
            for model in self._models:
                model.is_current = model.id == current_model

        self._flat_models: list[ModelInfo] = []

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Select Model", classes="title")
            yield ListView(id="model-list")

    def on_mount(self) -> None:
        """Populate the model list."""
        list_view = self.query_one("#model-list", ListView)

        # Group by provider
        providers: dict[str, list[ModelInfo]] = {}
        for model in self._models:
            if model.provider not in providers:
                providers[model.provider] = []
            providers[model.provider].append(model)

        # Add items with headers
        self._flat_models = []
        for provider in sorted(providers.keys()):
            # Skip header in flat list
            for model in providers[provider]:
                list_view.append(ModelListItem(model))
                self._flat_models.append(model)

        # Select current model
        if self._current_model:
            for i, model in enumerate(self._flat_models):
                if model.id == self._current_model:
                    list_view.index = i
                    break

    def action_cancel(self) -> None:
        """Cancel selection."""
        self.dismiss(None)

    def action_select(self) -> None:
        """Select current model."""
        list_view = self.query_one("#model-list", ListView)
        if list_view.index is not None and self._flat_models:
            selected = self._flat_models[list_view.index]
            self.dismiss(selected)

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        list_view = self.query_one("#model-list", ListView)
        if list_view.index is not None and list_view.index > 0:
            list_view.index -= 1

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        list_view = self.query_one("#model-list", ListView)
        if list_view.index is not None:
            if list_view.index < len(self._flat_models) - 1:
                list_view.index += 1

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection."""
        if isinstance(event.item, ModelListItem):
            self.dismiss(event.item.model)


def get_default_models() -> list[ModelInfo]:
    """Get the default list of available models."""
    return [
        # Anthropic
        ModelInfo(
            id="anthropic/claude-sonnet-4",
            name="claude-sonnet-4",
            provider="Anthropic",
            context_window=200_000,
            description="Best balance of speed and capability",
        ),
        ModelInfo(
            id="anthropic/claude-3-opus",
            name="claude-3-opus",
            provider="Anthropic",
            context_window=200_000,
            description="Most capable, best for complex tasks",
        ),
        ModelInfo(
            id="anthropic/claude-haiku",
            name="claude-haiku",
            provider="Anthropic",
            context_window=200_000,
            description="Fastest, best for simple tasks",
        ),
        # OpenAI
        ModelInfo(
            id="openai/gpt-4o",
            name="gpt-4o",
            provider="OpenAI",
            context_window=128_000,
            description="GPT-4 Omni - multimodal",
        ),
        ModelInfo(
            id="openai/gpt-4o-mini",
            name="gpt-4o-mini",
            provider="OpenAI",
            context_window=128_000,
            description="Smaller, faster GPT-4o",
        ),
        ModelInfo(
            id="openai/gpt-4-turbo",
            name="gpt-4-turbo",
            provider="OpenAI",
            context_window=128_000,
            description="GPT-4 Turbo with vision",
        ),
        ModelInfo(
            id="openai/o1",
            name="o1",
            provider="OpenAI",
            context_window=128_000,
            description="Reasoning model for complex tasks",
        ),
        ModelInfo(
            id="openai/o1-mini",
            name="o1-mini",
            provider="OpenAI",
            context_window=128_000,
            description="Smaller reasoning model",
        ),
    ]
