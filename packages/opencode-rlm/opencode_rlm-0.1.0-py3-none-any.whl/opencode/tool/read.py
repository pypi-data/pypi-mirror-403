"""
Read tool for reading file contents.
"""

from __future__ import annotations

import base64
import mimetypes
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


class ReadTool(Tool):
    """Read files from the filesystem."""

    DEFAULT_LIMIT = 2000
    MAX_LINE_LENGTH = 2000
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

    @property
    def name(self) -> str:
        return "read"

    @property
    def description(self) -> str:
        return """Read a file from the filesystem.

The filePath must be an absolute path.
By default, reads up to 2000 lines from the beginning.
Use offset and limit for reading specific sections of long files.
Lines longer than 2000 characters will be truncated.
Results are returned with line numbers (1-indexed).
Can also read image files (returns base64 encoded)."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                ("filePath", "Absolute path to the file to read", STRING_PARAM),
            ],
            optional=[
                (
                    "offset",
                    "Line number to start reading from (0-based)",
                    INTEGER_PARAM,
                ),
                ("limit", "Number of lines to read (default: 2000)", INTEGER_PARAM),
            ],
        )

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Read a file."""
        file_path = kwargs.get("filePath", "")
        offset = kwargs.get("offset", 0)
        limit = kwargs.get("limit", self.DEFAULT_LIMIT)

        if not file_path:
            return ToolResult.fail("No file path provided")

        path = Path(file_path)
        if not path.is_absolute():
            path = ctx.working_directory / path

        if not path.exists():
            return ToolResult.fail(f"File not found: {path}")

        if not path.is_file():
            return ToolResult.fail(f"Not a file: {path}")

        # Check if it's an image
        suffix = path.suffix.lower()
        if suffix in self.IMAGE_EXTENSIONS:
            return await self._read_image(path)

        return await self._read_text(path, offset, limit)

    async def _read_image(self, path: Path) -> ToolResult:
        """Read an image file as base64."""
        try:
            data = path.read_bytes()
            encoded = base64.b64encode(data).decode("ascii")

            mime_type = mimetypes.guess_type(str(path))[0] or "image/png"

            return ToolResult.ok(
                f"Image file ({mime_type}, {len(data)} bytes)",
                image_base64=encoded,
                mime_type=mime_type,
            )
        except Exception as e:
            return ToolResult.fail(f"Failed to read image: {e}")

    async def _read_text(self, path: Path, offset: int, limit: int) -> ToolResult:
        """Read a text file with line numbers."""
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return ToolResult.fail(f"Failed to read file: {e}")

        if not content:
            return ToolResult.ok("(empty file)")

        lines = content.split("\n")
        total_lines = len(lines)

        # Apply offset and limit
        start = max(0, offset)
        end = min(start + limit, total_lines)
        selected_lines = lines[start:end]

        # Format with line numbers (cat -n style)
        output_lines = []
        for i, line in enumerate(selected_lines, start=start + 1):
            # Truncate long lines
            if len(line) > self.MAX_LINE_LENGTH:
                line = line[: self.MAX_LINE_LENGTH] + "..."
            # Right-align line number, tab, then content
            output_lines.append(f"{i:6}\t{line}")

        output = "\n".join(output_lines)

        # Add truncation note if needed
        if end < total_lines:
            output += f"\n\n... (showing lines {start + 1}-{end} of {total_lines})"

        return ToolResult.ok(output, total_lines=total_lines)
