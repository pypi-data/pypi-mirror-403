"""
Main TUI Application using Textual framework.

This is the primary entry point for the PinkyClawd TUI, with full
RLM integration for unlimited context management.
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
from textual.widgets import Footer, Header, Static
from textual.worker import Worker, get_current_worker

from pinkyclawd.config import get_config, load_config
from pinkyclawd.config.storage import (
    Message,
    MessagePart,
    MessageRole,
    PartType,
    Session,
    get_storage,
)
from pinkyclawd.config.theme import get_theme_manager, get_current_theme
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


class PinkyClawdApp(App):
    """
    PinkyClawd TUI Application with full RLM integration.

    Features:
    - Multi-line prompt input with history
    - Streaming message display
    - Token usage tracking with context bar
    - Session management
    - RLM automatic context archival and retrieval
    """

    TITLE = "PinkyClawd"
    SUB_TITLE = "AI-Powered Development"

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        width: 100%;
        height: 100%;
    }

    #sidebar {
        width: 30;
        background: $panel;
        border-right: solid $primary;
        display: none;
    }

    #sidebar.visible {
        display: block;
    }

    #content {
        width: 1fr;
    }

    #messages {
        height: 1fr;
        overflow-y: scroll;
        padding: 1;
    }

    #context-bar {
        dock: bottom;
        height: 3;
        padding: 0 1;
        background: $panel;
    }

    #prompt-container {
        dock: bottom;
        height: auto;
        min-height: 3;
        max-height: 12;
        border-top: solid $primary;
        padding: 1;
    }

    #prompt-input {
        height: auto;
        min-height: 1;
    }

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
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+p", "command_palette", "Commands", show=True),
        Binding("ctrl+n", "new_session", "New Session"),
        Binding("ctrl+l", "toggle_sidebar", "Sessions"),
        Binding("ctrl+k", "show_context", "Context"),
        Binding("f2", "cycle_model", "Model"),
        Binding("escape", "interrupt", "Stop"),
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
        self.messages: list[Message] = []
        self.is_generating = False
        self.current_worker: Worker | None = None

        # Apply theme
        if self.config.theme:
            self.theme_manager.set_theme(self.config.theme)

        # Set default model from config
        if not self.current_model:
            self.current_model = self.config.model

    def compose(self) -> ComposeResult:
        """Compose the main UI layout."""
        yield Header()

        with Container(id="main-container"):
            with Horizontal():
                # Sidebar (hidden by default)
                with Vertical(id="sidebar"):
                    yield Static("Sessions", classes="sidebar-title")
                    yield Sidebar(id="session-list")

                # Main content
                with Vertical(id="content"):
                    # Messages area
                    yield MessageList(id="messages")

                    # Context bar (RLM token tracking)
                    yield ContextBar(
                        tokens_used=0,
                        token_limit=200000,
                        id="context-bar",
                    )

                    # Prompt input
                    with Container(id="prompt-container"):
                        yield PromptInput(
                            placeholder="Type your message... (Enter to send, Shift+Enter for newline)",
                            id="prompt-input",
                        )

        yield Footer()

    async def on_mount(self) -> None:
        """Handle app mount."""
        self.title = f"PinkyClawd - {self.working_directory.name}"

        # Register RLM event handlers
        register_event_handlers()

        # Set up event handlers
        self.event_bus.subscribe(self._handle_event)

        # Initialize or load session
        await self._init_session()

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

    async def _create_session(self) -> None:
        """Create a new session."""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        self.session = Session(
            id=session_id,
            title="New Conversation",
            directory=str(self.working_directory),
        )
        self.storage.create_session(self.session)
        self.messages = []
        self._refresh_messages()
        self.notify(f"Created new session")

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
        # Theme application would update CSS variables

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

        if cmd in ("/quit", "/exit"):
            self.action_quit()
        elif cmd == "/new":
            await self._create_session()
        elif cmd == "/context":
            self.action_show_context()
        elif cmd == "/compact":
            await self._compact_context()
        elif cmd == "/clear":
            self.messages = []
            self._refresh_messages()
            self.notify("Messages cleared")
        elif cmd.startswith("/model"):
            self.action_cycle_model()
        else:
            self.notify(f"Unknown command: {cmd}", severity="error")

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
            # Get user's last message
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

    # Actions

    def action_quit(self) -> None:
        """Quit the application."""
        # Archive on session end if needed
        if self.session and self.messages:
            self.rlm_handler.archive_on_session_end(self.session.id, self.messages)
        self.exit()

    def action_command_palette(self) -> None:
        """Open the command palette."""
        from pinkyclawd.tui.dialogs.command import CommandPalette

        self.push_screen(CommandPalette())

    def action_new_session(self) -> None:
        """Create a new session."""
        self.run_worker(self._create_session())

    def action_toggle_sidebar(self) -> None:
        """Toggle the sidebar visibility."""
        sidebar = self.query_one("#sidebar")
        sidebar.toggle_class("visible")

    def action_show_context(self) -> None:
        """Show context usage."""
        if not self.session:
            return

        state = self.rlm_handler.get_context_state(self.session.id)
        self.notify(
            f"Context: {state.usage_ratio:.1%} "
            f"({state.total_tokens:,}/{state.model_limit:,} tokens)"
        )

    def action_cycle_model(self) -> None:
        """Cycle through available models."""
        from pinkyclawd.tui.dialogs.model import ModelSelector

        self.push_screen(ModelSelector())

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
