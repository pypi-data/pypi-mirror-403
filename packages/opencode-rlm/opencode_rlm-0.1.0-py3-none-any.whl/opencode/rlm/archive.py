"""
Context archival system for RLM.

Summarizes and stores conversation segments to SQLite,
enabling retrieval of past context when needed.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from opencode.config.settings import get_config
from opencode.config.storage import (
    ContextBlock,
    Message,
    MessagePart,
    PartType,
    get_storage,
)
from opencode.events import EventType, Event, get_event_bus
from opencode.rlm.context import TokenCounter, get_context_manager

logger = logging.getLogger(__name__)


@dataclass
class ArchiveResult:
    """Result of an archival operation."""

    block_id: str
    tokens_archived: int
    messages_archived: int
    summary: str
    success: bool
    error: str | None = None


def create_archive_block(
    session_id: str,
    messages: list[Message],
    task_id: str | None = None,
    task_description: str = "",
) -> ContextBlock:
    """
    Create a context block from messages.

    Args:
        session_id: Session the messages belong to
        messages: Messages to archive
        task_id: Optional task ID for task-based archival
        task_description: Description of the task being archived

    Returns:
        ContextBlock ready to be stored
    """
    counter = TokenCounter()

    # Build content from messages
    content_parts = []
    for msg in messages:
        role = msg.role.value.upper()
        text_parts = []

        for part in msg.parts:
            if part.type == PartType.TEXT:
                text_parts.append(part.content.get("text", ""))
            elif part.type == PartType.TOOL_USE:
                tool_name = part.content.get("name", "unknown")
                text_parts.append(f"[Tool: {tool_name}]")
            elif part.type == PartType.TOOL_RESULT:
                result = part.content.get("result", "")
                # Truncate long results
                if len(result) > 500:
                    result = result[:500] + "..."
                text_parts.append(f"[Result: {result}]")

        if text_parts:
            content_parts.append(f"{role}: {' '.join(text_parts)}")

    content = "\n\n".join(content_parts)

    # Generate summary (first 200 chars of content + task description)
    summary_parts = []
    if task_description:
        summary_parts.append(task_description)
    if content:
        summary_parts.append(content[:200] + ("..." if len(content) > 200 else ""))
    summary = " | ".join(summary_parts)

    # Count tokens
    tokens = counter.count_text(content)

    return ContextBlock(
        id=f"ctx_{uuid.uuid4().hex[:12]}",
        session_id=session_id,
        task_id=task_id,
        task_description=task_description,
        summary=summary,
        content=content,
        tokens=tokens,
        created_at=datetime.now(),
    )


class ContextArchiver:
    """
    Archives conversation context to persistent storage.

    Handles both automatic archival (when threshold is reached)
    and task-based archival (when todos are completed).
    """

    def __init__(self) -> None:
        self._storage = get_storage()
        self._counter = TokenCounter()
        self._event_bus = get_event_bus()
        self._context_manager = get_context_manager()

        # Register for archive trigger
        self._context_manager.on_archive_needed(self._on_archive_needed)

    def archive_messages(
        self,
        session_id: str,
        messages: list[Message],
        task_id: str | None = None,
        task_description: str = "",
    ) -> ArchiveResult:
        """
        Archive a set of messages.

        Args:
            session_id: Session ID
            messages: Messages to archive
            task_id: Optional task ID
            task_description: Task description

        Returns:
            ArchiveResult with details
        """
        if not messages:
            return ArchiveResult(
                block_id="",
                tokens_archived=0,
                messages_archived=0,
                summary="",
                success=False,
                error="No messages to archive",
            )

        try:
            # Create block
            block = create_archive_block(
                session_id=session_id,
                messages=messages,
                task_id=task_id,
                task_description=task_description,
            )

            # Store it
            self._storage.add_context_block(block)

            # Update context manager
            self._context_manager.mark_archived(session_id, block.tokens)

            # Emit event
            self._emit_archive_event(session_id, block)

            logger.info(
                f"Archived {len(messages)} messages ({block.tokens} tokens) to block {block.id}"
            )

            return ArchiveResult(
                block_id=block.id,
                tokens_archived=block.tokens,
                messages_archived=len(messages),
                summary=block.summary,
                success=True,
            )

        except Exception as e:
            logger.error(f"Failed to archive messages: {e}")
            return ArchiveResult(
                block_id="",
                tokens_archived=0,
                messages_archived=0,
                summary="",
                success=False,
                error=str(e),
            )

    def archive_oldest(
        self,
        session_id: str,
        target_tokens: int | None = None,
    ) -> ArchiveResult:
        """
        Archive oldest messages to free up context space.

        Args:
            session_id: Session ID
            target_tokens: Target tokens to free (defaults to 25% of limit)

        Returns:
            ArchiveResult
        """
        messages = self._storage.get_messages(session_id)
        if not messages:
            return ArchiveResult(
                block_id="",
                tokens_archived=0,
                messages_archived=0,
                summary="",
                success=False,
                error="No messages in session",
            )

        # Calculate target
        state = self._context_manager.get_state(session_id)
        if target_tokens is None:
            target_tokens = int(state.model_limit * 0.25)

        # Find messages to archive
        messages_to_archive = []
        tokens_accumulated = 0

        for msg in messages:
            if tokens_accumulated >= target_tokens:
                break

            estimate = self._counter.count_message(msg)
            tokens_accumulated += estimate.total
            messages_to_archive.append(msg)

        if not messages_to_archive:
            return ArchiveResult(
                block_id="",
                tokens_archived=0,
                messages_archived=0,
                summary="",
                success=False,
                error="No messages old enough to archive",
            )

        return self.archive_messages(
            session_id=session_id,
            messages=messages_to_archive,
            task_description="Automatic archival - context threshold reached",
        )

    def archive_task(
        self,
        session_id: str,
        task_id: str,
        task_description: str,
        messages: list[Message],
    ) -> ArchiveResult:
        """
        Archive messages related to a completed task.

        Args:
            session_id: Session ID
            task_id: Task/todo ID
            task_description: Task description
            messages: Messages related to the task

        Returns:
            ArchiveResult
        """
        return self.archive_messages(
            session_id=session_id,
            messages=messages,
            task_id=task_id,
            task_description=task_description,
        )

    def get_archived_blocks(
        self,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[ContextBlock]:
        """Get archived context blocks."""
        return self._storage.get_context_blocks(session_id=session_id, limit=limit)

    def _on_archive_needed(self, session_id: str) -> None:
        """Callback when archival is needed."""
        config = get_config()
        if not config.rlm.enabled:
            return

        # Emit start event
        self._event_bus.emit_sync(
            Event(
                type=EventType.RLM_ARCHIVE_STARTED,
                data={"session_id": session_id},
            )
        )

        # Perform archival
        result = self.archive_oldest(session_id)

        # Emit completion event
        self._event_bus.emit_sync(
            Event(
                type=EventType.RLM_ARCHIVE_COMPLETED,
                data={
                    "session_id": session_id,
                    "block_id": result.block_id,
                    "tokens_archived": result.tokens_archived,
                    "success": result.success,
                },
            )
        )

    def _emit_archive_event(self, session_id: str, block: ContextBlock) -> None:
        """Emit archive completed event."""
        self._event_bus.emit_sync(
            Event(
                type=EventType.RLM_ARCHIVE_COMPLETED,
                data={
                    "session_id": session_id,
                    "block_id": block.id,
                    "tokens": block.tokens,
                    "summary": block.summary,
                },
            )
        )


# Global archiver instance
_archiver: ContextArchiver | None = None


def get_archiver() -> ContextArchiver:
    """Get the global archiver instance."""
    global _archiver
    if _archiver is None:
        _archiver = ContextArchiver()
    return _archiver
