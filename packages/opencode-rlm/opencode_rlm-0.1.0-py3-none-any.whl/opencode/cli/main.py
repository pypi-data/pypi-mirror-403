"""
Main CLI entry point for OpenCode.

Provides the command-line interface matching opencode's yargs-based CLI.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Sequence


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="opencode",
        description="OpenCode - AI-powered development tool",
    )

    parser.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="Show version number",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Default TUI command (no subcommand)
    parser.add_argument(
        "project",
        nargs="?",
        help="Project directory to open",
    )

    parser.add_argument(
        "--continue",
        "-c",
        dest="continue_session",
        action="store_true",
        help="Continue the last session",
    )

    parser.add_argument(
        "--session",
        "-s",
        dest="session_id",
        help="Continue a specific session",
    )

    parser.add_argument(
        "--model",
        "-m",
        help="Model to use (provider/model)",
    )

    parser.add_argument(
        "--agent",
        default="build",
        help="Agent to use (default: build)",
    )

    parser.add_argument(
        "--prompt",
        "-p",
        help="Initial prompt to send",
    )

    parser.add_argument(
        "--port",
        type=int,
        help="Server port (for server mode)",
    )

    # Run command (non-interactive)
    run_parser = subparsers.add_parser(
        "run",
        help="Run with a message (non-interactive)",
    )
    run_parser.add_argument(
        "message",
        nargs="*",
        help="Message to send",
    )
    run_parser.add_argument(
        "--model",
        "-m",
        help="Model to use",
    )
    run_parser.add_argument(
        "--agent",
        default="build",
        help="Agent to use",
    )
    run_parser.add_argument(
        "--format",
        choices=["default", "json"],
        default="default",
        help="Output format",
    )

    # Serve command
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start the server in background mode",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=4096,
        help="Server port",
    )

    # Models command
    subparsers.add_parser(
        "models",
        help="List available models",
    )

    # Sessions command
    sessions_parser = subparsers.add_parser(
        "session",
        help="Session management",
    )
    sessions_parser.add_argument(
        "action",
        choices=["list", "delete", "export", "import"],
        nargs="?",
        default="list",
        help="Session action",
    )

    # Auth command
    auth_parser = subparsers.add_parser(
        "auth",
        help="Manage provider authentication",
    )
    auth_parser.add_argument(
        "provider",
        nargs="?",
        help="Provider to authenticate",
    )

    # Upgrade command
    subparsers.add_parser(
        "upgrade",
        help="Upgrade to latest version",
    )

    return parser


def main(args: Sequence[str] | None = None) -> int:
    """Main entry point."""
    parser = create_parser()
    parsed = parser.parse_args(args)

    if parsed.version:
        from opencode import __version__

        print(f"opencode {__version__}")
        return 0

    if parsed.command == "run":
        return run_command(parsed)
    elif parsed.command == "serve":
        return serve_command(parsed)
    elif parsed.command == "models":
        return models_command(parsed)
    elif parsed.command == "session":
        return session_command(parsed)
    elif parsed.command == "auth":
        return auth_command(parsed)
    elif parsed.command == "upgrade":
        return upgrade_command(parsed)
    else:
        # Default: launch TUI
        return tui_command(parsed)


def tui_command(args: argparse.Namespace) -> int:
    """Launch the TUI."""
    from opencode.tui import run_app

    project = Path(args.project) if args.project else Path.cwd()

    run_app(
        working_directory=project,
        session_id=args.session_id,
        model=args.model,
        agent=args.agent,
    )

    return 0


def run_command(args: argparse.Namespace) -> int:
    """Run a non-interactive session."""
    message = " ".join(args.message) if args.message else None

    if not message:
        print("Error: No message provided", file=sys.stderr)
        return 1

    # Run the message and get response
    print(f"Running: {message}")
    print("(Non-interactive mode not fully implemented yet)")

    return 0


def serve_command(args: argparse.Namespace) -> int:
    """Start the server."""
    print(f"Starting server on port {args.port}...")
    print("(Server mode not fully implemented yet)")
    return 0


def models_command(args: argparse.Namespace) -> int:
    """List available models."""
    print("Available models:")
    print()
    print("Anthropic:")
    print("  - anthropic/claude-sonnet-4-20250514 (Claude Sonnet 4)")
    print("  - anthropic/claude-opus-4-20250514 (Claude Opus 4)")
    print("  - anthropic/claude-3-5-sonnet-20241022 (Claude 3.5 Sonnet)")
    print()
    print("OpenAI:")
    print("  - openai/gpt-4o (GPT-4o)")
    print("  - openai/gpt-4o-mini (GPT-4o Mini)")
    print("  - openai/o1 (o1)")
    print()
    return 0


def session_command(args: argparse.Namespace) -> int:
    """Session management."""
    action = args.action

    if action == "list":
        print("Recent sessions:")
        print("(Session listing not fully implemented yet)")
    elif action == "delete":
        print("Delete session (not implemented)")
    elif action == "export":
        print("Export session (not implemented)")
    elif action == "import":
        print("Import session (not implemented)")

    return 0


def auth_command(args: argparse.Namespace) -> int:
    """Manage authentication."""
    provider = args.provider

    if provider:
        print(f"Authenticating with {provider}...")
        print("(Auth not fully implemented yet)")
    else:
        print("Providers:")
        print("  - anthropic (ANTHROPIC_API_KEY)")
        print("  - openai (OPENAI_API_KEY)")
        print()
        print("Set API keys as environment variables.")

    return 0


def upgrade_command(args: argparse.Namespace) -> int:
    """Upgrade to latest version."""
    print("Checking for updates...")
    print("pip install --upgrade opencode-rlm")
    return 0


def cli() -> None:
    """CLI entry point for setuptools."""
    sys.exit(main())


if __name__ == "__main__":
    cli()
