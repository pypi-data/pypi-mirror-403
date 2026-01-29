"""
Session management dialog.

Allows users to view, switch, rename, and delete sessions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Static, ListView, ListItem, Label, Input, Button

from opencode.session.manager import SessionInfo, get_session_manager


class SessionListItem(ListItem):
    """A list item for a session."""

    def __init__(self, session: SessionInfo, is_current: bool = False) -> None:
        super().__init__()
        self.session = session
        self.is_current = is_current

    def compose(self) -> ComposeResult:
        with Container(classes="session-item"):
            with Horizontal():
                yield Label(self.session.title, classes="session-title")
                if self.is_current:
                    yield Label("(current)", classes="session-current")
                yield Label(
                    self._format_time(self.session.updated_at),
                    classes="session-time",
                )
            with Horizontal(classes="session-meta"):
                yield Label(f"{self.session.message_count} messages", classes="session-messages")
                if self.session.is_archived:
                    yield Label("archived", classes="session-archived")

    def _format_time(self, dt: datetime) -> str:
        """Format datetime as relative time."""
        now = datetime.now()
        diff = now - dt

        if diff.days > 7:
            return dt.strftime("%b %d")
        if diff.days > 0:
            return f"{diff.days}d ago"
        if diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        if diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        return "just now"


class SessionDialog(
    ModalScreen[tuple[Literal["switch", "delete", "rename", "fork", "export"], SessionInfo] | None]
):
    """
    Session management modal dialog.

    Shows sessions with options to switch, rename, delete, fork, or export.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "switch", "Switch"),
        Binding("d", "delete", "Delete"),
        Binding("r", "rename", "Rename"),
        Binding("f", "fork", "Fork"),
        Binding("e", "export", "Export"),
        Binding("up", "cursor_up", "Up"),
        Binding("down", "cursor_down", "Down"),
    ]

    CSS = """
    SessionDialog {
        align: center middle;
    }

    SessionDialog > Container {
        width: 80;
        max-width: 90%;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: tall $primary;
        padding: 1;
    }

    SessionDialog .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    SessionDialog ListView {
        height: auto;
        max-height: 20;
    }

    .session-item {
        padding: 0 1;
    }

    .session-item Horizontal {
        height: 1;
    }

    .session-title {
        width: 1fr;
        text-style: bold;
    }

    .session-current {
        color: $success;
        margin: 0 1;
    }

    .session-time {
        width: auto;
        color: $text-muted;
    }

    .session-meta {
        padding-left: 2;
    }

    .session-messages {
        color: $text-muted;
        margin-right: 2;
    }

    .session-archived {
        color: $warning;
    }

    SessionDialog ListItem {
        padding: 0;
        height: 3;
    }

    SessionDialog ListItem:hover {
        background: $primary 20%;
    }

    SessionDialog ListItem.-selected {
        background: $primary 40%;
    }

    .actions {
        margin-top: 1;
        height: 1;
    }

    .actions Label {
        margin-right: 2;
        color: $text-muted;
    }

    .rename-input {
        display: none;
        margin-top: 1;
    }

    .rename-input.visible {
        display: block;
    }
    """

    def __init__(
        self,
        current_session_id: str | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self._manager = get_session_manager()
        self._current_session_id = current_session_id
        self._sessions: list[SessionInfo] = []
        self._rename_mode = False

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Sessions", classes="title")
            yield ListView(id="session-list")
            with Horizontal(classes="actions"):
                yield Label("[Enter] Switch")
                yield Label("[R] Rename")
                yield Label("[F] Fork")
                yield Label("[D] Delete")
                yield Label("[E] Export")
            with Container(classes="rename-input", id="rename-container"):
                yield Input(placeholder="New name...", id="rename-input")

    def on_mount(self) -> None:
        """Populate the session list."""
        self._refresh_list()

    def _refresh_list(self) -> None:
        """Refresh the session list."""
        list_view = self.query_one("#session-list", ListView)
        list_view.clear()

        self._sessions = self._manager.list(limit=50)

        current_index = 0
        for i, session in enumerate(self._sessions):
            is_current = session.id == self._current_session_id
            if is_current:
                current_index = i
            list_view.append(SessionListItem(session, is_current))

        if self._sessions:
            list_view.index = current_index

    def _get_selected(self) -> SessionInfo | None:
        """Get the currently selected session."""
        list_view = self.query_one("#session-list", ListView)
        if list_view.index is not None and self._sessions:
            return self._sessions[list_view.index]
        return None

    def action_cancel(self) -> None:
        """Cancel dialog."""
        if self._rename_mode:
            self._exit_rename_mode()
        else:
            self.dismiss(None)

    def action_switch(self) -> None:
        """Switch to selected session."""
        if self._rename_mode:
            self._confirm_rename()
            return

        selected = self._get_selected()
        if selected:
            self.dismiss(("switch", selected))

    def action_delete(self) -> None:
        """Delete selected session."""
        selected = self._get_selected()
        if selected and selected.id != self._current_session_id:
            self.dismiss(("delete", selected))

    def action_rename(self) -> None:
        """Enter rename mode."""
        selected = self._get_selected()
        if selected:
            self._enter_rename_mode(selected)

    def action_fork(self) -> None:
        """Fork selected session."""
        selected = self._get_selected()
        if selected:
            self.dismiss(("fork", selected))

    def action_export(self) -> None:
        """Export selected session."""
        selected = self._get_selected()
        if selected:
            self.dismiss(("export", selected))

    def _enter_rename_mode(self, session: SessionInfo) -> None:
        """Enter rename mode for a session."""
        self._rename_mode = True
        container = self.query_one("#rename-container")
        container.add_class("visible")

        input_widget = self.query_one("#rename-input", Input)
        input_widget.value = session.title
        input_widget.focus()

    def _exit_rename_mode(self) -> None:
        """Exit rename mode."""
        self._rename_mode = False
        container = self.query_one("#rename-container")
        container.remove_class("visible")

    def _confirm_rename(self) -> None:
        """Confirm the rename."""
        selected = self._get_selected()
        input_widget = self.query_one("#rename-input", Input)
        new_name = input_widget.value.strip()

        if selected and new_name:
            self.dismiss(
                (
                    "rename",
                    SessionInfo(
                        id=selected.id,
                        title=new_name,  # New title
                        directory=selected.directory,
                        message_count=selected.message_count,
                        created_at=selected.created_at,
                        updated_at=selected.updated_at,
                        is_archived=selected.is_archived,
                    ),
                )
            )
        else:
            self._exit_rename_mode()

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        list_view = self.query_one("#session-list", ListView)
        if list_view.index is not None and list_view.index > 0:
            list_view.index -= 1

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        list_view = self.query_one("#session-list", ListView)
        if list_view.index is not None:
            if list_view.index < len(self._sessions) - 1:
                list_view.index += 1

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection."""
        if isinstance(event.item, SessionListItem):
            self.dismiss(("switch", event.item.session))
