"""
Slash command registry and execution.

Manages registration and execution of user-defined and built-in commands.
"""

from __future__ import annotations

import shlex
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable, Literal

logger = logging.getLogger(__name__)


@dataclass
class CommandArg:
    """Definition of a command argument."""

    name: str
    description: str
    required: bool = False
    type: Literal["string", "integer", "boolean", "path"] = "string"
    default: Any = None
    choices: list[str] | None = None

    def parse(self, value: str) -> Any:
        """Parse a string value to the appropriate type."""
        if self.type == "integer":
            return int(value)
        if self.type == "boolean":
            return value.lower() in ("true", "yes", "1", "on")
        if self.type == "path":
            from pathlib import Path

            return Path(value).expanduser()
        return value


@dataclass
class CommandContext:
    """Context provided to command handlers."""

    session_id: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    raw_input: str = ""


@dataclass
class CommandResult:
    """Result of a command execution."""

    success: bool
    message: str = ""
    data: Any = None
    error: str | None = None

    @classmethod
    def ok(cls, message: str = "", data: Any = None) -> CommandResult:
        return cls(success=True, message=message, data=data)

    @classmethod
    def fail(cls, error: str) -> CommandResult:
        return cls(success=False, error=error)


CommandHandler = (
    Callable[[CommandContext], CommandResult] | Callable[[CommandContext], Awaitable[CommandResult]]
)


@dataclass
class Command:
    """Definition of a slash command."""

    name: str
    description: str
    handler: CommandHandler
    args: list[CommandArg] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    category: str = "General"
    hidden: bool = False

    def get_usage(self) -> str:
        """Get usage string for the command."""
        parts = [f"/{self.name}"]
        for arg in self.args:
            if arg.required:
                parts.append(f"<{arg.name}>")
            else:
                parts.append(f"[{arg.name}]")
        return " ".join(parts)

    def get_help(self) -> str:
        """Get full help text for the command."""
        lines = [
            f"/{self.name} - {self.description}",
            "",
            f"Usage: {self.get_usage()}",
        ]

        if self.args:
            lines.append("")
            lines.append("Arguments:")
            for arg in self.args:
                required = "(required)" if arg.required else "(optional)"
                default = f" [default: {arg.default}]" if arg.default is not None else ""
                lines.append(f"  {arg.name}: {arg.description} {required}{default}")

        if self.aliases:
            lines.append("")
            lines.append(f"Aliases: {', '.join('/' + a for a in self.aliases)}")

        return "\n".join(lines)


class CommandRegistry:
    """
    Registry of available slash commands.

    Manages command registration, lookup, and execution.
    """

    _instance: CommandRegistry | None = None

    def __new__(cls) -> CommandRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._commands: dict[str, Command] = {}
        self._aliases: dict[str, str] = {}
        self._initialized = True

    def register(self, command: Command) -> None:
        """Register a command."""
        self._commands[command.name] = command

        # Register aliases
        for alias in command.aliases:
            self._aliases[alias] = command.name

        logger.debug(f"Registered command: /{command.name}")

    def unregister(self, name: str) -> bool:
        """Unregister a command."""
        if name in self._commands:
            command = self._commands.pop(name)
            for alias in command.aliases:
                self._aliases.pop(alias, None)
            return True
        return False

    def get(self, name: str) -> Command | None:
        """Get a command by name or alias."""
        # Check aliases first
        if name in self._aliases:
            name = self._aliases[name]
        return self._commands.get(name)

    def list(self, include_hidden: bool = False) -> list[Command]:
        """List all registered commands."""
        commands = list(self._commands.values())
        if not include_hidden:
            commands = [c for c in commands if not c.hidden]
        return sorted(commands, key=lambda c: (c.category, c.name))

    def list_by_category(self, include_hidden: bool = False) -> dict[str, list[Command]]:
        """List commands grouped by category."""
        result: dict[str, list[Command]] = {}
        for command in self.list(include_hidden):
            if command.category not in result:
                result[command.category] = []
            result[command.category].append(command)
        return result

    def parse_input(self, input_str: str) -> tuple[str | None, dict[str, Any]]:
        """
        Parse a command input string.

        Args:
            input_str: Raw input like "/help models"

        Returns:
            Tuple of (command_name, parsed_args)
        """
        input_str = input_str.strip()

        if not input_str.startswith("/"):
            return None, {}

        # Parse using shlex for proper quoting
        try:
            parts = shlex.split(input_str[1:])
        except ValueError:
            parts = input_str[1:].split()

        if not parts:
            return None, {}

        command_name = parts[0].lower()
        command = self.get(command_name)

        if not command:
            return command_name, {}

        # Parse arguments
        args: dict[str, Any] = {}
        arg_values = parts[1:]

        for i, arg_def in enumerate(command.args):
            if i < len(arg_values):
                try:
                    args[arg_def.name] = arg_def.parse(arg_values[i])
                except (ValueError, TypeError):
                    args[arg_def.name] = arg_values[i]
            elif arg_def.default is not None:
                args[arg_def.name] = arg_def.default

        return command_name, args

    async def execute(
        self,
        input_str: str,
        session_id: str | None = None,
    ) -> CommandResult:
        """
        Execute a command from input string.

        Args:
            input_str: Raw input like "/help models"
            session_id: Current session ID

        Returns:
            CommandResult
        """
        command_name, args = self.parse_input(input_str)

        if command_name is None:
            return CommandResult.fail("Not a command")

        command = self.get(command_name)
        if not command:
            return CommandResult.fail(f"Unknown command: /{command_name}")

        # Check required args
        for arg_def in command.args:
            if arg_def.required and arg_def.name not in args:
                return CommandResult.fail(
                    f"Missing required argument: {arg_def.name}\nUsage: {command.get_usage()}"
                )

        # Create context
        ctx = CommandContext(
            session_id=session_id,
            args=args,
            raw_input=input_str,
        )

        # Execute
        try:
            result = command.handler(ctx)
            if hasattr(result, "__await__"):
                result = await result
            return result
        except Exception as e:
            logger.error(f"Command error: {e}", exc_info=True)
            return CommandResult.fail(str(e))

    def is_command(self, input_str: str) -> bool:
        """Check if input is a command."""
        return input_str.strip().startswith("/")

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None


def get_command_registry() -> CommandRegistry:
    """Get the global command registry."""
    return CommandRegistry()


def register_command(
    name: str,
    description: str,
    handler: CommandHandler,
    args: list[CommandArg] | None = None,
    aliases: list[str] | None = None,
    category: str = "General",
    hidden: bool = False,
) -> Command:
    """
    Register a new command.

    Args:
        name: Command name (without slash)
        description: Short description
        handler: Function to handle the command
        args: Command arguments
        aliases: Alternative names
        category: Category for grouping
        hidden: Hide from help

    Returns:
        The registered command
    """
    command = Command(
        name=name,
        description=description,
        handler=handler,
        args=args or [],
        aliases=aliases or [],
        category=category,
        hidden=hidden,
    )
    get_command_registry().register(command)
    return command


async def execute_command(
    input_str: str,
    session_id: str | None = None,
) -> CommandResult:
    """Execute a command from input string."""
    return await get_command_registry().execute(input_str, session_id)
