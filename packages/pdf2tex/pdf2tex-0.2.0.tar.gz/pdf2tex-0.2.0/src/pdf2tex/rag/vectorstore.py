"""
Vector store implementation using Qdrant.

Provides semantic search capabilities over document chunks.
"""

import asyncio
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import structlog

from pdf2tex.chunking.models import Chunk

logger = structlog.get_logger(__name__)


@dataclass
class SearchResult:
    """Result from vector search."""

    chunk: Chunk
    score: float
    metadata: dict[str, Any]


class VectorStore:
    """
    Vector store using Qdrant for semantic search.
    
    Features:
    - Efficient HNSW indexing
    - Hybrid search support
    - Filtering by metadata
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "pdf2tex",
        embedding_dimension: int = 1024,
        distance_metric: str = "cosine",
    ) -> None:
        """
        Initialize vector store.

        Args:
            host: Qdrant server host
            port: Qdrant server port
            collection_name: Name of the collection
            embedding_dimension: Dimension of embeddings
            distance_metric: Distance metric (cosine, euclidean, dot)
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.embedding_dimension = embedding_dimension
        self.distance_metric = distance_metric

        self._client = None

    async def initialize(self) -> None:
        """Initialize connection to Qdrant."""
        await asyncio.to_thread(self._connect)

    def _connect(self) -> None:
        """Connect to Qdrant server."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            logger.info(
                "Connecting to Qdrant",
                host=self.host,
                port=self.port,
            )

            self._client = QdrantClient(host=self.host, port=self.port)

            # Create collection if not exists
            collections = self._client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                distance = {
                    "cosine": Distance.COSINE,
                    "euclidean": Distance.EUCLID,
                    "dot": Distance.DOT,
                }.get(self.distance_metric, Distance.COSINE)

                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=distance,
                    ),
                )
                logger.info(
                    "Created collection",
                    name=self.collection_name,
                    dimension=self.embedding_dimension,
                )
            else:
                logger.info("Using existing collection", name=self.collection_name)

        except Exception as e:
            logger.error("Failed to connect to Qdrant", error=str(e))
            raise

    async def add_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> list[str]:
        """
        Add chunks to the vector store.

        Args:
            chunks: List of chunks
            embeddings: Corresponding embeddings

        Returns:
            List of point IDs
        """
        if self._client is None:
            await self.initialize()

        return await asyncio.to_thread(self._add_chunks_sync, chunks, embeddings)

    def _add_chunks_sync(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> list[str]:
        """Add chunks synchronously."""
        from qdrant_client.models import PointStruct

        points: list[PointStruct] = []
        point_ids: list[str] = []

        for chunk, embedding in zip(chunks, embeddings):
            point_id = str(uuid4())
            point_ids.append(point_id)

            payload = {
                "chunk_id": chunk.id,
                "document_id": chunk.metadata.document_id,
                "chapter_id": chunk.metadata.chapter_id,
                "content": chunk.content,
                "page_numbers": chunk.metadata.page_numbers,
                "section_path": chunk.metadata.section_path,
                "chunk_type": chunk.metadata.chunk_type.value,
                "has_math": chunk.metadata.has_math,
                "char_count": chunk.metadata.char_count,
            }

            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload,
                )
            )

        self._client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        logger.info("Added chunks to vector store", count=len(chunks))
        return point_ids

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filter_dict: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[SearchResult]:
        """
        Search for similar chunks.

        Args:
            query_embedding: Query vector
            top_k: Number of results
            filter_dict: Optional metadata filter
            score_threshold: Minimum score threshold

        Returns:
            List of search results
        """
        if self._client is None:
            await self.initialize()

        return await asyncio.to_thread(
            self._search_sync,
            query_embedding,
            top_k,
            filter_dict,
            score_threshold,
        )

    def _search_sync(
        self,
        query_embedding: list[float],
        top_k: int,
        filter_dict: dict[str, Any] | None,
        score_threshold: float | None,
    ) -> list[SearchResult]:
        """Search synchronously."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        # Build filter
        qdrant_filter = None
        if filter_dict:
            conditions = []
            for key, value in filter_dict.items():
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            qdrant_filter = Filter(must=conditions)

        # Search
        results = self._client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=qdrant_filter,
            score_threshold=score_threshold,
        )

        # Convert to SearchResult
        search_results: list[SearchResult] = []
        for result in results:
            payload = result.payload or {}
            
            # Reconstruct chunk from payload
            from pdf2tex.chunking.models import ChunkMetadata, ChunkType
            
            metadata = ChunkMetadata(
                chunk_id=payload.get("chunk_id", ""),
                document_id=payload.get("document_id", ""),
                chapter_id=payload.get("chapter_id"),
                section_path=payload.get("section_path", []),
                page_numbers=payload.get("page_numbers", []),
                chunk_type=ChunkType(payload.get("chunk_type", "paragraph")),
                has_math=payload.get("has_math", False),
                char_count=payload.get("char_count", 0),
            )

            chunk = Chunk(
                content=payload.get("content", ""),
                metadata=metadata,
            )

            search_results.append(
                SearchResult(
                    chunk=chunk,
                    score=result.score,
                    metadata=payload,
                )
            )

        return search_results

    async def search_by_document(
        self,
        query_embedding: list[float],
        document_id: str,
        top_k: int = 10,
    ) -> list[SearchResult]:
        """
        Search within a specific document.

        Args:
            query_embedding: Query vector
            document_id: Document to search in
            top_k: Number of results

        Returns:
            List of search results
        """
        return await self.search(
            query_embedding,
            top_k=top_k,
            filter_dict={"document_id": document_id},
        )

    async def search_by_chapter(
        self,
        query_embedding: list[float],
        chapter_id: str,
        top_k: int = 10,
    ) -> list[SearchResult]:
        """
        Search within a specific chapter.

        Args:
            query_embedding: Query vector
            chapter_id: Chapter to search in
            top_k: Number of results

        Returns:
            List of search results
        """
        return await self.search(
            query_embedding,
            top_k=top_k,
            filter_dict={"chapter_id": chapter_id},
        )

    async def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document identifier

        Returns:
            Number of deleted points
        """
        if self._client is None:
            await self.initialize()

        return await asyncio.to_thread(self._delete_document_sync, document_id)

    def _delete_document_sync(self, document_id: str) -> int:
        """Delete document synchronously."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        result = self._client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
        )

        logger.info("Deleted document from vector store", document_id=document_id)
        return result.status.value if hasattr(result.status, "value") else 0

    async def get_collection_info(self) -> dict[str, Any]:
        """Get collection statistics."""
        if self._client is None:
            await self.initialize()

        return await asyncio.to_thread(self._get_info_sync)

    def _get_info_sync(self) -> dict[str, Any]:
        """Get info synchronously."""
        info = self._client.get_collection(self.collection_name)
        return {
            "name": self.collection_name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": info.status.value,
            "dimension": self.embedding_dimension,
        }

    async def close(self) -> None:
        """Close connection."""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Vector store connection closed")
