"""
Agent selector dialog.

Allows users to switch between different agents with different capabilities.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Static, ListView, ListItem, Label

from opencode.agent.base import Agent, AgentMode
from opencode.agent.registry import get_agent_registry


class AgentListItem(ListItem):
    """A list item for an agent."""

    def __init__(self, agent: Agent, is_current: bool = False) -> None:
        super().__init__()
        self.agent = agent
        self.is_current = is_current

    def compose(self) -> ComposeResult:
        with Container(classes="agent-item"):
            with Horizontal():
                yield Label(f"{self.agent.icon} " if self.agent.icon else "", classes="agent-icon")
                yield Label(self.agent.name, classes="agent-name")
                if self.is_current:
                    yield Label("(current)", classes="agent-current")
                yield Label(self.agent.mode.value, classes="agent-mode")
            yield Label(self.agent.description, classes="agent-description")


class AgentSelector(ModalScreen[Agent | None]):
    """
    Agent selector modal dialog.

    Shows available agents with their descriptions and capabilities.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select", "Select"),
        Binding("up", "cursor_up", "Up"),
        Binding("down", "cursor_down", "Down"),
    ]

    CSS = """
    AgentSelector {
        align: center middle;
    }

    AgentSelector > Container {
        width: 70;
        max-width: 90%;
        height: auto;
        max-height: 70%;
        background: $surface;
        border: tall $primary;
        padding: 1;
    }

    AgentSelector .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    AgentSelector ListView {
        height: auto;
        max-height: 20;
    }

    .agent-item {
        padding: 0 1;
    }

    .agent-item Horizontal {
        height: 1;
    }

    .agent-icon {
        width: 3;
    }

    .agent-name {
        width: 1fr;
        text-style: bold;
    }

    .agent-current {
        color: $success;
        margin: 0 1;
    }

    .agent-mode {
        width: auto;
        color: $text-muted;
    }

    .agent-description {
        color: $text-muted;
        padding-left: 3;
    }

    AgentSelector ListItem {
        padding: 0;
        height: 3;
    }

    AgentSelector ListItem:hover {
        background: $primary 20%;
    }

    AgentSelector ListItem.-selected {
        background: $primary 40%;
    }

    .permissions-info {
        margin-top: 1;
        padding: 1;
        background: $surface-darken-1;
        border: round $primary 50%;
    }

    .permissions-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .permission-item {
        color: $text-muted;
    }
    """

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name=name)
        self._registry = get_agent_registry()
        self._agents: list[Agent] = []

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Select Agent", classes="title")
            yield ListView(id="agent-list")
            with Container(classes="permissions-info", id="permissions"):
                yield Static("Permissions", classes="permissions-title")
                yield Static("", id="permission-details")

    def on_mount(self) -> None:
        """Populate the agent list."""
        list_view = self.query_one("#agent-list", ListView)

        current = self._registry.get_current()
        self._agents = self._registry.list_primary()

        current_index = 0
        for i, agent in enumerate(self._agents):
            is_current = agent.id == current.id
            if is_current:
                current_index = i
            list_view.append(AgentListItem(agent, is_current))

        list_view.index = current_index
        self._update_permissions(current)

    def _update_permissions(self, agent: Agent) -> None:
        """Update the permissions display for an agent."""
        details = self.query_one("#permission-details", Static)

        perms = agent.permissions
        lines = []

        perm_map = {
            "read": ("Read files", perms.read),
            "write": ("Write files", perms.write),
            "edit": ("Edit files", perms.edit),
            "bash": ("Run commands", perms.bash),
            "webfetch": ("Fetch URLs", perms.webfetch),
        }

        for name, (label, value) in perm_map.items():
            icon = "" if value == "allow" else "" if value == "ask" else ""
            lines.append(f"  {icon} {label}: {value}")

        details.update("\n".join(lines))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Update permissions when selection changes."""
        if isinstance(event.item, AgentListItem):
            self._update_permissions(event.item.agent)

    def action_cancel(self) -> None:
        """Cancel selection."""
        self.dismiss(None)

    def action_select(self) -> None:
        """Select current agent."""
        list_view = self.query_one("#agent-list", ListView)
        if list_view.index is not None and self._agents:
            selected = self._agents[list_view.index]
            self.dismiss(selected)

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        list_view = self.query_one("#agent-list", ListView)
        if list_view.index is not None and list_view.index > 0:
            list_view.index -= 1

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        list_view = self.query_one("#agent-list", ListView)
        if list_view.index is not None:
            if list_view.index < len(self._agents) - 1:
                list_view.index += 1

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection."""
        if isinstance(event.item, AgentListItem):
            self.dismiss(event.item.agent)
