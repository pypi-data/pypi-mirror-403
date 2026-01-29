"""
Main TUI Application using Textual framework.

Matches OpenCode's layout and features with:
- Resizable panels (sidebar, explorer, terminal)
- Session tabs
- File tree
- Diff view
- Terminal integration
- Full RLM integration
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Static
from textual.worker import Worker

from pinkyclawd.config import get_config, load_config
from pinkyclawd.config.storage import (
    Message,
    MessagePart,
    MessageRole,
    PartType,
    Session,
    get_storage,
)
from pinkyclawd.config.theme import get_theme_manager, get_current_theme, BUILTIN_THEMES
from pinkyclawd.config.keybind import get_keybind_manager
from pinkyclawd.events import get_event_bus, EventType, Event
from pinkyclawd.provider.registry import get_provider
from pinkyclawd.rlm import (
    prepare_messages_with_rlm,
    update_after_response,
    detect_task_completion,
    get_rlm_handler,
    register_event_handlers,
)

# Import widgets
from pinkyclawd.tui.widgets.prompt import PromptInput
from pinkyclawd.tui.widgets.message import MessageList, MessageView
from pinkyclawd.tui.widgets.context_bar import ContextBar
from pinkyclawd.tui.widgets.sidebar import Sidebar
from pinkyclawd.tui.widgets.session_tabs import SessionTabBar, SessionTabInfo
from pinkyclawd.tui.widgets.file_tree import FileTreePanel
from pinkyclawd.tui.widgets.diff_view import DiffPanel, FileDiff
from pinkyclawd.tui.widgets.terminal import TerminalPanel
from pinkyclawd.tui.widgets.layout import FlexLayout, Panel, PanelPosition


class PinkyClawdApp(App):
    """
    PinkyClawd TUI Application with full RLM integration.

    Features:
    - Multi-panel layout with resizable areas
    - Session tabs for multiple conversations
    - File tree for project navigation
    - Diff view for code changes
    - Terminal integration
    - Streaming message display
    - Token usage tracking with context bar
    - RLM automatic context archival and retrieval
    """

    TITLE = "PinkyClawd"
    SUB_TITLE = "AI-Powered Development"

    CSS = """
    Screen {
        background: $surface;
    }

    /* Main layout */
    #main-layout {
        width: 100%;
        height: 100%;
    }

    /* Header bar with session tabs */
    #header-bar {
        height: 3;
        background: $panel;
        border-bottom: solid $border;
    }

    .app-title {
        width: auto;
        padding: 0 2;
        text-style: bold;
        color: $primary;
    }

    /* Sidebar */
    #sidebar-panel {
        width: 32;
        background: $panel;
        border-right: solid $border;
    }

    #sidebar-panel.collapsed {
        display: none;
    }

    /* Explorer panel */
    #explorer-panel {
        width: 28;
        background: $panel;
        border-right: solid $border;
        display: none;
    }

    #explorer-panel.visible {
        display: block;
    }

    /* Content area */
    #content-area {
        width: 1fr;
    }

    #messages {
        height: 1fr;
        overflow-y: scroll;
        padding: 1;
    }

    #context-bar {
        height: 3;
        padding: 0 1;
        background: $panel;
        border-top: solid $border;
    }

    #prompt-container {
        height: auto;
        min-height: 3;
        max-height: 12;
        border-top: solid $primary;
        padding: 1;
        background: $surface;
    }

    #prompt-input {
        height: auto;
        min-height: 1;
    }

    /* Terminal panel */
    #terminal-panel {
        height: 15;
        background: $panel;
        border-top: solid $border;
        display: none;
    }

    #terminal-panel.visible {
        display: block;
    }

    /* Diff panel */
    #diff-panel {
        width: 50%;
        background: $panel;
        border-left: solid $border;
        display: none;
    }

    #diff-panel.visible {
        display: block;
    }

    /* Status indicators */
    .status-message {
        text-align: center;
        color: $text-muted;
        padding: 1;
    }

    .rlm-indicator {
        color: $success;
    }

    .rlm-archiving {
        color: $warning;
    }

    /* Model/Agent indicator */
    .model-indicator {
        color: $text-muted;
        padding: 0 1;
    }

    .agent-indicator {
        color: $accent;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+p", "command_palette", "Commands", show=True),
        Binding("ctrl+n", "new_session", "New Session"),
        Binding("ctrl+b", "toggle_sidebar", "Sidebar"),
        Binding("ctrl+e", "toggle_explorer", "Explorer"),
        Binding("ctrl+`", "toggle_terminal", "Terminal"),
        Binding("ctrl+d", "toggle_diff", "Diff"),
        Binding("ctrl+k", "show_context", "Context"),
        Binding("ctrl+m", "select_model", "Model"),
        Binding("ctrl+a", "select_agent", "Agent"),
        Binding("ctrl+,", "open_settings", "Settings"),
        Binding("ctrl+t", "select_theme", "Theme"),
        Binding("escape", "interrupt", "Stop"),
        Binding("f1", "show_help", "Help"),
    ]

    def __init__(
        self,
        working_directory: Path | None = None,
        session_id: str | None = None,
        model: str | None = None,
        agent: str | None = None,
    ) -> None:
        super().__init__()

        self.working_directory = working_directory or Path.cwd()
        self.initial_session_id = session_id
        self.current_model = model
        self.current_agent = agent or "build"

        # Load configuration
        self.config = load_config(self.working_directory)

        # Initialize managers
        self.theme_manager = get_theme_manager()
        self.keybind_manager = get_keybind_manager()
        self.event_bus = get_event_bus()
        self.storage = get_storage()
        self.rlm_handler = get_rlm_handler()

        # Session state
        self.session: Session | None = None
        self.sessions: list[Session] = []
        self.messages: list[Message] = []
        self.is_generating = False
        self.current_worker: Worker | None = None

        # Panel state
        self.sidebar_visible = True
        self.explorer_visible = False
        self.terminal_visible = False
        self.diff_visible = False

        # Diff state
        self.current_diffs: list[FileDiff] = []

        # Apply theme
        if self.config.theme:
            self.theme_manager.set_theme(self.config.theme)

        # Set default model from config
        if not self.current_model:
            self.current_model = self.config.model

    def compose(self) -> ComposeResult:
        """Compose the main UI layout."""
        # Header with session tabs
        with Horizontal(id="header-bar"):
            yield Static("🐙 PinkyClawd", classes="app-title")
            yield SessionTabBar(
                tabs=[],
                id="session-tabs",
            )
            yield Static(f"@{self.current_agent}", classes="agent-indicator", id="agent-display")
            yield Static(self.current_model or "No model", classes="model-indicator", id="model-display")

        # Main content
        with Horizontal(id="main-layout"):
            # Sidebar
            with Vertical(id="sidebar-panel"):
                yield Sidebar(
                    sessions=self.sessions,
                    id="sidebar",
                )

            # Explorer panel
            with Vertical(id="explorer-panel"):
                yield FileTreePanel(
                    root=self.working_directory,
                    id="file-tree",
                )

            # Content area
            with Vertical(id="content-area"):
                # Main content with optional diff panel
                with Horizontal(id="content-row"):
                    # Messages
                    with Vertical(id="messages-column"):
                        yield MessageList(id="messages")

                        # Context bar
                        yield ContextBar(
                            tokens_used=0,
                            token_limit=200000,
                            id="context-bar",
                        )

                        # Prompt
                        with Container(id="prompt-container"):
                            yield PromptInput(
                                placeholder="Type your message... (Enter to send, Shift+Enter for newline)",
                                id="prompt-input",
                            )

                    # Diff panel
                    with Vertical(id="diff-panel"):
                        yield DiffPanel(id="diff-view")

                # Terminal panel
                with Vertical(id="terminal-panel"):
                    yield TerminalPanel(
                        working_directory=str(self.working_directory),
                        id="terminal",
                    )

        yield Footer()

    async def on_mount(self) -> None:
        """Handle app mount."""
        self.title = f"PinkyClawd - {self.working_directory.name}"

        # Register RLM event handlers
        register_event_handlers()

        # Set up event handlers
        self.event_bus.subscribe(self._handle_event)

        # Load sessions
        self.sessions = self.storage.list_sessions()

        # Initialize or load session
        await self._init_session()

        # Update sidebar
        self._update_sidebar()

        # Focus the prompt
        self.query_one("#prompt-input", PromptInput).focus()

    async def _init_session(self) -> None:
        """Initialize or load session."""
        if self.initial_session_id:
            # Load existing session
            self.session = self.storage.get_session(self.initial_session_id)
            if self.session:
                self.messages = self.storage.get_messages(self.session.id)
                self._refresh_messages()
                self.notify(f"Loaded session: {self.session.title}")
            else:
                self.notify(f"Session not found: {self.initial_session_id}", severity="error")

        if not self.session:
            # Create new session
            await self._create_session()

        # Update session tabs
        self._update_session_tabs()

    async def _create_session(self) -> None:
        """Create a new session."""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        self.session = Session(
            id=session_id,
            title="New Conversation",
            directory=str(self.working_directory),
        )
        self.storage.create_session(self.session)
        self.sessions.append(self.session)
        self.messages = []
        self._refresh_messages()
        self._update_session_tabs()
        self.notify("Created new session")

    def _handle_event(self, event: Event) -> None:
        """Handle events from the event bus."""
        if event.type == EventType.THEME_CHANGED:
            self._apply_theme()
        elif event.type == EventType.RLM_ARCHIVE_STARTED:
            self.notify("Archiving context...", severity="warning")
        elif event.type == EventType.RLM_ARCHIVE_COMPLETED:
            tokens = event.data.get("tokens_archived", 0)
            self.notify(f"Archived {tokens:,} tokens")
            self._update_context_bar()
        elif event.type == EventType.RLM_CONTEXT_RETRIEVED:
            blocks = event.data.get("block_count", 0)
            if blocks > 0:
                self.notify(f"Retrieved {blocks} context blocks")

    def _apply_theme(self) -> None:
        """Apply the current theme."""
        theme = get_current_theme()
        # Theme CSS variables would be updated here

    def _refresh_messages(self) -> None:
        """Refresh the message display."""
        message_list = self.query_one("#messages", MessageList)
        message_list.clear_messages()
        for msg in self.messages:
            message_list.add_message(msg)

    def _update_context_bar(self) -> None:
        """Update the context bar with current token usage."""
        if not self.session:
            return

        state = self.rlm_handler.get_context_state(self.session.id)
        context_bar = self.query_one("#context-bar", ContextBar)
        context_bar.update(
            tokens_used=state.total_tokens,
            token_limit=state.model_limit,
        )

    def _update_sidebar(self) -> None:
        """Update the sidebar with session list."""
        try:
            sidebar = self.query_one("#sidebar", Sidebar)
            sidebar.update_sessions(self.sessions)
            if self.session:
                sidebar.set_current_session(self.session)
        except Exception:
            pass

    def _update_session_tabs(self) -> None:
        """Update the session tab bar."""
        try:
            tab_bar = self.query_one("#session-tabs", SessionTabBar)
            tabs = [
                SessionTabInfo(
                    id=s.id,
                    title=s.title or "Untitled",
                    is_active=(self.session and s.id == self.session.id),
                    message_count=len(self.storage.get_messages(s.id)),
                    model=self.current_model,
                )
                for s in self.sessions[:8]
            ]
            tab_bar.set_tabs(tabs)
        except Exception:
            pass

    # Event handlers

    async def on_prompt_input_submitted(self, event: PromptInput.Submitted) -> None:
        """Handle prompt submission."""
        if self.is_generating:
            self.notify("Already generating...", severity="warning")
            return

        user_input = event.value.strip()
        if not user_input:
            return

        # Handle slash commands
        if user_input.startswith("/"):
            await self._handle_command(user_input)
            return

        # Process the message
        await self._process_message(user_input)

    async def _handle_command(self, command: str) -> None:
        """Handle slash commands."""
        cmd = command.lower().strip()
        args = cmd.split(" ", 1)
        cmd_name = args[0]
        cmd_args = args[1] if len(args) > 1 else ""

        commands = {
            "/quit": lambda: self.action_quit(),
            "/exit": lambda: self.action_quit(),
            "/new": lambda: self.run_worker(self._create_session()),
            "/context": lambda: self.action_show_context(),
            "/compact": lambda: self.run_worker(self._compact_context()),
            "/clear": lambda: self._clear_messages(),
            "/model": lambda: self.action_select_model(),
            "/agent": lambda: self.action_select_agent(),
            "/theme": lambda: self.action_select_theme(),
            "/settings": lambda: self.action_open_settings(),
            "/sidebar": lambda: self.action_toggle_sidebar(),
            "/explorer": lambda: self.action_toggle_explorer(),
            "/terminal": lambda: self.action_toggle_terminal(),
            "/diff": lambda: self.action_toggle_diff(),
            "/help": lambda: self.action_show_help(),
        }

        handler = commands.get(cmd_name)
        if handler:
            handler()
        else:
            self.notify(f"Unknown command: {cmd_name}", severity="error")

    def _clear_messages(self) -> None:
        """Clear messages."""
        self.messages = []
        self._refresh_messages()
        self.notify("Messages cleared")

    async def _process_message(self, user_input: str) -> None:
        """Process a user message with RLM integration."""
        if not self.session:
            return

        self.is_generating = True

        try:
            # 1. Create user message
            user_message = self._create_message(MessageRole.USER, user_input)
            self.messages.append(user_message)
            self.storage.add_message(user_message)

            # Add to display
            message_list = self.query_one("#messages", MessageList)
            message_list.add_message(user_message)

            # 2. RLM: Prepare messages with context injection
            augmented_messages, rlm_context = prepare_messages_with_rlm(
                session_id=self.session.id,
                user_query=user_input,
                messages=self.messages,
                model=self.current_model,
            )

            if rlm_context.has_retrieved_context:
                self.notify(f"Injected {len(rlm_context.retrieved_context.blocks)} context blocks")

            # 3. Create placeholder for assistant response
            assistant_message = self._create_message(MessageRole.ASSISTANT, "")
            self.messages.append(assistant_message)
            message_list.add_message(assistant_message)

            # 4. Stream response from provider
            self.current_worker = self.run_worker(
                self._stream_response(augmented_messages, assistant_message),
                exclusive=True,
            )

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            self.is_generating = False

    async def _stream_response(
        self,
        messages: list[Message],
        assistant_message: Message,
    ) -> None:
        """Stream response from provider."""
        try:
            provider = get_provider(self.current_model)
            full_response = ""

            async for chunk in provider.stream(
                messages=messages,
                model=self.current_model,
            ):
                if chunk.type == "text" and chunk.text:
                    full_response += chunk.text

                    # Update message content
                    if assistant_message.parts:
                        assistant_message.parts[0].content["text"] = full_response

                    # Update display
                    message_list = self.query_one("#messages", MessageList)
                    message_list.update_last_message(full_response)

                elif chunk.type == "done":
                    break

            # 5. Save final message
            if assistant_message.parts:
                assistant_message.parts[0].content["text"] = full_response
            self.storage.add_message(assistant_message)

            # 6. RLM: Update state after response
            context_state = update_after_response(
                session_id=self.session.id,
                assistant_message=assistant_message,
                model=self.current_model,
            )

            # 7. Update context bar
            self._update_context_bar()

            # 8. Check for task completion
            user_text = ""
            for msg in reversed(self.messages):
                if msg.role == MessageRole.USER:
                    for part in msg.parts:
                        if part.type == PartType.TEXT:
                            user_text = part.content.get("text", "")
                            break
                    break

            if detect_task_completion(user_text):
                self.rlm_handler.check_completion_and_archive(
                    message=user_text,
                    session_id=self.session.id,
                    messages=self.messages[-10:],
                )

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

        finally:
            self.is_generating = False

    async def _compact_context(self) -> None:
        """Force context compaction."""
        if not self.session:
            return

        if self.rlm_handler.force_compact(self.session.id):
            self.notify("Context compacted")
            self._update_context_bar()
        else:
            self.notify("Nothing to compact")

    def _create_message(self, role: MessageRole, text: str) -> Message:
        """Create a new message."""
        msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        return Message(
            id=msg_id,
            session_id=self.session.id if self.session else "",
            role=role,
            parts=[
                MessagePart(
                    id=f"part_{uuid.uuid4().hex[:8]}",
                    message_id=msg_id,
                    type=PartType.TEXT,
                    content={"text": text},
                )
            ],
            created_at=datetime.now(),
        )

    # Session tab handlers

    def on_session_tab_bar_tab_selected(self, event: SessionTabBar.TabSelected) -> None:
        """Handle session tab selection."""
        for session in self.sessions:
            if session.id == event.session_id:
                self.session = session
                self.messages = self.storage.get_messages(session.id)
                self._refresh_messages()
                self._update_session_tabs()
                self._update_sidebar()
                self._update_context_bar()
                break

    def on_session_tab_bar_tab_closed(self, event: SessionTabBar.TabClosed) -> None:
        """Handle session tab close."""
        # Remove session from list
        self.sessions = [s for s in self.sessions if s.id != event.session_id]

        # If closing current session, switch to another
        if self.session and self.session.id == event.session_id:
            if self.sessions:
                self.session = self.sessions[0]
                self.messages = self.storage.get_messages(self.session.id)
                self._refresh_messages()
            else:
                self.run_worker(self._create_session())

        self._update_session_tabs()
        self._update_sidebar()

    def on_session_tab_bar_new_tab_requested(self, event: SessionTabBar.NewTabRequested) -> None:
        """Handle new tab request."""
        self.run_worker(self._create_session())

    # Sidebar handlers

    def on_sidebar_session_selected(self, event: Sidebar.SessionSelected) -> None:
        """Handle sidebar session selection."""
        for session in self.sessions:
            if session.id == event.session_id:
                self.session = session
                self.messages = self.storage.get_messages(session.id)
                self._refresh_messages()
                self._update_session_tabs()
                self._update_sidebar()
                self._update_context_bar()
                break

    # File tree handlers

    def on_file_tree_file_selected(self, event) -> None:
        """Handle file selection in tree."""
        # Could open file preview or add to context
        pass

    # Actions

    def action_quit(self) -> None:
        """Quit the application."""
        if self.session and self.messages:
            self.rlm_handler.archive_on_session_end(self.session.id, self.messages)
        self.exit()

    def action_command_palette(self) -> None:
        """Open the command palette."""
        from pinkyclawd.tui.dialogs.command import CommandPalette, get_default_commands

        async def handle_command(cmd):
            if cmd:
                # Execute the selected command
                if cmd.action:
                    result = cmd.action()
                    if asyncio.iscoroutine(result):
                        await result

        commands = get_default_commands()
        self.push_screen(CommandPalette(commands=commands), handle_command)

    def action_new_session(self) -> None:
        """Create a new session."""
        self.run_worker(self._create_session())

    def action_toggle_sidebar(self) -> None:
        """Toggle the sidebar visibility."""
        sidebar = self.query_one("#sidebar-panel")
        self.sidebar_visible = not self.sidebar_visible
        if self.sidebar_visible:
            sidebar.remove_class("collapsed")
        else:
            sidebar.add_class("collapsed")

    def action_toggle_explorer(self) -> None:
        """Toggle the explorer panel."""
        explorer = self.query_one("#explorer-panel")
        self.explorer_visible = not self.explorer_visible
        if self.explorer_visible:
            explorer.add_class("visible")
        else:
            explorer.remove_class("visible")

    def action_toggle_terminal(self) -> None:
        """Toggle the terminal panel."""
        terminal = self.query_one("#terminal-panel")
        self.terminal_visible = not self.terminal_visible
        if self.terminal_visible:
            terminal.add_class("visible")
        else:
            terminal.remove_class("visible")

    def action_toggle_diff(self) -> None:
        """Toggle the diff panel."""
        diff = self.query_one("#diff-panel")
        self.diff_visible = not self.diff_visible
        if self.diff_visible:
            diff.add_class("visible")
        else:
            diff.remove_class("visible")

    def action_show_context(self) -> None:
        """Show context usage."""
        if not self.session:
            return

        state = self.rlm_handler.get_context_state(self.session.id)
        self.notify(
            f"Context: {state.usage_ratio:.1%} "
            f"({state.total_tokens:,}/{state.model_limit:,} tokens)"
        )

    def action_select_model(self) -> None:
        """Open model selector."""
        from pinkyclawd.tui.dialogs.model import ModelSelector

        def handle_model(model_id):
            if model_id:
                self.current_model = model_id
                try:
                    model_display = self.query_one("#model-display", Static)
                    model_display.update(model_id)
                except Exception:
                    pass
                self.notify(f"Model: {model_id}")

        self.push_screen(ModelSelector(), handle_model)

    def action_select_agent(self) -> None:
        """Open agent selector."""
        from pinkyclawd.tui.dialogs.agent import AgentSelector

        def handle_agent(agent_id):
            if agent_id:
                self.current_agent = agent_id
                try:
                    agent_display = self.query_one("#agent-display", Static)
                    agent_display.update(f"@{agent_id}")
                except Exception:
                    pass
                self.notify(f"Agent: {agent_id}")

        self.push_screen(AgentSelector(), handle_agent)

    def action_select_theme(self) -> None:
        """Open theme selector."""
        from pinkyclawd.tui.dialogs.theme import ThemeSelector

        def handle_theme(theme_name):
            if theme_name:
                self.theme_manager.set_theme(theme_name)
                self.notify(f"Theme: {theme_name}")

        self.push_screen(ThemeSelector(), handle_theme)

    def action_open_settings(self) -> None:
        """Open settings dialog."""
        from pinkyclawd.tui.dialogs.settings import SettingsDialog

        settings = {
            "theme": self.theme_manager.current.name,
            "model": self.current_model,
            "rlm_enabled": self.config.rlm.enabled if hasattr(self.config, 'rlm') else True,
        }

        themes = [(t.name, t.display_name) for t in BUILTIN_THEMES.values()]

        def handle_settings(result):
            if result:
                # Apply settings
                if "theme" in result:
                    self.theme_manager.set_theme(result["theme"])
                self.notify("Settings saved")

        self.push_screen(SettingsDialog(settings=settings, themes=themes), handle_settings)

    def action_show_help(self) -> None:
        """Show help dialog."""
        from pinkyclawd.tui.dialogs.help import HelpDialog

        self.push_screen(HelpDialog())

    def action_interrupt(self) -> None:
        """Interrupt current generation."""
        if self.current_worker and self.is_generating:
            self.current_worker.cancel()
            self.is_generating = False
            self.notify("Generation interrupted")


def run_app(
    working_directory: Path | None = None,
    session_id: str | None = None,
    model: str | None = None,
    agent: str | None = None,
) -> None:
    """Run the PinkyClawd TUI application."""
    app = PinkyClawdApp(
        working_directory=working_directory,
        session_id=session_id,
        model=model,
        agent=agent,
    )
    app.run()
