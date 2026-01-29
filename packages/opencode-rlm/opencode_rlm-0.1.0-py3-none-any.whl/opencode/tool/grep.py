"""
Grep tool for searching file contents.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from opencode.tool.base import Tool, ToolContext, ToolResult, make_schema, STRING_PARAM


class GrepTool(Tool):
    """Search file contents using regex patterns."""

    MAX_MATCHES = 200
    MAX_FILES = 100

    @property
    def name(self) -> str:
        return "grep"

    @property
    def description(self) -> str:
        return """Search file contents using regular expressions.

Supports full regex syntax (e.g., "log.*Error", "function\\s+\\w+").
Use the include parameter to filter by file pattern (e.g., "*.py").
Returns file paths and line numbers with matches, sorted by modification time."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                ("pattern", "Regex pattern to search for", STRING_PARAM),
            ],
            optional=[
                (
                    "path",
                    "Directory to search in (defaults to working directory)",
                    STRING_PARAM,
                ),
                (
                    "include",
                    'File pattern to include (e.g., "*.py", "*.{ts,tsx}")',
                    STRING_PARAM,
                ),
            ],
        )

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Search for pattern in files."""
        pattern = kwargs.get("pattern", "")
        search_path = kwargs.get("path")
        include = kwargs.get("include", "*")

        if not pattern:
            return ToolResult.fail("No pattern provided")

        # Compile regex
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return ToolResult.fail(f"Invalid regex pattern: {e}")

        # Determine search directory
        if search_path:
            base_dir = Path(search_path)
            if not base_dir.is_absolute():
                base_dir = ctx.working_directory / base_dir
        else:
            base_dir = ctx.working_directory

        if not base_dir.exists():
            return ToolResult.fail(f"Directory not found: {base_dir}")

        # Handle include patterns like "*.{ts,tsx}"
        include_patterns = self._expand_pattern(include)

        results: list[tuple[Path, int, float]] = []  # (path, line_num, mtime)
        files_searched = 0

        try:
            for file_pattern in include_patterns:
                for file_path in base_dir.rglob(file_pattern):
                    if not file_path.is_file():
                        continue

                    files_searched += 1
                    if files_searched > self.MAX_FILES * 10:
                        break

                    try:
                        content = file_path.read_text(
                            encoding="utf-8", errors="replace"
                        )
                        mtime = file_path.stat().st_mtime

                        for i, line in enumerate(content.split("\n"), 1):
                            if regex.search(line):
                                results.append((file_path, i, mtime))
                                if len(results) >= self.MAX_MATCHES:
                                    break
                    except Exception:
                        continue

                    if len(results) >= self.MAX_MATCHES:
                        break

            if not results:
                return ToolResult.ok("No matches found")

            # Sort by modification time (newest first)
            results.sort(key=lambda x: x[2], reverse=True)

            # Group by file
            file_matches: dict[Path, list[int]] = {}
            for path, line_num, _ in results:
                if path not in file_matches:
                    file_matches[path] = []
                file_matches[path].append(line_num)

            # Format output
            output_lines = []
            for path, lines in file_matches.items():
                line_nums = ", ".join(str(n) for n in lines[:10])
                if len(lines) > 10:
                    line_nums += f" ... (+{len(lines) - 10} more)"
                output_lines.append(f"{path}:{line_nums}")

            output = "\n".join(output_lines)

            truncated = len(results) >= self.MAX_MATCHES
            if truncated:
                output += f"\n\n... (showing first {self.MAX_MATCHES} matches)"

            return ToolResult.ok(
                output,
                match_count=len(results),
                file_count=len(file_matches),
                truncated=truncated,
            )

        except Exception as e:
            return ToolResult.fail(f"Search failed: {e}")

    def _expand_pattern(self, pattern: str) -> list[str]:
        """Expand brace patterns like *.{ts,tsx} into multiple patterns."""
        # Simple brace expansion
        match = re.search(r"\{([^}]+)\}", pattern)
        if match:
            options = match.group(1).split(",")
            prefix = pattern[: match.start()]
            suffix = pattern[match.end() :]
            return [f"{prefix}{opt.strip()}{suffix}" for opt in options]
        return [pattern]
