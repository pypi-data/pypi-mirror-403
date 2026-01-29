"""
Prompt input widget with autocomplete and history.

Matches opencode's Prompt component with multi-line support,
file/command autocomplete, and history navigation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Any

from textual.widgets import TextArea
from textual.message import Message
from textual.binding import Binding


class PromptInput(TextArea):
    """
    Multi-line prompt input with autocomplete.

    Features:
    - Multi-line text input
    - File/command autocomplete
    - History navigation (up/down)
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
    ]

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
        history: list[str] | None = None,
        on_submit: Callable[[str], Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.placeholder_text = placeholder
        self.history = history or []
        self.history_index = len(self.history)
        self.stash = ""  # Stashed input when navigating history
        self.on_submit_callback = on_submit

    def on_mount(self) -> None:
        """Set up the widget."""
        self.focus()

    def action_submit(self) -> None:
        """Submit the prompt."""
        value = self.text.strip()
        if not value:
            return

        # Add to history
        if not self.history or self.history[-1] != value:
            self.history.append(value)
        self.history_index = len(self.history)

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
        if not self.history:
            return

        # Stash current input if at end
        if self.history_index == len(self.history):
            self.stash = self.text

        if self.history_index > 0:
            self.history_index -= 1
            self.text = self.history[self.history_index]
            self.move_cursor_to_end()

        self.post_message(self.HistoryNavigated(-1))

    def action_history_next(self) -> None:
        """Navigate to next history entry."""
        if self.history_index < len(self.history):
            self.history_index += 1

            if self.history_index == len(self.history):
                self.text = self.stash
            else:
                self.text = self.history[self.history_index]

            self.move_cursor_to_end()

        self.post_message(self.HistoryNavigated(1))

    def action_autocomplete(self) -> None:
        """Trigger autocomplete."""
        # Get current word
        text = self.text
        cursor = self.cursor_location

        # Find word start
        line = text.split("\n")[cursor[0]] if text else ""
        word_start = cursor[1]
        while word_start > 0 and line[word_start - 1] not in " \t":
            word_start -= 1

        prefix = line[word_start : cursor[1]]

        # Check for file completion
        if "/" in prefix or prefix.startswith("."):
            self._complete_file(prefix)
        elif prefix.startswith("@"):
            self._complete_agent(prefix[1:])
        elif prefix.startswith("/"):
            self._complete_command(prefix[1:])

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
        agents = ["build", "plan", "explore", "general"]
        matches = [a for a in agents if a.startswith(prefix)]
        if len(matches) == 1:
            self._insert_completion("@" + prefix, "@" + matches[0])

    def _complete_command(self, prefix: str) -> None:
        """Complete slash command."""
        commands = ["help", "models", "agents", "session", "clear", "export"]
        matches = [c for c in commands if c.startswith(prefix)]
        if len(matches) == 1:
            self._insert_completion("/" + prefix, "/" + matches[0])

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
            lines[cursor[0]] = line[:idx] + new + line[cursor[1] :]
            self.text = "\n".join(lines)
            # Move cursor to end of completion
            new_col = idx + len(new)
            self.move_cursor((cursor[0], new_col))

    def move_cursor_to_end(self) -> None:
        """Move cursor to end of text."""
        lines = self.text.split("\n")
        if lines:
            self.move_cursor((len(lines) - 1, len(lines[-1])))
