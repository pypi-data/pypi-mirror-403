"""
Cross-encoder reranker for search results.

Improves retrieval quality by reranking initial results.
"""

import asyncio
from dataclasses import dataclass
from typing import Any

import structlog

from pdf2tex.rag.vectorstore import SearchResult

logger = structlog.get_logger(__name__)


@dataclass
class RankedResult:
    """Reranked search result."""

    result: SearchResult
    rerank_score: float
    original_rank: int


class Reranker:
    """
    Cross-encoder reranker using sentence-transformers.
    
    Provides more accurate relevance scoring than embedding
    similarity alone.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "cuda",
        batch_size: int = 32,
    ) -> None:
        """
        Initialize reranker.

        Args:
            model_name: HuggingFace cross-encoder model
            device: Device to use
            batch_size: Batch size for inference
        """
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size

        self._model = None

    async def initialize(self) -> None:
        """Initialize the cross-encoder model."""
        await asyncio.to_thread(self._load_model)

    def _load_model(self) -> None:
        """Load the cross-encoder model."""
        try:
            from sentence_transformers import CrossEncoder
            import torch

            logger.info(
                "Loading cross-encoder model",
                model=self.model_name,
                device=self.device,
            )

            # Check CUDA availability
            if self.device.startswith("cuda") and not torch.cuda.is_available():
                self.device = "cpu"
                logger.warning("CUDA not available, using CPU")

            self._model = CrossEncoder(
                self.model_name,
                max_length=512,
                device=self.device,
            )

            logger.info("Cross-encoder model loaded", device=self.device)

        except Exception as e:
            logger.error("Failed to load cross-encoder", error=str(e))
            raise

    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int | None = None,
    ) -> list[RankedResult]:
        """
        Rerank search results.

        Args:
            query: Search query
            results: Initial search results
            top_k: Number of results to return

        Returns:
            Reranked results
        """
        if self._model is None:
            await self.initialize()

        if not results:
            return []

        return await asyncio.to_thread(self._rerank_sync, query, results, top_k)

    def _rerank_sync(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int | None,
    ) -> list[RankedResult]:
        """Rerank synchronously."""
        # Create query-document pairs
        pairs = [(query, result.chunk.content) for result in results]

        # Score pairs
        scores = self._model.predict(pairs, batch_size=self.batch_size)

        # Create ranked results
        ranked: list[RankedResult] = []
        for i, (result, score) in enumerate(zip(results, scores)):
            ranked.append(
                RankedResult(
                    result=result,
                    rerank_score=float(score),
                    original_rank=i + 1,
                )
            )

        # Sort by rerank score
        ranked.sort(key=lambda x: x.rerank_score, reverse=True)

        # Apply top_k
        if top_k:
            ranked = ranked[:top_k]

        return ranked

    async def rerank_chunks(
        self,
        query: str,
        chunks: list[Any],
        content_getter: Any = None,
        top_k: int | None = None,
    ) -> list[tuple[Any, float]]:
        """
        Rerank arbitrary chunks.

        Args:
            query: Search query
            chunks: List of chunk objects
            content_getter: Function to get content from chunk
            top_k: Number of results

        Returns:
            List of (chunk, score) tuples
        """
        if self._model is None:
            await self.initialize()

        if not chunks:
            return []

        # Get content
        if content_getter is None:
            content_getter = lambda x: x.content if hasattr(x, "content") else str(x)

        pairs = [(query, content_getter(chunk)) for chunk in chunks]
        scores = await asyncio.to_thread(
            self._model.predict, pairs, batch_size=self.batch_size
        )

        # Create result pairs
        results = list(zip(chunks, [float(s) for s in scores]))
        results.sort(key=lambda x: x[1], reverse=True)

        if top_k:
            results = results[:top_k]

        return results

    def score_pair(self, query: str, document: str) -> float:
        """
        Score a single query-document pair.

        Args:
            query: Query text
            document: Document text

        Returns:
            Relevance score
        """
        if self._model is None:
            raise RuntimeError("Model not initialized")

        score = self._model.predict([(query, document)])
        return float(score[0])

    async def score_pair_async(self, query: str, document: str) -> float:
        """Async version of score_pair."""
        if self._model is None:
            await self.initialize()
        return await asyncio.to_thread(self.score_pair, query, document)

    def get_info(self) -> dict[str, Any]:
        """Get reranker information."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "batch_size": self.batch_size,
            "initialized": self._model is not None,
        }


class MathAwareReranker(Reranker):
    """
    Reranker with enhanced handling for mathematical content.
    
    Boosts scores for results containing mathematical expressions
    when the query appears to be math-related.
    """

    MATH_QUERY_INDICATORS = [
        "equation",
        "formula",
        "theorem",
        "proof",
        "lemma",
        "definition",
        "derivative",
        "integral",
        "matrix",
        "vector",
        "function",
        "calculate",
        "solve",
    ]

    def __init__(
        self,
        math_boost: float = 0.1,
        **kwargs: Any,
    ) -> None:
        """
        Initialize math-aware reranker.

        Args:
            math_boost: Score boost for math content
            **kwargs: Arguments for Reranker
        """
        super().__init__(**kwargs)
        self.math_boost = math_boost

    def _is_math_query(self, query: str) -> bool:
        """Check if query is math-related."""
        query_lower = query.lower()
        return any(
            indicator in query_lower
            for indicator in self.MATH_QUERY_INDICATORS
        )

    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int | None = None,
    ) -> list[RankedResult]:
        """Rerank with math awareness."""
        ranked = await super().rerank(query, results, top_k=None)

        # Apply math boost if query is math-related
        if self._is_math_query(query):
            for item in ranked:
                if item.result.chunk.metadata.has_math:
                    item.rerank_score += self.math_boost

            # Re-sort after boost
            ranked.sort(key=lambda x: x.rerank_score, reverse=True)

        if top_k:
            ranked = ranked[:top_k]

        return ranked
