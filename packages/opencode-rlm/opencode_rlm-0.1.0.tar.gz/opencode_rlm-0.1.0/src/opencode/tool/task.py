"""
Task tool for launching sub-agents.
"""

from __future__ import annotations

from typing import Any

from opencode.tool.base import Tool, ToolContext, ToolResult, make_schema, STRING_PARAM


class TaskTool(Tool):
    """Launch sub-agents for parallel work."""

    @property
    def name(self) -> str:
        return "task"

    @property
    def description(self) -> str:
        return """Launch a sub-agent to handle complex, multistep tasks autonomously.

Available agent types:
- general: For researching and executing multi-step tasks in parallel
- explore: Fast agent for codebase exploration (find files, search code)

Use this when:
- Task requires multiple independent pieces of work
- You need to explore a codebase without using context
- Task matches a specialized agent's description

Launch multiple agents in parallel when possible for efficiency."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                (
                    "description",
                    "Short (3-5 words) description of the task",
                    STRING_PARAM,
                ),
                ("prompt", "Detailed task for the agent to perform", STRING_PARAM),
                (
                    "subagent_type",
                    "Type of agent to use",
                    {
                        "type": "string",
                        "enum": ["general", "explore"],
                    },
                ),
            ],
            optional=[
                ("session_id", "Existing task session to continue", STRING_PARAM),
                ("command", "The command that triggered this task", STRING_PARAM),
            ],
        )

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Launch a sub-agent task."""
        description = kwargs.get("description", "")
        prompt = kwargs.get("prompt", "")
        subagent_type = kwargs.get("subagent_type", "general")

        if not description:
            return ToolResult.fail("No description provided")
        if not prompt:
            return ToolResult.fail("No prompt provided")

        # In the full implementation, this would spawn a sub-agent
        # For now, return task info for the orchestrator to handle
        return ToolResult.ok(
            f"Launching {subagent_type} agent: {description}",
            description=description,
            prompt=prompt,
            subagent_type=subagent_type,
            task_launched=True,
        )
