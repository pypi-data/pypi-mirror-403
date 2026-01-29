"""
Terminal widget for PTY emulation.

Provides terminal functionality similar to OpenCode's Ghostty integration:
- PTY subprocess management
- ANSI escape code handling
- Scrollback buffer
- Resize handling
"""

from __future__ import annotations

import asyncio
import os
import pty
import select
import signal
import struct
import sys
import termios
import fcntl
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static, RichLog, Input
from textual.worker import Worker


@dataclass
class TerminalSize:
    """Terminal dimensions."""

    rows: int = 24
    cols: int = 80


class TerminalOutput(RichLog):
    """Terminal output display with ANSI support."""

    DEFAULT_CSS = """
    TerminalOutput {
        height: 1fr;
        background: $surface;
        color: $text;
        scrollbar-background: $surface;
        scrollbar-color: $primary;
    }
    """

    def __init__(self, max_lines: int = 10000, **kwargs: Any) -> None:
        super().__init__(
            highlight=True,
            markup=False,
            auto_scroll=True,
            max_lines=max_lines,
            **kwargs,
        )


class TerminalInput(Input):
    """Terminal input field."""

    DEFAULT_CSS = """
    TerminalInput {
        dock: bottom;
        height: 1;
        background: $surface;
        border: none;
        padding: 0;
    }

    TerminalInput:focus {
        border: none;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            placeholder="",
            **kwargs,
        )


class Terminal(Vertical):
    """
    Interactive terminal widget with PTY support.

    Features:
    - PTY subprocess management
    - ANSI escape code handling
    - Command history
    - Scrollback buffer
    - Resize handling
    - Shell integration
    """

    BINDINGS = [
        Binding("ctrl+c", "interrupt", "Interrupt"),
        Binding("ctrl+d", "send_eof", "EOF"),
        Binding("ctrl+l", "clear", "Clear"),
        Binding("up", "history_prev", "Previous"),
        Binding("down", "history_next", "Next"),
    ]

    DEFAULT_CSS = """
    Terminal {
        height: 100%;
        width: 100%;
        background: $surface;
        border: solid $border;
    }

    .terminal-header {
        height: 2;
        padding: 0 1;
        background: $primary 20%;
        border-bottom: solid $border;
    }

    .terminal-title {
        text-style: bold;
    }

    .terminal-status {
        color: $text-muted;
    }

    .terminal-body {
        height: 1fr;
        padding: 0;
    }

    .terminal-prompt {
        height: 1;
        background: $surface;
        border-top: solid $border;
    }

    .terminal-prompt-prefix {
        width: auto;
        color: $primary;
        padding-right: 1;
    }
    """

    is_running: reactive[bool] = reactive(False)
    shell: reactive[str] = reactive("")

    class CommandExecuted(Message):
        """Message sent when a command is executed."""

        def __init__(self, command: str) -> None:
            super().__init__()
            self.command = command

    class ProcessExited(Message):
        """Message sent when the process exits."""

        def __init__(self, exit_code: int) -> None:
            super().__init__()
            self.exit_code = exit_code

    def __init__(
        self,
        working_directory: str | None = None,
        shell: str | None = None,
        environment: dict[str, str] | None = None,
        on_output: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.working_directory = working_directory or os.getcwd()
        self.shell = shell or os.environ.get("SHELL", "/bin/bash")
        self.environment = environment or {}
        self._on_output = on_output

        # PTY state
        self._master_fd: int | None = None
        self._slave_fd: int | None = None
        self._pid: int | None = None
        self._reader_task: asyncio.Task | None = None

        # History
        self._history: list[str] = []
        self._history_index: int = 0
        self._stash: str = ""

        # Size
        self._size = TerminalSize()

    def compose(self) -> ComposeResult:
        # Header
        with Horizontal(classes="terminal-header"):
            yield Static(f"Terminal: {self.shell}", classes="terminal-title")
            yield Static("Ready", classes="terminal-status", id="terminal-status")

        # Output area
        with Vertical(classes="terminal-body"):
            yield TerminalOutput(id="terminal-output")

        # Input prompt
        with Horizontal(classes="terminal-prompt"):
            yield Static("$ ", classes="terminal-prompt-prefix")
            yield TerminalInput(id="terminal-input")

    async def on_mount(self) -> None:
        """Start the terminal on mount."""
        self.query_one("#terminal-input", TerminalInput).focus()

    async def start_shell(self) -> None:
        """Start the shell process."""
        if self.is_running:
            return

        try:
            # Create PTY
            self._master_fd, self._slave_fd = pty.openpty()

            # Set non-blocking
            flags = fcntl.fcntl(self._master_fd, fcntl.F_GETFL)
            fcntl.fcntl(self._master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            # Fork process
            self._pid = os.fork()

            if self._pid == 0:
                # Child process
                os.close(self._master_fd)
                os.setsid()

                # Set controlling terminal
                fcntl.ioctl(self._slave_fd, termios.TIOCSCTTY, 0)

                # Redirect stdin/stdout/stderr
                os.dup2(self._slave_fd, 0)
                os.dup2(self._slave_fd, 1)
                os.dup2(self._slave_fd, 2)

                if self._slave_fd > 2:
                    os.close(self._slave_fd)

                # Set environment
                env = os.environ.copy()
                env.update(self.environment)
                env["TERM"] = "xterm-256color"

                # Change directory
                os.chdir(self.working_directory)

                # Execute shell
                os.execvpe(self.shell, [self.shell], env)

            else:
                # Parent process
                os.close(self._slave_fd)
                self._slave_fd = None
                self.is_running = True

                # Update status
                self._update_status("Running")

                # Start reader
                self._reader_task = asyncio.create_task(self._read_output())

        except Exception as e:
            self._write_output(f"Error starting shell: {e}\n")
            self.is_running = False

    async def _read_output(self) -> None:
        """Read output from the PTY."""
        while self.is_running and self._master_fd is not None:
            try:
                # Wait for data
                ready, _, _ = select.select([self._master_fd], [], [], 0.1)

                if ready:
                    data = os.read(self._master_fd, 4096)
                    if data:
                        output = data.decode("utf-8", errors="replace")
                        self._write_output(output)

                        if self._on_output:
                            self._on_output(output)
                    else:
                        # EOF
                        break

                # Check if process is still running
                if self._pid:
                    pid, status = os.waitpid(self._pid, os.WNOHANG)
                    if pid != 0:
                        exit_code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
                        self._write_output(f"\n[Process exited with code {exit_code}]\n")
                        self.post_message(self.ProcessExited(exit_code))
                        break

            except OSError:
                break
            except asyncio.CancelledError:
                break

            await asyncio.sleep(0.01)

        self.is_running = False
        self._update_status("Exited")

    def _write_output(self, text: str) -> None:
        """Write text to the output display."""
        try:
            output = self.query_one("#terminal-output", TerminalOutput)
            output.write(text)
        except Exception:
            pass

    def _update_status(self, status: str) -> None:
        """Update the status display."""
        try:
            status_widget = self.query_one("#terminal-status", Static)
            status_widget.update(status)
        except Exception:
            pass

    def write(self, data: str) -> None:
        """Write data to the PTY."""
        if self._master_fd is not None:
            try:
                os.write(self._master_fd, data.encode("utf-8"))
            except OSError:
                pass

    async def execute_command(self, command: str) -> None:
        """Execute a command in the terminal."""
        if not command.strip():
            return

        # Add to history
        if not self._history or self._history[-1] != command:
            self._history.append(command)
        self._history_index = len(self._history)

        # Show command
        self._write_output(f"$ {command}\n")

        # Send to PTY if running
        if self.is_running and self._master_fd:
            self.write(command + "\n")
        else:
            # Execute directly
            await self._execute_direct(command)

        self.post_message(self.CommandExecuted(command))

    async def _execute_direct(self, command: str) -> None:
        """Execute a command directly without PTY."""
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.working_directory,
            )

            if proc.stdout:
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    self._write_output(line.decode("utf-8", errors="replace"))

            await proc.wait()
            self._write_output(f"[Exit code: {proc.returncode}]\n")

        except Exception as e:
            self._write_output(f"Error: {e}\n")

    async def on_terminal_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        command = event.value.strip()
        event.input.clear()
        await self.execute_command(command)

    def resize(self, rows: int, cols: int) -> None:
        """Resize the PTY."""
        self._size = TerminalSize(rows, cols)

        if self._master_fd is not None:
            try:
                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                fcntl.ioctl(self._master_fd, termios.TIOCSWINSZ, winsize)
            except OSError:
                pass

    def action_interrupt(self) -> None:
        """Send interrupt signal."""
        if self._pid:
            try:
                os.kill(self._pid, signal.SIGINT)
            except OSError:
                pass

    def action_send_eof(self) -> None:
        """Send EOF."""
        self.write("\x04")

    def action_clear(self) -> None:
        """Clear the terminal."""
        try:
            output = self.query_one("#terminal-output", TerminalOutput)
            output.clear()
        except Exception:
            pass

    def action_history_prev(self) -> None:
        """Navigate to previous history entry."""
        if not self._history:
            return

        try:
            input_widget = self.query_one("#terminal-input", TerminalInput)

            if self._history_index == len(self._history):
                self._stash = input_widget.value

            if self._history_index > 0:
                self._history_index -= 1
                input_widget.value = self._history[self._history_index]
                input_widget.cursor_position = len(input_widget.value)
        except Exception:
            pass

    def action_history_next(self) -> None:
        """Navigate to next history entry."""
        try:
            input_widget = self.query_one("#terminal-input", TerminalInput)

            if self._history_index < len(self._history):
                self._history_index += 1

                if self._history_index == len(self._history):
                    input_widget.value = self._stash
                else:
                    input_widget.value = self._history[self._history_index]

                input_widget.cursor_position = len(input_widget.value)
        except Exception:
            pass

    def stop(self) -> None:
        """Stop the terminal process."""
        self.is_running = False

        if self._reader_task:
            self._reader_task.cancel()
            self._reader_task = None

        if self._pid:
            try:
                os.kill(self._pid, signal.SIGTERM)
                os.waitpid(self._pid, 0)
            except OSError:
                pass
            self._pid = None

        if self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except OSError:
                pass
            self._master_fd = None


class TerminalPanel(Vertical):
    """
    Terminal panel with tabs for multiple terminals.

    Features:
    - Multiple terminal tabs
    - New/close terminal
    - Tab switching
    """

    DEFAULT_CSS = """
    TerminalPanel {
        height: 100%;
        width: 100%;
    }

    .terminal-tabs {
        height: 2;
        background: $surface;
        border-bottom: solid $border;
    }

    .terminal-tab {
        padding: 0 2;
        height: 2;
        background: $surface;
        border-right: solid $border;
    }

    .terminal-tab.active {
        background: $primary 30%;
    }

    .terminal-tab:hover {
        background: $primary 20%;
    }

    .terminal-content {
        height: 1fr;
    }
    """

    def __init__(
        self,
        working_directory: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.working_directory = working_directory or os.getcwd()
        self._terminals: list[Terminal] = []
        self._active_index: int = 0

    def compose(self) -> ComposeResult:
        # Tab bar
        with Horizontal(classes="terminal-tabs"):
            yield Static("Terminal 1", classes="terminal-tab active", id="tab-0")
            yield Static("+", classes="terminal-tab", id="new-tab")

        # Terminal content
        with Vertical(classes="terminal-content"):
            terminal = Terminal(
                working_directory=self.working_directory,
                id="terminal-0",
            )
            self._terminals.append(terminal)
            yield terminal

    def new_terminal(self) -> Terminal:
        """Create a new terminal."""
        index = len(self._terminals)
        terminal = Terminal(
            working_directory=self.working_directory,
            id=f"terminal-{index}",
        )
        self._terminals.append(terminal)

        # Add tab
        tabs = self.query_one(".terminal-tabs", Horizontal)
        new_tab = self.query_one("#new-tab", Static)
        tab = Static(f"Terminal {index + 1}", classes="terminal-tab", id=f"tab-{index}")
        tabs.mount(tab, before=new_tab)

        # Switch to new terminal
        self.switch_terminal(index)

        return terminal

    def switch_terminal(self, index: int) -> None:
        """Switch to a terminal by index."""
        if 0 <= index < len(self._terminals):
            # Update active tab
            for i, tab in enumerate(self.query(".terminal-tab")):
                if tab.id == f"tab-{i}":
                    if i == index:
                        tab.add_class("active")
                    else:
                        tab.remove_class("active")

            # Show/hide terminals
            for i, terminal in enumerate(self._terminals):
                terminal.display = (i == index)

            self._active_index = index

    def close_terminal(self, index: int) -> None:
        """Close a terminal by index."""
        if 0 <= index < len(self._terminals) and len(self._terminals) > 1:
            terminal = self._terminals[index]
            terminal.stop()
            terminal.remove()
            self._terminals.pop(index)

            # Remove tab
            tab = self.query_one(f"#tab-{index}", Static)
            tab.remove()

            # Switch to another terminal
            if self._active_index >= len(self._terminals):
                self._active_index = len(self._terminals) - 1
            self.switch_terminal(self._active_index)

    @property
    def active_terminal(self) -> Terminal | None:
        """Get the active terminal."""
        if 0 <= self._active_index < len(self._terminals):
            return self._terminals[self._active_index]
        return None
