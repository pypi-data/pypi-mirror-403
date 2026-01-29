"""Tool system for OpenCode."""

from opencode.tool.base import (
    Tool,
    ToolContext,
    ToolResult,
    ToolPermission,
    PermissionRule,
)
from opencode.tool.registry import (
    ToolRegistry,
    get_tool_registry,
)

__all__ = [
    "Tool",
    "ToolContext",
    "ToolResult",
    "ToolPermission",
    "PermissionRule",
    "ToolRegistry",
    "get_tool_registry",
]
