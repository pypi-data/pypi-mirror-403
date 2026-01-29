"""
Built-in slash commands.

Provides standard commands like /help, /models, /agents, /clear, etc.
"""

from __future__ import annotations

from pathlib import Path

from opencode.commands.registry import (
    Command,
    CommandArg,
    CommandContext,
    CommandResult,
    get_command_registry,
)


def _help_handler(ctx: CommandContext) -> CommandResult:
    """Show help for commands."""
    registry = get_command_registry()
    topic = ctx.args.get("topic")

    if topic:
        # Help for specific command
        command = registry.get(topic)
        if command:
            return CommandResult.ok(command.get_help())
        return CommandResult.fail(f"Unknown command: {topic}")

    # General help
    lines = ["Available Commands:", ""]

    for category, commands in registry.list_by_category().items():
        lines.append(f"{category}:")
        for cmd in commands:
            lines.append(f"  /{cmd.name:12} {cmd.description}")
        lines.append("")

    lines.append("Type /help <command> for detailed help on a command.")
    return CommandResult.ok("\n".join(lines))


def _models_handler(ctx: CommandContext) -> CommandResult:
    """List or switch models."""
    from opencode.config.settings import get_config

    action = ctx.args.get("action", "list")
    config = get_config()

    if action == "list":
        lines = [
            "Available Models:",
            "",
            f"Current: {config.model}",
            "",
            "Anthropic:",
            "  claude-sonnet-4     Best balance of speed and capability",
            "  claude-3-opus       Most capable, for complex tasks",
            "  claude-haiku        Fastest, for simple tasks",
            "",
            "OpenAI:",
            "  gpt-4o              GPT-4 Omni - multimodal",
            "  gpt-4o-mini         Smaller, faster GPT-4o",
            "  o1                  Reasoning model",
            "",
            "Use /model <name> to switch models.",
        ]
        return CommandResult.ok("\n".join(lines))

    # Switch model
    return CommandResult.ok(f"Model switching not yet implemented. Use Ctrl+M instead.")


def _agents_handler(ctx: CommandContext) -> CommandResult:
    """List or switch agents."""
    from opencode.agent.registry import get_agent_registry

    action = ctx.args.get("action", "list")
    registry = get_agent_registry()

    if action == "list":
        current = registry.get_current()
        agents = registry.list_primary()

        lines = ["Available Agents:", ""]

        for agent in agents:
            marker = "*" if agent.id == current.id else " "
            lines.append(f"  {marker} {agent.name:10} {agent.description}")

        lines.append("")
        lines.append("Use /agent <name> to switch agents, or press Tab to cycle.")
        return CommandResult.ok("\n".join(lines))

    # Switch agent
    agent_name = action
    if registry.set_current(agent_name):
        agent = registry.get_current()
        return CommandResult.ok(f"Switched to {agent.name} agent.")
    return CommandResult.fail(f"Unknown agent: {agent_name}")


def _clear_handler(ctx: CommandContext) -> CommandResult:
    """Clear the current conversation."""
    return CommandResult.ok(
        "Clear command received. This will be handled by the TUI.",
        data={"action": "clear"},
    )


def _compact_handler(ctx: CommandContext) -> CommandResult:
    """Compact the current session by archiving old messages."""
    from opencode.session.manager import get_session_manager

    session_id = ctx.session_id
    if not session_id:
        return CommandResult.fail("No active session.")

    manager = get_session_manager()
    if manager.compact(session_id):
        return CommandResult.ok("Session compacted. Old messages have been archived.")
    return CommandResult.fail("No messages to archive.")


def _export_handler(ctx: CommandContext) -> CommandResult:
    """Export the current session."""
    from opencode.session.export import export_session

    session_id = ctx.session_id
    if not session_id:
        return CommandResult.fail("No active session.")

    path = ctx.args.get("path")
    if not path:
        # Default path
        path = Path(f"session_{session_id}.json")

    result = export_session(session_id, path)
    if result.success:
        return CommandResult.ok(f"Session exported to: {result.path}")
    return CommandResult.fail(result.error or "Export failed")


def _sessions_handler(ctx: CommandContext) -> CommandResult:
    """List recent sessions."""
    from opencode.session.manager import get_session_manager

    manager = get_session_manager()
    sessions = manager.list(limit=10)

    if not sessions:
        return CommandResult.ok("No sessions found.")

    lines = ["Recent Sessions:", ""]

    current_id = manager.current_session_id
    for session in sessions:
        marker = "*" if session.id == current_id else " "
        lines.append(
            f"  {marker} {session.title[:30]:30} "
            f"({session.message_count} messages, "
            f"{session.updated_at.strftime('%b %d %H:%M')})"
        )

    lines.append("")
    lines.append("Use Ctrl+S to open session manager.")
    return CommandResult.ok("\n".join(lines))


def _config_handler(ctx: CommandContext) -> CommandResult:
    """Show or modify configuration."""
    from opencode.config.settings import get_config
    from opencode.config.paths import get_global_config_path, get_project_config_path

    key = ctx.args.get("key")
    config = get_config()

    if not key:
        # Show config info
        global_path = get_global_config_path()
        project_path = get_project_config_path()

        lines = [
            "Configuration:",
            "",
            f"Global config: {global_path}",
            f"Project config: {project_path or 'Not found'}",
            "",
            "Current settings:",
            f"  theme: {config.theme}",
            f"  model: {config.model}",
            f"  default_agent: {config.default_agent}",
            f"  rlm.enabled: {config.rlm.enabled}",
            f"  rlm.threshold: {config.rlm.threshold_ratio:.0%}",
            "",
            "Use /config <key> to view a specific setting.",
        ]
        return CommandResult.ok("\n".join(lines))

    # Get specific config value
    try:
        parts = key.split(".")
        value = config
        for part in parts:
            value = getattr(value, part)
        return CommandResult.ok(f"{key} = {value}")
    except AttributeError:
        return CommandResult.fail(f"Unknown config key: {key}")


