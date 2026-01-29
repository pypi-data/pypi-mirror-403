"""
Bash tool for executing shell commands.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any

from opencode.tool.base import (
    Tool,
    ToolContext,
    ToolResult,
    make_schema,
    STRING_PARAM,
    INTEGER_PARAM,
)


class BashTool(Tool):
    """Execute shell commands with timeout and working directory support."""

    DEFAULT_TIMEOUT = 120000  # 2 minutes in ms
    MAX_OUTPUT_LINES = 2000
    MAX_OUTPUT_BYTES = 51200  # 50KB

    @property
    def name(self) -> str:
        return "bash"

    @property
    def description(self) -> str:
        return """Execute a bash command in a persistent shell session.

Use for terminal operations like git, npm, docker, etc.
DO NOT use for file operations - use dedicated tools instead.

Commands run in the working directory by default.
Use the workdir parameter to run in a different directory.

Output exceeding limits will be truncated and saved to a file."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                ("command", "The command to execute", STRING_PARAM),
                (
                    "description",
                    "Brief description of what this command does (5-10 words)",
                    STRING_PARAM,
                ),
            ],
            optional=[
                ("timeout", "Timeout in milliseconds (default: 120000)", INTEGER_PARAM),
                ("workdir", "Working directory for the command", STRING_PARAM),
            ],
        )

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Execute a shell command."""
        command = kwargs.get("command", "")
        timeout_ms = kwargs.get("timeout", self.DEFAULT_TIMEOUT)
        workdir = kwargs.get("workdir")

        if not command:
            return ToolResult.fail("No command provided")

        # Determine working directory
        cwd = Path(workdir) if workdir else ctx.working_directory
        if not cwd.exists():
            return ToolResult.fail(f"Working directory does not exist: {cwd}")

        try:
            # Run command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(cwd),
                env={**os.environ, "TERM": "dumb"},
            )

            timeout_sec = timeout_ms / 1000
            try:
                stdout, _ = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_sec,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult.fail(
                    f"Command timed out after {timeout_sec}s",
                    output="",
                )

            output = stdout.decode("utf-8", errors="replace")

            # Check for truncation
            lines = output.split("\n")
            truncated = False
            full_output_path = None

            if (
                len(lines) > self.MAX_OUTPUT_LINES
                or len(output) > self.MAX_OUTPUT_BYTES
            ):
                truncated = True
                # Save full output to file
                output_file = (
                    ctx.working_directory / f".opencode_output_{ctx.message_id}.txt"
                )
                output_file.write_text(output)
                full_output_path = str(output_file)

                # Truncate for response
                if len(lines) > self.MAX_OUTPUT_LINES:
                    output = "\n".join(lines[: self.MAX_OUTPUT_LINES])
                    output += f"\n\n... (truncated, full output at {full_output_path})"
                elif len(output) > self.MAX_OUTPUT_BYTES:
                    output = output[: self.MAX_OUTPUT_BYTES]
                    output += f"\n\n... (truncated, full output at {full_output_path})"

            return ToolResult(
                success=process.returncode == 0,
                output=output,
                error=None
                if process.returncode == 0
                else f"Exit code: {process.returncode}",
                truncated=truncated,
                full_output_path=full_output_path,
                metadata={"exit_code": process.returncode},
            )

        except Exception as e:
            return ToolResult.fail(f"Command execution failed: {e}")
