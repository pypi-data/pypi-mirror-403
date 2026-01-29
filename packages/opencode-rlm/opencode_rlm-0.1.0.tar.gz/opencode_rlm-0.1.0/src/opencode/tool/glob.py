"""
Glob tool for finding files by pattern.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from opencode.tool.base import Tool, ToolContext, ToolResult, make_schema, STRING_PARAM


class GlobTool(Tool):
    """Find files using glob patterns."""

    MAX_RESULTS = 500

    @property
    def name(self) -> str:
        return "glob"

    @property
    def description(self) -> str:
        return """Find files matching a glob pattern.

Supports patterns like "**/*.py", "src/**/*.ts", etc.
Returns matching file paths sorted by modification time.
Use this when you need to find files by name patterns."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                ("pattern", "Glob pattern to match files against", STRING_PARAM),
            ],
            optional=[
                (
                    "path",
                    "Directory to search in (defaults to working directory)",
                    STRING_PARAM,
                ),
            ],
        )

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Find files matching a glob pattern."""
        pattern = kwargs.get("pattern", "")
        search_path = kwargs.get("path")

        if not pattern:
            return ToolResult.fail("No pattern provided")

        # Determine search directory
        if search_path:
            base_dir = Path(search_path)
            if not base_dir.is_absolute():
                base_dir = ctx.working_directory / base_dir
        else:
            base_dir = ctx.working_directory

        if not base_dir.exists():
            return ToolResult.fail(f"Directory not found: {base_dir}")

        try:
            # Find matching files
            matches = list(base_dir.glob(pattern))

            # Filter to files only
            files = [p for p in matches if p.is_file()]

            # Sort by modification time (newest first)
            files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            # Limit results
            truncated = len(files) > self.MAX_RESULTS
            if truncated:
                files = files[: self.MAX_RESULTS]

            if not files:
                return ToolResult.ok("No files found")

            # Format output
            output_lines = [str(p) for p in files]
            output = "\n".join(output_lines)

            if truncated:
                output += f"\n\n... (showing first {self.MAX_RESULTS} results)"

            return ToolResult.ok(
                output,
                count=len(files),
                truncated=truncated,
            )

        except Exception as e:
            return ToolResult.fail(f"Glob search failed: {e}")