def _context_handler(ctx: CommandContext) -> CommandResult:
    """Show RLM context usage."""
    from opencode.rlm.context import get_context_manager

    session_id = ctx.session_id
    if not session_id:
        return CommandResult.fail("No active session.")

    manager = get_context_manager()
    state = manager.get_state(session_id)

    lines = [
        "Context Usage:",
        "",
        f"Total tokens: {state.total_tokens:,} / {state.model_limit:,}",
        f"Usage: {state.usage_ratio:.1%}",
        f"Input tokens: {state.input_tokens:,}",
        f"Output tokens: {state.output_tokens:,}",
        f"Messages: {state.message_count}",
        f"Archives: {state.archived_count}",
        "",
    ]

    if state.should_archive:
        lines.append("Warning: Context threshold reached. Archival recommended.")
    else:
        lines.append(f"Available: {state.available_tokens:,} tokens")

    return CommandResult.ok("\n".join(lines))


def _search_handler(ctx: CommandContext) -> CommandResult:
    """Search archived context."""
    from opencode.rlm.search import get_searcher

    query = ctx.args.get("query")
    if not query:
        return CommandResult.fail("Please provide a search query.")

    searcher = get_searcher()
    results = searcher.search(query, limit=5)

    if not results:
        return CommandResult.ok("No results found.")

    lines = [f"Search results for '{query}':", ""]

    for result in results:
        block = result.block
        lines.append(f"Score: {result.score:.2f}")
        lines.append(f"Task: {block.task_description or 'General'}")
        lines.append(f"Summary: {block.summary[:100]}...")
        lines.append("")

    return CommandResult.ok("\n".join(lines))


def _theme_handler(ctx: CommandContext) -> CommandResult:
    """Change the color theme."""
    return CommandResult.ok(
        "Use Ctrl+T to open the theme selector.",
        data={"action": "theme"},
    )


def _quit_handler(ctx: CommandContext) -> CommandResult:
    """Exit OpenCode."""
    return CommandResult.ok(
        "Goodbye!",
        data={"action": "quit"},
    )


def _version_handler(ctx: CommandContext) -> CommandResult:
    """Show version information."""
    lines = [
        "OpenCode v0.1.0",
        "",
        "A Python TUI for AI-assisted coding",
        "with Recursive Language Model support.",
        "",
        "https://github.com/opencode-ai/opencode",
    ]
    return CommandResult.ok("\n".join(lines))


def register_builtin_commands() -> None:
    """Register all built-in commands."""
    registry = get_command_registry()

    # Help
    registry.register(
        Command(
            name="help",
            description="Show help for commands",
            handler=_help_handler,
            args=[
                CommandArg("topic", "Command or topic to get help for"),
            ],
            aliases=["h", "?"],
            category="Help",
        )
    )

    # Models
    registry.register(
        Command(
            name="models",
            description="List available models",
            handler=_models_handler,
            args=[
                CommandArg("action", "Action: list or model name", default="list"),
            ],
            aliases=["model", "m"],
            category="Model",
        )
    )

    # Agents
    registry.register(
        Command(
            name="agents",
            description="List or switch agents",
            handler=_agents_handler,
            args=[
                CommandArg("action", "Action: list or agent name", default="list"),
            ],
            aliases=["agent", "a"],
            category="Agent",
        )
    )

    # Clear
    registry.register(
        Command(
            name="clear",
            description="Clear the current conversation",
            handler=_clear_handler,
            aliases=["cls"],
            category="Edit",
        )
    )

    # Compact
    registry.register(
        Command(
            name="compact",
            description="Archive old messages to free context",
            handler=_compact_handler,
            category="Session",
        )
    )

    # Export
    registry.register(
        Command(
            name="export",
            description="Export session to file",
            handler=_export_handler,
            args=[
                CommandArg("path", "Output file path", type="path"),
            ],
            category="Session",
        )
    )

    # Sessions
    registry.register(
        Command(
            name="sessions",
            description="List recent sessions",
            handler=_sessions_handler,
            aliases=["session", "s"],
            category="Session",
        )
    )

    # Config
    registry.register(
        Command(
            name="config",
            description="Show or modify configuration",
            handler=_config_handler,
            args=[
                CommandArg("key", "Config key to view (e.g., rlm.enabled)"),
            ],
            aliases=["settings"],
            category="Config",
        )
    )

    # Context
    registry.register(
        Command(
            name="context",
            description="Show RLM context usage",
            handler=_context_handler,
            aliases=["ctx", "tokens"],
            category="RLM",
        )
    )

    # Search
    registry.register(
        Command(
            name="search",
            description="Search archived context",
            handler=_search_handler,
            args=[
                CommandArg("query", "Search query", required=True),
            ],
            aliases=["find"],
            category="RLM",
        )
    )

    # Theme
    registry.register(
        Command(
            name="theme",
            description="Change the color theme",
            handler=_theme_handler,
            aliases=["themes"],
            category="View",
        )
    )

    # Quit
    registry.register(
        Command(
            name="quit",
            description="Exit OpenCode",
            handler=_quit_handler,
            aliases=["exit", "q"],
            category="General",
        )
    )

    # Version
    registry.register(
        Command(
            name="version",
            description="Show version information",
            handler=_version_handler,
            aliases=["v"],
            category="Help",
        )
    )
