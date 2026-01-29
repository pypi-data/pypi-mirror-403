"""
Slash command system for OpenCode.

Provides command registration, parsing, and execution for user-entered
slash commands like /help, /models, /clear, etc.
"""

from opencode.commands.registry import (
    Command,
    CommandArg,
    CommandContext,
    CommandResult,
    CommandRegistry,
    get_command_registry,
    register_command,
    execute_command,
)
from opencode.commands.builtins import register_builtin_commands

__all__ = [
    "Command",
    "CommandArg",
    "CommandContext",
    "CommandResult",
    "CommandRegistry",
    "get_command_registry",
    "register_command",
    "execute_command",
    "register_builtin_commands",
]
