"""
Write tool for creating/overwriting files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from opencode.tool.base import Tool, ToolContext, ToolResult, make_schema, STRING_PARAM


class WriteTool(Tool):
    """Write content to a file."""

    @property
    def name(self) -> str:
        return "write"

    @property
    def description(self) -> str:
        return """Write content to a file on the filesystem.

This will OVERWRITE the file if it exists.
If this is an existing file, you MUST use the Read tool first.
ALWAYS prefer editing existing files over creating new ones.
NEVER proactively create documentation files (*.md) unless requested."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                ("filePath", "Absolute path to the file to write", STRING_PARAM),
                ("content", "Content to write to the file", STRING_PARAM),
            ],
        )

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Write to a file."""
        file_path = kwargs.get("filePath", "")
        content = kwargs.get("content", "")

        if not file_path:
            return ToolResult.fail("No file path provided")

        path = Path(file_path)
        if not path.is_absolute():
            path = ctx.working_directory / path

        # Check if file exists (for warning)
        existed = path.exists()

        try:
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            path.write_text(content, encoding="utf-8")

            action = "Updated" if existed else "Created"
            return ToolResult.ok(
                f"{action} {path} ({len(content)} bytes)",
                existed=existed,
                bytes_written=len(content),
            )
        except Exception as e:
            return ToolResult.fail(f"Failed to write file: {e}")
