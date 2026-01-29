"""
Recursive Language Model (RLM) system for unlimited context.

Provides automatic context archival, retrieval, and management
to enable Claude to maintain coherent conversations beyond its
context window limits.
"""

from opencode.rlm.context import ContextManager, TokenCounter, get_context_manager
from opencode.rlm.archive import ContextArchiver, create_archive_block, get_archiver
from opencode.rlm.search import ContextSearcher, SearchResult, get_searcher
from opencode.rlm.retrieve import ContextRetriever, RetrievalContext, get_retriever
from opencode.rlm.handler import (
    RLMHandler,
    RLMContext,
    get_rlm_handler,
    prepare_messages_with_rlm,
    update_after_response,
)

__all__ = [
    # Context management
    "ContextManager",
    "TokenCounter",
    "get_context_manager",
    # Archival
    "ContextArchiver",
    "create_archive_block",
    "get_archiver",
    # Search
    "ContextSearcher",
    "SearchResult",
    "get_searcher",
    # Retrieval
    "ContextRetriever",
    "RetrievalContext",
    "get_retriever",
    # Handler (main integration point)
    "RLMHandler",
    "RLMContext",
    "get_rlm_handler",
    "prepare_messages_with_rlm",
    "update_after_response",
]
