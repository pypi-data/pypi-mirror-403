"""
Context search system for RLM.

Provides keyword and semantic search across archived context blocks.
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Any, Literal

from opencode.config.settings import get_config
from opencode.config.storage import ContextBlock, get_storage

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A search result with relevance score."""

    block: ContextBlock
    score: float
    match_type: Literal["keyword", "semantic", "hybrid"]
    highlights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_id": self.block.id,
            "session_id": self.block.session_id,
            "task_id": self.block.task_id,
            "task_description": self.block.task_description,
            "summary": self.block.summary,
            "score": self.score,
            "match_type": self.match_type,
            "highlights": self.highlights,
            "tokens": self.block.tokens,
            "created_at": self.block.created_at.isoformat(),
        }


class KeywordSearcher:
    """Simple keyword-based search."""

    def search(
        self,
        query: str,
        blocks: list[ContextBlock],
        limit: int = 10,
    ) -> list[SearchResult]:
        """
        Search blocks using keyword matching.

        Args:
            query: Search query
            blocks: Blocks to search
            limit: Maximum results

        Returns:
            Sorted search results
        """
        if not query or not blocks:
            return []

        # Tokenize query
        query_terms = self._tokenize(query.lower())
        if not query_terms:
            return []

        results = []

        for block in blocks:
            score, highlights = self._score_block(block, query_terms)
            if score > 0:
                results.append(
                    SearchResult(
                        block=block,
                        score=score,
                        match_type="keyword",
                        highlights=highlights,
                    )
                )

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def _tokenize(self, text: str) -> list[str]:
        """Extract search terms from text."""
        # Remove punctuation and split
        words = re.findall(r"\b\w+\b", text.lower())
        # Filter short words and stopwords
        stopwords = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "all",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "just",
            "and",
            "but",
            "if",
            "or",
            "because",
            "until",
            "while",
            "this",
            "that",
            "these",
            "those",
        }
        return [w for w in words if len(w) > 2 and w not in stopwords]

    def _score_block(
        self,
        block: ContextBlock,
        query_terms: list[str],
    ) -> tuple[float, list[str]]:
        """Score a block against query terms."""
        # Combine searchable text
        text = " ".join(
            [
                block.task_description,
                block.summary,
                block.content,
            ]
        ).lower()

        text_terms = set(self._tokenize(text))

        # Calculate term frequency
        matches = 0
        highlights = []

        for term in query_terms:
            if term in text_terms:
                matches += 1
                # Find context around match
                highlight = self._extract_highlight(block.content, term)
                if highlight:
                    highlights.append(highlight)

        if matches == 0:
            return 0.0, []

        # Score based on:
        # - Percentage of query terms matched
        # - Bonus for task description matches
        # - Recency bonus

        base_score = matches / len(query_terms)

        # Bonus for task description match
        task_text = block.task_description.lower()
        if any(term in task_text for term in query_terms):
            base_score *= 1.5

        return min(1.0, base_score), highlights[:3]

    def _extract_highlight(self, content: str, term: str, context: int = 50) -> str:
        """Extract a snippet around a matching term."""
        lower_content = content.lower()
        idx = lower_content.find(term)
        if idx == -1:
            return ""

        start = max(0, idx - context)
        end = min(len(content), idx + len(term) + context)

        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet


class SemanticSearcher:
    """
    Semantic search using embeddings.

    Falls back to keyword search if embeddings are not available.
    """

    def __init__(self) -> None:
        self._embeddings_cache: dict[str, list[float]] = {}
        self._embedding_model: str | None = None
        self._keyword_searcher = KeywordSearcher()

    async def search(
        self,
        query: str,
        blocks: list[ContextBlock],
        limit: int = 10,
    ) -> list[SearchResult]:
        """
        Search blocks using semantic similarity.

        Args:
            query: Search query
            blocks: Blocks to search
            limit: Maximum results

        Returns:
            Sorted search results
        """
        config = get_config()

        # Check if semantic search is enabled
        if not config.rlm.semantic_search.get("enabled", False):
            # Fall back to keyword search
            return self._keyword_searcher.search(query, blocks, limit)

        # For now, use keyword search as semantic requires external embedding API
        # TODO: Implement actual embedding-based search when embedding provider is available
        logger.debug("Semantic search falling back to keyword search")
        return self._keyword_searcher.search(query, blocks, limit)

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)


