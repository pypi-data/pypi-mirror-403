"""
Todo tools for task management.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal

from opencode.tool.base import (
    Tool,
    ToolContext,
    ToolResult,
    make_schema,
    STRING_PARAM,
    ARRAY_PARAM,
)


class TodoWriteTool(Tool):
    """Update the todo list."""

    @property
    def name(self) -> str:
        return "todowrite"

    @property
    def description(self) -> str:
        return """Update the todo list for tracking tasks.

Use this tool to:
- Plan complex multistep tasks (3+ steps)
- Track progress on implementation
- Break down large features into smaller tasks

Mark todos as:
- pending: Not yet started
- in_progress: Currently working on (only ONE at a time)
- completed: Task finished
- cancelled: No longer needed

Update status in real-time as you work."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                (
                    "todos",
                    "The updated todo list",
                    {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Unique identifier",
                                },
                                "content": {
                                    "type": "string",
                                    "description": "Task description",
                                },
                                "status": {
                                    "type": "string",
                                    "enum": [
                                        "pending",
                                        "in_progress",
                                        "completed",
                                        "cancelled",
                                    ],
                                },
                                "priority": {
                                    "type": "string",
                                    "enum": ["high", "medium", "low"],
                                },
                            },
                            "required": ["id", "content", "status", "priority"],
                        },
                    },
                ),
            ],
        )

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Update todos."""
        todos = kwargs.get("todos", [])

        if not isinstance(todos, list):
            return ToolResult.fail("todos must be a list")

        # Validate todos
        for todo in todos:
            if not isinstance(todo, dict):
                return ToolResult.fail("Each todo must be an object")

            required = ["id", "content", "status", "priority"]
            for field in required:
                if field not in todo:
                    return ToolResult.fail(f"Todo missing required field: {field}")

            if todo["status"] not in [
                "pending",
                "in_progress",
                "completed",
                "cancelled",
            ]:
                return ToolResult.fail(f"Invalid status: {todo['status']}")

            if todo["priority"] not in ["high", "medium", "low"]:
                return ToolResult.fail(f"Invalid priority: {todo['priority']}")

        # Count by status
        counts = {"pending": 0, "in_progress": 0, "completed": 0, "cancelled": 0}
        for todo in todos:
            counts[todo["status"]] += 1

        summary = ", ".join(f"{k}: {v}" for k, v in counts.items() if v > 0)

        return ToolResult.ok(
            f"Updated {len(todos)} todos ({summary})",
            todos=todos,
            counts=counts,
        )


class TodoReadTool(Tool):
    """Read the current todo list."""

    @property
    def name(self) -> str:
        return "todoread"

    @property
    def description(self) -> str:
        return "Read the current todo list to see task status."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Read todos (returns from session state)."""
        # Note: In the full implementation, this would read from session storage
        return ToolResult.ok(
            "No todos found. Use todowrite to create tasks.",
            todos=[],
        )
