"""
RAG service coordinating retrieval operations.
"""

import asyncio
from dataclasses import dataclass
from typing import Any

import structlog

from pdf2tex.chunking.models import Chunk, ChunkingResult
from pdf2tex.config import RAGSettings, Settings
from pdf2tex.rag.embeddings import CachedEmbeddingClient, EmbeddingClient
from pdf2tex.rag.reranker import MathAwareReranker, RankedResult, Reranker
from pdf2tex.rag.vectorstore import SearchResult, VectorStore

logger = structlog.get_logger(__name__)


@dataclass
class RetrievalResult:
    """Result of retrieval operation."""

    query: str
    results: list[RankedResult]
    total_candidates: int
    metadata: dict[str, Any]


class RAGService:
    """
    Retrieval-Augmented Generation service.
    
    Coordinates:
    - Embedding generation
    - Vector storage
    - Semantic search
    - Result reranking
    """

    def __init__(
        self,
        settings: Settings | None = None,
    ) -> None:
        """
        Initialize RAG service.

        Args:
            settings: Application settings
        """
        self.settings = settings or Settings()
        self.rag_settings: RAGSettings = self.settings.rag

        # Initialize components
        self._embedding_client: EmbeddingClient | None = None
        self._vector_store: VectorStore | None = None
        self._reranker: Reranker | None = None
        
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all RAG components."""
        if self._initialized:
            return

        logger.info("Initializing RAG service")

        # Initialize embedding client
        self._embedding_client = CachedEmbeddingClient(
            model_name=self.rag_settings.embedding_model,
            device=self.rag_settings.device,
            batch_size=self.rag_settings.embedding_batch_size,
        )
        await self._embedding_client.initialize()

        # Initialize vector store
        self._vector_store = VectorStore(
            host=self.rag_settings.qdrant_host,
            port=self.rag_settings.qdrant_port,
            collection_name=self.rag_settings.collection_name,
            embedding_dimension=self._embedding_client.dimension,
        )
        await self._vector_store.initialize()

        # Initialize reranker
        if self.rag_settings.use_reranker:
            self._reranker = MathAwareReranker(
                model_name=self.rag_settings.reranker_model,
                device=self.rag_settings.device,
            )
            await self._reranker.initialize()

        self._initialized = True
        logger.info("RAG service initialized")

    async def index_document(
        self,
        chunking_result: ChunkingResult,
        progress_callback: Any | None = None,
    ) -> dict[str, Any]:
        """
        Index a chunked document.

        Args:
            chunking_result: Chunking result with all chunks
            progress_callback: Optional progress callback

        Returns:
            Indexing statistics
        """
        if not self._initialized:
            await self.initialize()

        chunks = chunking_result.all_chunks
        document_id = chunking_result.document_id

        logger.info(
            "Indexing document",
            document_id=document_id,
            chunks=len(chunks),
        )

        # Generate embeddings in batches
        batch_size = self.rag_settings.embedding_batch_size
        all_embeddings: list[list[float]] = []

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [chunk.content for chunk in batch]

            if progress_callback:
                await progress_callback({
                    "phase": "embedding",
                    "current": i,
                    "total": len(chunks),
                })

            embeddings = await self._embedding_client.embed_batch(texts)
            all_embeddings.extend(embeddings)

        # Store in vector store
        point_ids = await self._vector_store.add_chunks(chunks, all_embeddings)

        stats = {
            "document_id": document_id,
            "chunks_indexed": len(chunks),
            "point_ids": len(point_ids),
        }

        logger.info("Document indexed", **stats)
        return stats

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        document_id: str | None = None,
        chapter_id: str | None = None,
        rerank: bool = True,
    ) -> RetrievalResult:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: Search query
            top_k: Number of results
            document_id: Optional document filter
            chapter_id: Optional chapter filter
            rerank: Whether to rerank results

        Returns:
            Retrieval result
        """
        if not self._initialized:
            await self.initialize()

        # Generate query embedding
        query_embedding = await self._embedding_client.embed_query(query)

        # Build filter
        filter_dict: dict[str, Any] | None = None
        if document_id or chapter_id:
            filter_dict = {}
            if document_id:
                filter_dict["document_id"] = document_id
            if chapter_id:
                filter_dict["chapter_id"] = chapter_id

        # Initial retrieval (get more for reranking)
        retrieval_k = top_k * 3 if rerank and self._reranker else top_k
        search_results = await self._vector_store.search(
            query_embedding,
            top_k=retrieval_k,
            filter_dict=filter_dict,
        )

        # Rerank if enabled
        if rerank and self._reranker and search_results:
            ranked_results = await self._reranker.rerank(
                query, search_results, top_k=top_k
            )
        else:
            ranked_results = [
                RankedResult(
                    result=r,
                    rerank_score=r.score,
                    original_rank=i + 1,
                )
                for i, r in enumerate(search_results[:top_k])
            ]

        return RetrievalResult(
            query=query,
            results=ranked_results,
            total_candidates=len(search_results),
            metadata={
                "document_id": document_id,
                "chapter_id": chapter_id,
                "reranked": rerank and self._reranker is not None,
            },
        )

    async def retrieve_for_chapter(
        self,
        chapter_content: str,
        document_id: str,
        top_k: int = 20,
    ) -> list[Chunk]:
        """
        Retrieve relevant context for generating a chapter.

        Args:
            chapter_content: Chapter content for context
            document_id: Document to search in
            top_k: Number of results

        Returns:
            List of relevant chunks
        """
        # Extract key sentences for querying
        queries = self._extract_queries(chapter_content)

        all_chunks: dict[str, Chunk] = {}
        chunk_scores: dict[str, float] = {}

        for query in queries:
            result = await self.retrieve(
                query,
                top_k=top_k // len(queries) + 1,
                document_id=document_id,
                rerank=True,
            )

            for ranked in result.results:
                chunk_id = ranked.result.chunk.id
                if chunk_id not in all_chunks:
                    all_chunks[chunk_id] = ranked.result.chunk
                    chunk_scores[chunk_id] = ranked.rerank_score
                else:
                    # Combine scores
                    chunk_scores[chunk_id] = max(
                        chunk_scores[chunk_id], ranked.rerank_score
                    )

        # Sort by combined score
        sorted_chunks = sorted(
            all_chunks.values(),
            key=lambda c: chunk_scores.get(c.id, 0),
            reverse=True,
        )

        return sorted_chunks[:top_k]

    def _extract_queries(self, text: str, max_queries: int = 5) -> list[str]:
        """Extract key sentences as queries."""
        import re

        # Split into sentences
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        # Take diverse sentences
        if len(sentences) <= max_queries:
            return sentences

        # Sample evenly distributed
        step = len(sentences) // max_queries
        return [sentences[i * step] for i in range(max_queries)]

    async def delete_document(self, document_id: str) -> dict[str, Any]:
        """
        Delete a document from the index.

        Args:
            document_id: Document to delete

        Returns:
            Deletion statistics
        """
        if not self._initialized:
            await self.initialize()

        result = await self._vector_store.delete_document(document_id)
        return {"document_id": document_id, "deleted": True, "result": result}

    async def get_status(self) -> dict[str, Any]:
        """Get service status."""
        status = {
            "initialized": self._initialized,
            "settings": {
                "embedding_model": self.rag_settings.embedding_model,
                "reranker_enabled": self.rag_settings.use_reranker,
                "top_k": self.rag_settings.top_k,
            },
        }

        if self._initialized and self._vector_store:
            collection_info = await self._vector_store.get_collection_info()
            status["collection"] = collection_info

        return status

    async def close(self) -> None:
        """Close all connections."""
        if self._vector_store:
            await self._vector_store.close()
        
        self._embedding_client = None
        self._vector_store = None
        self._reranker = None
        self._initialized = False
        
        logger.info("RAG service closed")