class ContextSearcher:
    """
    Main search interface supporting hybrid search.

    Combines keyword and semantic search with configurable weights.
    """

    def __init__(self) -> None:
        self._storage = get_storage()
        self._keyword_searcher = KeywordSearcher()
        self._semantic_searcher = SemanticSearcher()

    def search(
        self,
        query: str,
        session_id: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """
        Search archived context blocks.

        Args:
            query: Search query
            session_id: Optional session filter
            limit: Maximum results

        Returns:
            Search results sorted by relevance
        """
        # Get all blocks (or filtered by session)
        blocks = self._storage.get_context_blocks(session_id=session_id, limit=1000)

        if not blocks:
            return []

        # Perform keyword search
        keyword_results = self._keyword_searcher.search(query, blocks, limit * 2)

        # For now, return keyword results
        # TODO: Implement hybrid search when semantic is available
        return keyword_results[:limit]

    async def search_async(
        self,
        query: str,
        session_id: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Async search with semantic support."""
        blocks = self._storage.get_context_blocks(session_id=session_id, limit=1000)

        if not blocks:
            return []

        config = get_config()
        weights = config.rlm.semantic_search.get(
            "hybrid_weights",
            {"keyword": 0.3, "semantic": 0.7},
        )

        # Get results from both searchers
        keyword_results = self._keyword_searcher.search(query, blocks, limit * 2)
        semantic_results = await self._semantic_searcher.search(query, blocks, limit * 2)

        # Merge results with weighted scores
        return self._merge_results(
            keyword_results,
            semantic_results,
            keyword_weight=weights.get("keyword", 0.3),
            semantic_weight=weights.get("semantic", 0.7),
            limit=limit,
        )

    def _merge_results(
        self,
        keyword_results: list[SearchResult],
        semantic_results: list[SearchResult],
        keyword_weight: float,
        semantic_weight: float,
        limit: int,
    ) -> list[SearchResult]:
        """Merge keyword and semantic results with weights."""
        # Create score map by block ID
        scores: dict[str, tuple[ContextBlock, float, list[str]]] = {}

        for result in keyword_results:
            block_id = result.block.id
            weighted_score = result.score * keyword_weight
            scores[block_id] = (result.block, weighted_score, result.highlights)

        for result in semantic_results:
            block_id = result.block.id
            weighted_score = result.score * semantic_weight

            if block_id in scores:
                block, existing_score, highlights = scores[block_id]
                scores[block_id] = (
                    block,
                    existing_score + weighted_score,
                    highlights + result.highlights,
                )
            else:
                scores[block_id] = (result.block, weighted_score, result.highlights)

        # Create merged results
        merged = [
            SearchResult(
                block=block,
                score=score,
                match_type="hybrid",
                highlights=list(set(highlights))[:3],
            )
            for block, score, highlights in scores.values()
        ]

        # Sort by score
        merged.sort(key=lambda r: r.score, reverse=True)
        return merged[:limit]

    def get_recent(self, session_id: str | None = None, limit: int = 10) -> list[ContextBlock]:
        """Get most recent archived blocks."""
        return self._storage.get_context_blocks(session_id=session_id, limit=limit)

    def get_by_task(self, task_id: str) -> ContextBlock | None:
        """Get archived block for a specific task."""
        blocks = self._storage.get_context_blocks(limit=1000)
        for block in blocks:
            if block.task_id == task_id:
                return block
        return None


# Global searcher instance
_searcher: ContextSearcher | None = None


def get_searcher() -> ContextSearcher:
    """Get the global searcher instance."""
    global _searcher
    if _searcher is None:
        _searcher = ContextSearcher()
    return _searcher
