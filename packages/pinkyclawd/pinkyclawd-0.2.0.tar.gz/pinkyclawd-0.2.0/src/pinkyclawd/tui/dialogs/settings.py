"""
Settings dialogs for PinkyClawd TUI.

Matches OpenCode's settings panels:
- General settings
- Keybinds
- Models
- Providers
- MCP servers
- Permissions
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Label,
    ListItem,
    ListView,
    Select,
    Static,
    Switch,
    Tabs,
    Tab,
    TabPane,
    TabbedContent,
)
from rich.text import Text


class SettingsTab(Enum):
    """Settings tab types."""

    GENERAL = "general"
    APPEARANCE = "appearance"
    KEYBINDS = "keybinds"
    MODELS = "models"
    PROVIDERS = "providers"
    MCP = "mcp"
    PERMISSIONS = "permissions"
    COMMANDS = "commands"


@dataclass
class SettingItem:
    """A single setting item."""

    key: str
    label: str
    description: str
    value: Any
    type: str  # "toggle", "text", "select", "number"
    options: list[tuple[str, str]] | None = None  # For select type
    min_value: int | None = None  # For number type
    max_value: int | None = None


class SettingRow(Horizontal):
    """A single setting row with label, description, and control."""

    DEFAULT_CSS = """
    SettingRow {
        height: auto;
        min-height: 4;
        padding: 1;
        border-bottom: solid $border;
    }

    SettingRow:hover {
        background: $surface;
    }

    .setting-info {
        width: 2fr;
    }

    .setting-label {
        text-style: bold;
    }

    .setting-description {
        color: $text-muted;
    }

    .setting-control {
        width: 1fr;
        content-align: right middle;
    }

    .setting-control Input {
        width: 100%;
    }

    .setting-control Select {
        width: 100%;
    }
    """

    def __init__(
        self,
        setting: SettingItem,
        on_change: Callable[[str, Any], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.setting = setting
        self._on_change = on_change

    def compose(self) -> ComposeResult:
        # Info section
        with Vertical(classes="setting-info"):
            yield Static(self.setting.label, classes="setting-label")
            yield Static(self.setting.description, classes="setting-description")

        # Control section
        with Vertical(classes="setting-control"):
            if self.setting.type == "toggle":
                yield Switch(value=bool(self.setting.value), id=f"setting-{self.setting.key}")
            elif self.setting.type == "text":
                yield Input(
                    value=str(self.setting.value or ""),
                    id=f"setting-{self.setting.key}",
                )
            elif self.setting.type == "number":
                yield Input(
                    value=str(self.setting.value or 0),
                    type="integer",
                    id=f"setting-{self.setting.key}",
                )
            elif self.setting.type == "select" and self.setting.options:
                yield Select(
                    [(label, value) for value, label in self.setting.options],
                    value=self.setting.value,
                    id=f"setting-{self.setting.key}",
                )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle toggle change."""
        if self._on_change:
            self._on_change(self.setting.key, event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle text/number input."""
        if self._on_change:
            value = event.value
            if self.setting.type == "number":
                try:
                    value = int(value)
                except ValueError:
                    value = 0
            self._on_change(self.setting.key, value)

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select change."""
        if self._on_change:
            self._on_change(self.setting.key, event.value)


class GeneralSettingsPane(ScrollableContainer):
    """General settings panel."""

    DEFAULT_CSS = """
    GeneralSettingsPane {
        height: 100%;
        padding: 1;
    }

    .section-title {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
        color: $primary;
    }
    """

    def __init__(
        self,
        settings: dict[str, Any] | None = None,
        on_change: Callable[[str, Any], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._settings = settings or {}
        self._on_change = on_change

    def compose(self) -> ComposeResult:
        yield Static("Behavior", classes="section-title")

        yield SettingRow(
            SettingItem(
                key="auto_save",
                label="Auto-save sessions",
                description="Automatically save session data periodically",
                value=self._settings.get("auto_save", True),
                type="toggle",
            ),
            on_change=self._on_change,
        )

        yield SettingRow(
            SettingItem(
                key="confirm_exit",
                label="Confirm on exit",
                description="Show confirmation when exiting the application",
                value=self._settings.get("confirm_exit", True),
                type="toggle",
            ),
            on_change=self._on_change,
        )

        yield SettingRow(
            SettingItem(
                key="stream_responses",
                label="Stream responses",
                description="Show responses as they are generated",
                value=self._settings.get("stream_responses", True),
                type="toggle",
            ),
            on_change=self._on_change,
        )

        yield Static("RLM Settings", classes="section-title")

        yield SettingRow(
            SettingItem(
                key="rlm_enabled",
                label="Enable RLM",
                description="Enable Recursive Language Model for unlimited context",
                value=self._settings.get("rlm_enabled", True),
                type="toggle",
            ),
            on_change=self._on_change,
        )

        yield SettingRow(
            SettingItem(
                key="rlm_auto_retrieve",
                label="Auto-retrieve context",
                description="Automatically retrieve relevant archived context",
                value=self._settings.get("rlm_auto_retrieve", True),
                type="toggle",
            ),
            on_change=self._on_change,
        )

        yield SettingRow(
            SettingItem(
                key="rlm_threshold_ratio",
                label="Archive threshold",
                description="Trigger archival at this context usage ratio",
                value=self._settings.get("rlm_threshold_ratio", "0.33"),
                type="select",
                options=[
                    ("0.25", "25%"),
                    ("0.33", "33% (default)"),
                    ("0.40", "40%"),
                    ("0.50", "50%"),
                ],
            ),
            on_change=self._on_change,
        )


class AppearanceSettingsPane(ScrollableContainer):
    """Appearance settings panel."""

    DEFAULT_CSS = """
    AppearanceSettingsPane {
        height: 100%;
        padding: 1;
    }

    .section-title {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
        color: $primary;
    }

    .theme-preview {
        height: 8;
        margin: 1 0;
        border: solid $border;
        padding: 1;
    }
    """

    def __init__(
        self,
        settings: dict[str, Any] | None = None,
        themes: list[tuple[str, str]] | None = None,
        on_change: Callable[[str, Any], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._settings = settings or {}
        self._themes = themes or []
        self._on_change = on_change

    def compose(self) -> ComposeResult:
        yield Static("Theme", classes="section-title")

        yield SettingRow(
            SettingItem(
                key="theme",
                label="Color theme",
                description="Select the application color theme",
                value=self._settings.get("theme", "pinkyclawd"),
                type="select",
                options=self._themes or [("pinkyclawd", "PinkyClawd (default)")],
            ),
            on_change=self._on_change,
        )

        yield Static("Display", classes="section-title")

        yield SettingRow(
            SettingItem(
                key="show_timestamps",
                label="Show timestamps",
                description="Display message timestamps",
                value=self._settings.get("show_timestamps", True),
                type="toggle",
            ),
            on_change=self._on_change,
        )

        yield SettingRow(
            SettingItem(
                key="show_thinking",
                label="Show thinking blocks",
                description="Display AI thinking/reasoning blocks",
                value=self._settings.get("show_thinking", True),
                type="toggle",
            ),
            on_change=self._on_change,
        )

        yield SettingRow(
            SettingItem(
                key="show_tool_details",
                label="Expand tool details",
                description="Show full tool input/output by default",
                value=self._settings.get("show_tool_details", False),
                type="toggle",
            ),
            on_change=self._on_change,
        )

        yield SettingRow(
            SettingItem(
                key="code_line_numbers",
                label="Code line numbers",
                description="Show line numbers in code blocks",
                value=self._settings.get("code_line_numbers", True),
                type="toggle",
            ),
            on_change=self._on_change,
        )


class KeybindsSettingsPane(ScrollableContainer):
    """Keybinds settings panel."""

    DEFAULT_CSS = """
    KeybindsSettingsPane {
        height: 100%;
        padding: 1;
    }

    .keybind-row {
        height: 3;
        padding: 0 1;
        border-bottom: solid $border;
    }

    .keybind-row:hover {
        background: $surface;
    }

    .keybind-action {
        width: 2fr;
        text-style: bold;
    }

    .keybind-key {
        width: 1fr;
        background: $primary 20%;
        padding: 0 1;
        text-align: center;
    }

    .keybind-edit {
        width: auto;
        padding: 0 1;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        keybinds: dict[str, str] | None = None,
        on_change: Callable[[str, str], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._keybinds = keybinds or self._get_default_keybinds()
        self._on_change = on_change

    def _get_default_keybinds(self) -> dict[str, str]:
        return {
            "submit": "Enter",
            "newline": "Shift+Enter",
            "command_palette": "Ctrl+P",
            "new_session": "Ctrl+N",
            "toggle_sidebar": "Ctrl+B",
            "toggle_terminal": "Ctrl+`",
            "toggle_explorer": "Ctrl+E",
            "select_model": "Ctrl+M",
            "select_agent": "Ctrl+A",
            "interrupt": "Escape",
            "copy": "Ctrl+C",
            "paste": "Ctrl+V",
            "clear": "Ctrl+L",
            "quit": "Ctrl+Q",
        }

    def compose(self) -> ComposeResult:
        for action, key in self._keybinds.items():
            with Horizontal(classes="keybind-row"):
                yield Static(action.replace("_", " ").title(), classes="keybind-action")
                yield Static(key, classes="keybind-key")
                yield Static("[Edit]", classes="keybind-edit")


class ModelsSettingsPane(ScrollableContainer):
    """Models settings panel."""

    DEFAULT_CSS = """
    ModelsSettingsPane {
        height: 100%;
        padding: 1;
    }

    .section-title {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
        color: $primary;
    }

    .model-card {
        height: auto;
        min-height: 5;
        padding: 1;
        margin-bottom: 1;
        border: solid $border;
        background: $surface;
    }

    .model-card:hover {
        border: solid $primary;
    }

    .model-card.active {
        border: thick $primary;
        background: $primary 10%;
    }

    .model-name {
        text-style: bold;
    }

    .model-provider {
        color: $text-muted;
    }

    .model-info {
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        models: list[dict[str, Any]] | None = None,
        current_model: str | None = None,
        on_select: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._models = models or self._get_default_models()
        self._current_model = current_model
        self._on_select = on_select

    def _get_default_models(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "claude-sonnet-4-20250514",
                "name": "Claude Sonnet 4",
                "provider": "anthropic",
                "context": 200000,
                "description": "Most capable model for coding",
            },
            {
                "id": "claude-3-5-haiku-20241022",
                "name": "Claude 3.5 Haiku",
                "provider": "anthropic",
                "context": 200000,
                "description": "Fast and affordable",
            },
            {
                "id": "gpt-4-turbo",
                "name": "GPT-4 Turbo",
                "provider": "openai",
                "context": 128000,
                "description": "OpenAI's latest GPT-4",
            },
            {
                "id": "gpt-4o",
                "name": "GPT-4o",
                "provider": "openai",
                "context": 128000,
                "description": "OpenAI's optimized GPT-4",
            },
        ]

    def compose(self) -> ComposeResult:
        yield Static("Available Models", classes="section-title")

        for model in self._models:
            is_active = model["id"] == self._current_model
            classes = "model-card active" if is_active else "model-card"

            with Vertical(classes=classes):
                with Horizontal():
                    yield Static(model["name"], classes="model-name")
                    yield Static(f" ({model['provider']})", classes="model-provider")

                info = f"{model['context']:,} tokens | {model['description']}"
                yield Static(info, classes="model-info")


class ProvidersSettingsPane(ScrollableContainer):
    """Providers settings panel."""

    DEFAULT_CSS = """
    ProvidersSettingsPane {
        height: 100%;
        padding: 1;
    }

    .section-title {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
        color: $primary;
    }

    .provider-card {
        height: auto;
        min-height: 4;
        padding: 1;
        margin-bottom: 1;
        border: solid $border;
        background: $surface;
    }

    .provider-header {
        height: 2;
    }

    .provider-name {
        text-style: bold;
    }

    .provider-status {
        color: $text-muted;
    }

    .provider-status.connected {
        color: $success;
    }

    .provider-status.error {
        color: $error;
    }

    .provider-key {
        margin-top: 1;
    }
    """

    def __init__(
        self,
        providers: dict[str, dict[str, Any]] | None = None,
        on_configure: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._providers = providers or self._get_default_providers()
        self._on_configure = on_configure

    def _get_default_providers(self) -> dict[str, dict[str, Any]]:
        return {
            "anthropic": {
                "name": "Anthropic",
                "description": "Claude models (Sonnet 4, Haiku, etc.)",
                "status": "connected",
                "api_key_set": True,
            },
            "openai": {
                "name": "OpenAI",
                "description": "GPT-4, GPT-4o models",
                "status": "not_configured",
                "api_key_set": False,
            },
            "groq": {
                "name": "Groq",
                "description": "Fast inference for open models",
                "status": "not_configured",
                "api_key_set": False,
            },
            "ollama": {
                "name": "Ollama",
                "description": "Local model inference",
                "status": "not_configured",
                "api_key_set": False,
            },
        }

    def compose(self) -> ComposeResult:
        yield Static("Configured Providers", classes="section-title")

        for provider_id, provider in self._providers.items():
            status_class = f"provider-status {provider['status']}"

            with Vertical(classes="provider-card"):
                with Horizontal(classes="provider-header"):
                    yield Static(provider["name"], classes="provider-name")
                    status_text = {
                        "connected": "● Connected",
                        "error": "● Error",
                        "not_configured": "○ Not configured",
                    }.get(provider["status"], "○ Unknown")
                    yield Static(status_text, classes=status_class)

                yield Static(provider["description"], classes="provider-description")

                with Horizontal(classes="provider-key"):
                    if provider["api_key_set"]:
                        yield Static("API key: ****", classes="provider-key-set")
                    else:
                        yield Button("Configure", id=f"configure-{provider_id}")


class MCPSettingsPane(ScrollableContainer):
    """MCP servers settings panel."""

    DEFAULT_CSS = """
    MCPSettingsPane {
        height: 100%;
        padding: 1;
    }

    .section-title {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
        color: $primary;
    }

    .mcp-server {
        height: auto;
        min-height: 4;
        padding: 1;
        margin-bottom: 1;
        border: solid $border;
        background: $surface;
    }

    .mcp-name {
        text-style: bold;
    }

    .mcp-command {
        color: $text-muted;
        font-family: monospace;
    }

    .mcp-status.connected {
        color: $success;
    }

    .mcp-status.disconnected {
        color: $error;
    }
    """

    def __init__(
        self,
        servers: dict[str, dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._servers = servers or {}

    def compose(self) -> ComposeResult:
        yield Static("MCP Servers", classes="section-title")

        if not self._servers:
            yield Static("No MCP servers configured", classes="text-muted")
            yield Button("Add Server", id="add-mcp-server")
            return

        for name, server in self._servers.items():
            status = server.get("status", "disconnected")
            status_class = f"mcp-status {status}"

            with Vertical(classes="mcp-server"):
                with Horizontal():
                    yield Static(name, classes="mcp-name")
                    status_icon = "●" if status == "connected" else "○"
                    yield Static(f" {status_icon} {status}", classes=status_class)

                command = server.get("command", "")
                yield Static(f"$ {command}", classes="mcp-command")

        yield Button("Add Server", id="add-mcp-server")


class SettingsDialog(ModalScreen[dict[str, Any] | None]):
    """
    Complete settings dialog with tabbed interface.

    Features:
    - Multiple settings categories
    - Tab navigation
    - Live preview (for themes)
    - Save/Cancel
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save"),
    ]

    CSS = """
    SettingsDialog {
        align: center middle;
    }

    SettingsDialog > Container {
        width: 90%;
        max-width: 100;
        height: 90%;
        max-height: 40;
        background: $panel;
        border: thick $primary;
    }

    .settings-header {
        height: 3;
        padding: 1;
        background: $surface;
        border-bottom: solid $border;
    }

    .settings-title {
        text-style: bold;
    }

    .settings-body {
        height: 1fr;
    }

    .settings-footer {
        height: 3;
        padding: 0 1;
        background: $surface;
        border-top: solid $border;
        content-align: right middle;
    }

    .settings-footer Button {
        margin-left: 1;
    }
    """

    def __init__(
        self,
        settings: dict[str, Any] | None = None,
        themes: list[tuple[str, str]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._settings = settings or {}
        self._themes = themes or []
        self._changes: dict[str, Any] = {}

    def compose(self) -> ComposeResult:
        from textual.containers import Container

        with Container():
            # Header
            with Horizontal(classes="settings-header"):
                yield Static("Settings", classes="settings-title")

            # Body with tabs
            with TabbedContent(classes="settings-body"):
                with TabPane("General", id="tab-general"):
                    yield GeneralSettingsPane(
                        settings=self._settings,
                        on_change=self._on_setting_change,
                    )

                with TabPane("Appearance", id="tab-appearance"):
                    yield AppearanceSettingsPane(
                        settings=self._settings,
                        themes=self._themes,
                        on_change=self._on_setting_change,
                    )

                with TabPane("Keybinds", id="tab-keybinds"):
                    yield KeybindsSettingsPane()

                with TabPane("Models", id="tab-models"):
                    yield ModelsSettingsPane(
                        current_model=self._settings.get("model"),
                    )

                with TabPane("Providers", id="tab-providers"):
                    yield ProvidersSettingsPane()

                with TabPane("MCP", id="tab-mcp"):
                    yield MCPSettingsPane()

            # Footer
            with Horizontal(classes="settings-footer"):
                yield Button("Cancel", id="cancel")
                yield Button("Save", variant="primary", id="save")

    def _on_setting_change(self, key: str, value: Any) -> None:
        """Handle setting change."""
        self._changes[key] = value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "save":
            # Merge changes with original settings
            result = {**self._settings, **self._changes}
            self.dismiss(result)

    def action_cancel(self) -> None:
        """Cancel and close."""
        self.dismiss(None)

    def action_save(self) -> None:
        """Save and close."""
        result = {**self._settings, **self._changes}
        self.dismiss(result)
