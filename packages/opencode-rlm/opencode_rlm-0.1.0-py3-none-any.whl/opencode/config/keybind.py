"""
Keybinding system for OpenCode TUI.

Supports leader key patterns and configurable bindings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Any
import re


class Action(Enum):
    """All available actions that can be bound to keys."""

    # Application
    QUIT = auto()
    HELP = auto()
    COMMAND_PALETTE = auto()

    # Session
    NEW_SESSION = auto()
    LIST_SESSIONS = auto()
    EXPORT_SESSION = auto()
    FORK_SESSION = auto()
    RENAME_SESSION = auto()
    DELETE_SESSION = auto()
    SHARE_SESSION = auto()
    INTERRUPT = auto()
    COMPACT_SESSION = auto()

    # Navigation
    SCROLL_UP = auto()
    SCROLL_DOWN = auto()
    PAGE_UP = auto()
    PAGE_DOWN = auto()
    SCROLL_TOP = auto()
    SCROLL_BOTTOM = auto()
    NEXT_MESSAGE = auto()
    PREV_MESSAGE = auto()

    # Model/Agent
    LIST_MODELS = auto()
    LIST_AGENTS = auto()
    CYCLE_MODEL = auto()
    CYCLE_MODEL_REVERSE = auto()
    CYCLE_AGENT = auto()
    CYCLE_AGENT_REVERSE = auto()
    CYCLE_VARIANT = auto()
    TOGGLE_FAVORITE = auto()

    # UI
    TOGGLE_SIDEBAR = auto()
    LIST_THEMES = auto()
    VIEW_STATUS = auto()
    COPY_MESSAGE = auto()
    TOGGLE_CODE_CONCEALMENT = auto()

    # Editing
    UNDO_MESSAGE = auto()
    REDO_MESSAGE = auto()
    OPEN_EDITOR = auto()

    # Input
    SUBMIT = auto()
    NEWLINE = auto()
    CLEAR_INPUT = auto()
    HISTORY_PREV = auto()
    HISTORY_NEXT = auto()


@dataclass
class KeyBinding:
    """A single key binding."""

    key: str
    action: Action
    description: str = ""
    when: str | None = None  # Context condition


@dataclass
class KeySequence:
    """Parsed key sequence."""

    modifiers: set[str] = field(default_factory=set)
    key: str = ""
    is_leader: bool = False

    def __str__(self) -> str:
        parts = []
        if self.is_leader:
            parts.append("<leader>")
        parts.extend(sorted(self.modifiers))
        parts.append(self.key)
        return "+".join(parts)


def parse_key(key_str: str) -> KeySequence:
    """Parse a key string into a KeySequence."""
    seq = KeySequence()

    # Handle leader key
    if key_str.startswith("<leader>"):
        seq.is_leader = True
        key_str = key_str[8:]  # Remove <leader>
        if key_str.startswith("+"):
            key_str = key_str[1:]

    # Split by + and identify modifiers
    parts = key_str.lower().split("+")
    modifiers = {"ctrl", "alt", "shift", "meta", "cmd"}

    for part in parts:
        if part in modifiers:
            seq.modifiers.add(part)
        else:
            seq.key = part

    return seq


# Default keybindings matching opencode
DEFAULT_BINDINGS: list[KeyBinding] = [
    # Application
    KeyBinding("ctrl+c", Action.QUIT, "Exit application"),
    KeyBinding("ctrl+d", Action.QUIT, "Exit application"),
    KeyBinding("<leader>q", Action.QUIT, "Exit application"),
    KeyBinding("ctrl+p", Action.COMMAND_PALETTE, "Open command palette"),
    KeyBinding("<leader>?", Action.HELP, "Show help"),
    # Session
    KeyBinding("<leader>n", Action.NEW_SESSION, "New session"),
    KeyBinding("<leader>l", Action.LIST_SESSIONS, "List sessions"),
    KeyBinding("<leader>x", Action.EXPORT_SESSION, "Export session"),
    KeyBinding("ctrl+r", Action.RENAME_SESSION, "Rename session"),
    KeyBinding("escape", Action.INTERRUPT, "Interrupt session"),
    KeyBinding("<leader>c", Action.COMPACT_SESSION, "Compact session"),
    # Navigation
    KeyBinding("ctrl+alt+y", Action.SCROLL_UP, "Scroll up one line"),
    KeyBinding("ctrl+alt+e", Action.SCROLL_DOWN, "Scroll down one line"),
    KeyBinding("pageup", Action.PAGE_UP, "Page up"),
    KeyBinding("ctrl+alt+b", Action.PAGE_UP, "Page up"),
    KeyBinding("pagedown", Action.PAGE_DOWN, "Page down"),
    KeyBinding("ctrl+alt+f", Action.PAGE_DOWN, "Page down"),
    KeyBinding("ctrl+g", Action.SCROLL_TOP, "Go to first message"),
    KeyBinding("home", Action.SCROLL_TOP, "Go to first message"),
    KeyBinding("ctrl+alt+g", Action.SCROLL_BOTTOM, "Go to last message"),
    KeyBinding("end", Action.SCROLL_BOTTOM, "Go to last message"),
    # Model/Agent
    KeyBinding("<leader>m", Action.LIST_MODELS, "List models"),
    KeyBinding("f2", Action.CYCLE_MODEL, "Cycle recent models"),
    KeyBinding("shift+f2", Action.CYCLE_MODEL_REVERSE, "Cycle recent models reverse"),
    KeyBinding("<leader>a", Action.LIST_AGENTS, "List agents"),
    KeyBinding("tab", Action.CYCLE_AGENT, "Cycle agent"),
    KeyBinding("shift+tab", Action.CYCLE_AGENT_REVERSE, "Cycle agent reverse"),
    KeyBinding("ctrl+t", Action.CYCLE_VARIANT, "Cycle model variants"),
    KeyBinding("ctrl+f", Action.TOGGLE_FAVORITE, "Toggle model favorite"),
    # UI
    KeyBinding("<leader>b", Action.TOGGLE_SIDEBAR, "Toggle sidebar"),
    KeyBinding("<leader>t", Action.LIST_THEMES, "List themes"),
    KeyBinding("<leader>s", Action.VIEW_STATUS, "View status"),
    KeyBinding("<leader>y", Action.COPY_MESSAGE, "Copy message"),
    KeyBinding("<leader>h", Action.TOGGLE_CODE_CONCEALMENT, "Toggle code concealment"),
    # Editing
    KeyBinding("<leader>u", Action.UNDO_MESSAGE, "Undo message"),
    KeyBinding("<leader>r", Action.REDO_MESSAGE, "Redo message"),
    KeyBinding("<leader>e", Action.OPEN_EDITOR, "Open external editor"),
    # Input
    KeyBinding("return", Action.SUBMIT, "Submit prompt"),
    KeyBinding("shift+return", Action.NEWLINE, "Insert newline"),
    KeyBinding("ctrl+return", Action.NEWLINE, "Insert newline"),
    KeyBinding("alt+return", Action.NEWLINE, "Insert newline"),
    KeyBinding("ctrl+j", Action.NEWLINE, "Insert newline"),
    KeyBinding("up", Action.HISTORY_PREV, "Previous in history"),
    KeyBinding("down", Action.HISTORY_NEXT, "Next in history"),
]


class KeybindManager:
    """Manages keybindings and dispatches actions."""

    def __init__(self, leader: str = "ctrl+x") -> None:
        self.leader = leader
        self._bindings: dict[str, KeyBinding] = {}
        self._handlers: dict[Action, list[Callable[[], Any]]] = {}
        self._leader_pending = False

        # Load default bindings
        for binding in DEFAULT_BINDINGS:
            self.register(binding)

    def register(self, binding: KeyBinding) -> None:
        """Register a key binding."""
        self._bindings[binding.key.lower()] = binding

    def unregister(self, key: str) -> None:
        """Unregister a key binding."""
        self._bindings.pop(key.lower(), None)

    def on(self, action: Action, handler: Callable[[], Any]) -> Callable[[], None]:
        """Register an action handler."""
        if action not in self._handlers:
            self._handlers[action] = []
        self._handlers[action].append(handler)

        def unsubscribe() -> None:
            self._handlers[action].remove(handler)

        return unsubscribe

    def handle_key(self, key: str) -> bool:
        """
        Handle a key press.

        Returns True if the key was handled.
        """
        key = key.lower()

        # Check for leader key
        if key == self.leader:
            self._leader_pending = True
            return True

        # Check for leader + key combo
        if self._leader_pending:
            self._leader_pending = False
            leader_key = f"<leader>{key}"
            if leader_key in self._bindings:
                self._dispatch(self._bindings[leader_key].action)
                return True

        # Check for direct binding
        if key in self._bindings:
            self._dispatch(self._bindings[key].action)
            return True

        return False

    def _dispatch(self, action: Action) -> None:
        """Dispatch an action to all handlers."""
        for handler in self._handlers.get(action, []):
            try:
                handler()
            except Exception:
                pass  # Log error

    def get_bindings_for_action(self, action: Action) -> list[KeyBinding]:
        """Get all bindings for an action."""
        return [b for b in self._bindings.values() if b.action == action]

    def get_all_bindings(self) -> list[KeyBinding]:
        """Get all registered bindings."""
        return list(self._bindings.values())

    def format_key(self, key: str) -> str:
        """Format a key for display."""
        key = key.replace("<leader>", f"{self.leader} ")
        key = key.replace("ctrl+", "^")
        key = key.replace("alt+", "M-")
        key = key.replace("shift+", "S-")
        return key


# Global keybind manager
_keybind_manager: KeybindManager | None = None


def get_keybind_manager() -> KeybindManager:
    """Get the global keybind manager."""
    global _keybind_manager
    if _keybind_manager is None:
        _keybind_manager = KeybindManager()
    return _keybind_manager
