"""
TUI dialog components for OpenCode.

Provides modal dialogs for command palette, model selection,
agent selection, session management, and theme selection.
"""

from opencode.tui.dialogs.command import CommandPalette
from opencode.tui.dialogs.model import ModelSelector
from opencode.tui.dialogs.agent import AgentSelector
from opencode.tui.dialogs.session import SessionDialog
from opencode.tui.dialogs.theme import ThemeSelector

__all__ = [
    "CommandPalette",
    "ModelSelector",
    "AgentSelector",
    "SessionDialog",
    "ThemeSelector",
]
