"""
RLM conversation handler.

Integrates RLM context management into the conversation flow:
- Injects relevant archived context before sending to provider
- Tracks token usage across messages
- Triggers archival when threshold is reached
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from opencode.config.settings import get_config
from opencode.config.storage import Message, MessagePart, MessageRole, PartType
from opencode.rlm.context import get_context_manager, ContextState
from opencode.rlm.retrieve import get_retriever, RetrievalContext
from opencode.rlm.archive import get_archiver


logger = logging.getLogger(__name__)


@dataclass
class RLMContext:
    """RLM context state for a conversation turn."""

    session_id: str
    retrieved_context: RetrievalContext | None = None
    context_state: ContextState | None = None
    system_injection: str = ""

    @property
    def has_retrieved_context(self) -> bool:
        return self.retrieved_context is not None and not self.retrieved_context.is_empty


class RLMHandler:
    """
    Handles RLM integration for conversations.

    Call before sending messages to provider to:
    - Check if relevant context should be injected
    - Track token usage
    - Trigger archival when needed
    """

    _instance: RLMHandler | None = None

    def __new__(cls) -> RLMHandler:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._context_manager = get_context_manager()
        self._retriever = get_retriever()
        self._archiver = get_archiver()
        self._config = get_config()
        self._initialized = True

    def prepare_for_query(
        self,
        session_id: str,
        user_query: str,
        messages: list[Message],
        model: str | None = None,
    ) -> RLMContext:
        """
        Prepare RLM context for a user query.

        Call this before sending messages to the provider to:
        1. Retrieve relevant archived context
        2. Update token tracking
        3. Get any system message injection needed

        Args:
            session_id: Current session ID
            user_query: The user's query text
            messages: Current conversation messages
            model: Model being used (for token limits)

        Returns:
            RLMContext with retrieval info and system injection
        """
        rlm_context = RLMContext(session_id=session_id)

        if not self._config.rlm.enabled:
            return rlm_context

        # Update context state from current messages
        context_state = self._context_manager.update_from_messages(
            session_id=session_id,
            messages=messages,
            model=model or self._config.model,
        )
        rlm_context.context_state = context_state

        # Only retrieve if auto-retrieve is enabled
        if self._config.rlm.auto_retrieve:
            retrieved = self._retriever.retrieve_for_query(
                query=user_query,
                session_id=session_id,
            )

            if not retrieved.is_empty:
                rlm_context.retrieved_context = retrieved
                rlm_context.system_injection = retrieved.to_system_message()
                logger.info(
                    f"Retrieved {len(retrieved.blocks)} context blocks "
                    f"({retrieved.total_tokens} tokens) for query"
                )

        return rlm_context

    def get_augmented_messages(
        self,
        messages: list[Message],
        rlm_context: RLMContext,
    ) -> list[Message]:
        """
        Get messages augmented with RLM context.

        Adds retrieved context as a system message if available.

        Args:
            messages: Original conversation messages
            rlm_context: RLM context from prepare_for_query

        Returns:
            Messages with context injection if applicable
        """
        if not rlm_context.has_retrieved_context:
            return messages

        # Create system message with archived context
        context_message = Message(
            id="rlm_context",
            session_id=rlm_context.session_id,
            role=MessageRole.SYSTEM,
            parts=[
                MessagePart(
                    id="rlm_context_part",
                    message_id="rlm_context",
                    type=PartType.TEXT,
                    content={"text": rlm_context.system_injection},
                )
            ],
        )

        # Insert after any existing system messages
        augmented = []
        system_added = False

        for msg in messages:
            augmented.append(msg)
            # Add context after last system message
            if msg.role == MessageRole.SYSTEM and not system_added:
                augmented.append(context_message)
                system_added = True

        # If no system messages, add at the beginning
        if not system_added:
            augmented.insert(0, context_message)

        return augmented

    def after_response(
        self,
        session_id: str,
        assistant_message: Message,
        model: str | None = None,
    ) -> ContextState:
        """
        Call after receiving a response from the provider.

        Updates token tracking with the new assistant message.

        Args:
            session_id: Session ID
            assistant_message: The assistant's response
            model: Model used

        Returns:
            Updated context state
        """
        return self._context_manager.add_message(
            session_id=session_id,
            message=assistant_message,
            model=model,
        )

    def force_compact(self, session_id: str) -> bool:
        """
        Force compaction of a session.

        Archives oldest messages immediately.

        Args:
            session_id: Session to compact

        Returns:
            True if compaction succeeded
        """
        result = self._archiver.archive_oldest(session_id)
        return result.success

    def get_context_state(self, session_id: str) -> ContextState:
        """Get current context state for a session."""
        return self._context_manager.get_state(session_id)

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None


def get_rlm_handler() -> RLMHandler:
    """Get the global RLM handler instance."""
    return RLMHandler()


# Convenience functions for common operations


def prepare_messages_with_rlm(
    session_id: str,
    user_query: str,
    messages: list[Message],
    model: str | None = None,
) -> tuple[list[Message], RLMContext]:
    """
    Prepare messages with RLM context injection.

    This is the main integration point for RLM in the conversation flow.

    Args:
        session_id: Current session ID
        user_query: User's query text
        messages: Current conversation messages
        model: Model being used

    Returns:
        Tuple of (augmented_messages, rlm_context)
    """
    handler = get_rlm_handler()
    rlm_context = handler.prepare_for_query(session_id, user_query, messages, model)
    augmented = handler.get_augmented_messages(messages, rlm_context)
    return augmented, rlm_context


def update_after_response(
    session_id: str,
    assistant_message: Message,
    model: str | None = None,
) -> ContextState:
    """
    Update RLM state after receiving a response.

    Args:
        session_id: Session ID
        assistant_message: The assistant's response
        model: Model used

    Returns:
        Updated context state
    """
    return get_rlm_handler().after_response(session_id, assistant_message, model)
