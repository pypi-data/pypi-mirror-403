"""
Message display widget for conversation history.

Renders messages with proper formatting, syntax highlighting
for code blocks, and tool output display.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from textual.widgets import Static, Markdown
from textual.containers import Vertical, Container
from textual.app import ComposeResult

from opencode.config.storage import Message, MessagePart, MessageRole, PartType


class MessageView(Static):
    """
    Display a single message in the conversation.

    Handles:
    - User messages (simple text)
    - Assistant messages (markdown with code)
    - Tool calls and results
    - Streaming updates
    """

    DEFAULT_CSS = """
    MessageView {
        padding: 1;
        margin-bottom: 1;
    }
    
    MessageView.user {
        background: $primary 15%;
        border-left: thick $primary;
    }
    
    MessageView.assistant {
        background: $secondary 15%;
        border-left: thick $secondary;
    }
    
    MessageView.tool {
        background: $surface;
        border-left: thick $warning;
    }
    
    .message-role {
        text-style: bold;
        margin-bottom: 1;
    }
    
    .message-content {
        
    }
    
    .tool-call {
        background: $panel;
        padding: 1;
        margin: 1 0;
    }
    
    .tool-name {
        text-style: bold;
        color: $warning;
    }
    
    .tool-result {
        margin-top: 1;
        padding: 1;
        background: $surface;
    }
    """

    def __init__(self, message: Message, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.message = message
        self.add_class(message.role.value)

    def compose(self) -> ComposeResult:
        """Compose the message display."""
        # Role indicator
        role_display = {
            MessageRole.USER: "You",
            MessageRole.ASSISTANT: "Assistant",
            MessageRole.SYSTEM: "System",
            MessageRole.TOOL: "Tool",
        }

        yield Static(
            role_display.get(self.message.role, "Unknown"), classes="message-role"
        )

        # Message content
        if isinstance(self.message.content, str):
            yield Markdown(self.message.content, classes="message-content")
        else:
            for part in self.message.parts:
                yield self._render_part(part)

        # Tool calls
        for tool_call in self.message.tool_calls:
            yield self._render_tool_call(tool_call)

    def _render_part(self, part: MessagePart) -> Static:
        """Render a message part."""
        if part.type == PartType.TEXT:
            text = part.content.get("text", "")
            return Markdown(text, classes="message-content")

        if part.type == PartType.TOOL_USE:
            return self._render_tool_use(part.content)

        if part.type == PartType.TOOL_RESULT:
            return self._render_tool_result(part.content)

        return Static(f"[{part.type.value}]")

    def _render_tool_call(self, tool_call: Any) -> Container:
        """Render a tool call."""
        with Container(classes="tool-call") as container:
            yield Static(f"Tool: {tool_call.name}", classes="tool-name")
            # Could show arguments here
        return container

    def _render_tool_use(self, content: dict) -> Static:
        """Render tool use content."""
        name = content.get("name", "unknown")
        return Static(f"Calling tool: {name}", classes="tool-call")

    def _render_tool_result(self, content: dict) -> Static:
        """Render tool result content."""
        result = content.get("content", "")
        is_error = content.get("is_error", False)

        if is_error:
            return Static(f"Error: {result}", classes="tool-result error")

        # Truncate long results
        if len(result) > 500:
            result = result[:500] + "..."

        return Static(result, classes="tool-result")


class MessageList(Vertical):
    """
    Scrollable list of messages.

    Supports:
    - Automatic scrolling to bottom
    - Streaming message updates
    - Keyboard navigation
    """

    DEFAULT_CSS = """
    MessageList {
        height: 1fr;
        overflow-y: scroll;
    }
    """

    def __init__(self, messages: list[Message] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.messages = messages or []

    def compose(self) -> ComposeResult:
        """Compose the message list."""
        for message in self.messages:
            yield MessageView(message)

    def add_message(self, message: Message) -> None:
        """Add a new message to the list."""
        self.messages.append(message)
        self.mount(MessageView(message))
        self.scroll_end()

    def update_last_message(self, content: str) -> None:
        """Update the last message (for streaming)."""
        if self.messages:
            # Update the message content
            self.messages[-1].content = content
            # Re-render the last message view
            children = list(self.children)
            if children:
                last_view = children[-1]
                if isinstance(last_view, MessageView):
                    last_view.refresh()

    def clear_messages(self) -> None:
        """Clear all messages."""
        self.messages.clear()
        self.remove_children()
