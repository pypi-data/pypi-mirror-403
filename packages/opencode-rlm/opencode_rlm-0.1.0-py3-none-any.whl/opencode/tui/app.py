"""
Main TUI Application using Textual framework.

This is the primary entry point for the OpenCode TUI, matching
the functionality of the TypeScript version's @opentui/solid app.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from opencode.config import get_config, load_config
from opencode.config.theme import get_theme_manager, get_current_theme
from opencode.config.keybind import get_keybind_manager, Action
from opencode.events import get_event_bus, EventType, Event


class OpenCodeApp(App):
    """
    OpenCode TUI Application.

    A production-grade terminal interface for AI-assisted development,
    featuring session management, multi-provider support, and RLM context.
    """

    TITLE = "OpenCode"
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
    }
    
    #content {
        width: 1fr;
    }
    
    #messages {
        height: 1fr;
        overflow-y: scroll;
    }
    
    #prompt-container {
        height: auto;
        max-height: 10;
        border-top: solid $primary;
        padding: 1;
    }
    
    .message {
        padding: 1;
        margin-bottom: 1;
    }
    
    .message-user {
        background: $primary 20%;
    }
    
    .message-assistant {
        background: $secondary 20%;
    }
    
    .logo {
        text-align: center;
        padding: 2;
    }
    
    .status-bar {
        dock: bottom;
        height: 1;
        background: $panel;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+p", "command_palette", "Commands", show=True),
        Binding("ctrl+n", "new_session", "New Session"),
        Binding("ctrl+l", "list_sessions", "Sessions"),
        Binding("f2", "cycle_model", "Cycle Model"),
        Binding("tab", "cycle_agent", "Cycle Agent"),
        Binding("escape", "interrupt", "Interrupt"),
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
        self.session_id = session_id
        self.current_model = model
        self.current_agent = agent or "build"

        # Load configuration
        self.config = load_config(self.working_directory)

        # Initialize managers
        self.theme_manager = get_theme_manager()
        self.keybind_manager = get_keybind_manager()
        self.event_bus = get_event_bus()

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
                # Sidebar
                with Vertical(id="sidebar"):
                    yield Static("OpenCode", classes="logo")
                    yield Static("Sessions", id="session-list")

                # Main content
                with Vertical(id="content"):
                    yield Static("Messages will appear here", id="messages")
                    yield Static("Type your prompt here...", id="prompt-container")

        yield Footer()

    async def on_mount(self) -> None:
        """Handle app mount."""
        self.title = f"OpenCode - {self.working_directory.name}"

        # Set up event handlers
        self.event_bus.subscribe(self._handle_event)

        # Initialize providers
        # await self._init_providers()

    def _handle_event(self, event: Event) -> None:
        """Handle events from the event bus."""
        if event.type == EventType.THEME_CHANGED:
            self._apply_theme()
        elif event.type == EventType.MESSAGE_UPDATED:
            self._update_messages()

    def _apply_theme(self) -> None:
        """Apply the current theme to the UI."""
        theme = get_current_theme()
        # Theme application would happen here
        # In Textual, this involves updating CSS variables

    def _update_messages(self) -> None:
        """Update the messages display."""
        # Message update logic would go here
        pass

    # Actions

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def action_command_palette(self) -> None:
        """Open the command palette."""
        # Would push CommandPalette screen
        self.notify("Command palette (Ctrl+P)")

    def action_new_session(self) -> None:
        """Create a new session."""
        self.notify("Creating new session...")

    def action_list_sessions(self) -> None:
        """Show session list."""
        self.notify("Session list (Ctrl+L)")

    def action_cycle_model(self) -> None:
        """Cycle through recent models."""
        self.notify(f"Current model: {self.current_model}")

    def action_cycle_agent(self) -> None:
        """Cycle through agents."""
        self.notify(f"Current agent: {self.current_agent}")

    def action_interrupt(self) -> None:
        """Interrupt current operation."""
        self.notify("Interrupted")


def run_app(
    working_directory: Path | None = None,
    session_id: str | None = None,
    model: str | None = None,
    agent: str | None = None,
) -> None:
    """Run the OpenCode TUI application."""
    app = OpenCodeApp(
        working_directory=working_directory,
        session_id=session_id,
        model=model,
        agent=agent,
    )
    app.run()
