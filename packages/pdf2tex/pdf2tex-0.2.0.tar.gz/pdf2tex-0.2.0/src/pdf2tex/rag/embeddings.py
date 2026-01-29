"""
Embedding client using BGE-M3 model.

Generates dense vector embeddings for text chunks.
"""

import asyncio
from typing import Any

import numpy as np
import structlog

logger = structlog.get_logger(__name__)


class EmbeddingClient:
    """
    Client for generating text embeddings using BGE-M3.
    
    BGE-M3 is a multilingual embedding model that excels at
    scientific and technical content.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str = "cuda",
        max_length: int = 8192,
        batch_size: int = 32,
        normalize: bool = True,
    ) -> None:
        """
        Initialize embedding client.

        Args:
            model_name: HuggingFace model name
            device: Device to use (cuda/cpu)
            max_length: Maximum sequence length
            batch_size: Batch size for encoding
            normalize: Whether to normalize embeddings
        """
        self.model_name = model_name
        self.device = device
        self.max_length = max_length
        self.batch_size = batch_size
        self.normalize = normalize

        self._model = None
        self._tokenizer = None
        self._dimension: int | None = None

    async def initialize(self) -> None:
        """Initialize the embedding model."""
        await asyncio.to_thread(self._load_model)

    def _load_model(self) -> None:
        """Load the embedding model."""
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            logger.info(
                "Loading embedding model",
                model=self.model_name,
                device=self.device,
            )

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModel.from_pretrained(self.model_name)

            # Move to device
            if self.device.startswith("cuda") and torch.cuda.is_available():
                self._model = self._model.to(self.device)
            else:
                self.device = "cpu"
                self._model = self._model.to("cpu")

            self._model.eval()

            # Get embedding dimension
            with torch.no_grad():
                sample = self._tokenizer(
                    "test",
                    return_tensors="pt",
                    max_length=32,
                    truncation=True,
                )
                sample = {k: v.to(self.device) for k, v in sample.items()}
                output = self._model(**sample)
                self._dimension = output.last_hidden_state.shape[-1]

            logger.info(
                "Embedding model loaded",
                dimension=self._dimension,
                device=self.device,
            )

        except Exception as e:
            logger.error("Failed to load embedding model", error=str(e))
            raise

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        if self._dimension is None:
            raise RuntimeError("Model not initialized")
        return self._dimension

    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding for single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        embeddings = await self.embed_batch([text])
        return embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if self._model is None:
            await self.initialize()

        return await asyncio.to_thread(self._embed_sync, texts)

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        """Synchronous embedding generation."""
        import torch

        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]

            # Tokenize
            encoded = self._tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )
            encoded = {k: v.to(self.device) for k, v in encoded.items()}

            # Generate embeddings
            with torch.no_grad():
                outputs = self._model(**encoded)
                
                # Mean pooling
                attention_mask = encoded["attention_mask"]
                token_embeddings = outputs.last_hidden_state
                
                input_mask_expanded = (
                    attention_mask.unsqueeze(-1)
                    .expand(token_embeddings.size())
                    .float()
                )
                sum_embeddings = torch.sum(
                    token_embeddings * input_mask_expanded, dim=1
                )
                sum_mask = torch.clamp(input_mask_expanded.sum(dim=1), min=1e-9)
                embeddings = sum_embeddings / sum_mask

                # Normalize if requested
                if self.normalize:
                    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

                # Convert to list
                batch_embeddings = embeddings.cpu().numpy().tolist()
                all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Search query

        Returns:
            Query embedding
        """
        # BGE-M3 uses instruction prefix for queries
        prefixed_query = f"Represent this sentence for searching relevant passages: {query}"
        return await self.embed(prefixed_query)

    async def similarity(
        self,
        embedding1: list[float],
        embedding2: list[float],
    ) -> float:
        """
        Calculate cosine similarity between embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score (0-1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))

    def get_info(self) -> dict[str, Any]:
        """Get client information."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "dimension": self._dimension,
            "max_length": self.max_length,
            "batch_size": self.batch_size,
            "initialized": self._model is not None,
        }


class CachedEmbeddingClient(EmbeddingClient):
    """
    Embedding client with caching support.
    
    Caches embeddings to avoid recomputation.
    """

    def __init__(self, cache_size: int = 10000, **kwargs: Any) -> None:
        """
        Initialize cached embedding client.

        Args:
            cache_size: Maximum cache entries
            **kwargs: Arguments for EmbeddingClient
        """
        super().__init__(**kwargs)
        self._cache: dict[str, list[float]] = {}
        self._cache_size = cache_size

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()

    async def embed(self, text: str) -> list[float]:
        """Generate embedding with caching."""
        cache_key = self._get_cache_key(text)
        
        if cache_key in self._cache:
            return self._cache[cache_key]

        embedding = await super().embed(text)
        
        # Add to cache with size limit
        if len(self._cache) >= self._cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        self._cache[cache_key] = embedding
        return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings with caching."""
        results: list[list[float] | None] = [None] * len(texts)
        uncached_texts: list[str] = []
        uncached_indices: list[int] = []

        # Check cache
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                results[i] = self._cache[cache_key]
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        # Embed uncached texts
        if uncached_texts:
            new_embeddings = await super().embed_batch(uncached_texts)
            
            for i, (text, embedding) in enumerate(zip(uncached_texts, new_embeddings)):
                original_index = uncached_indices[i]
                results[original_index] = embedding
                
                # Cache result
                cache_key = self._get_cache_key(text)
                if len(self._cache) < self._cache_size:
                    self._cache[cache_key] = embedding

        return [r for r in results if r is not None]  # type: ignore

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()

    @property
    def cache_size(self) -> int:
        """Get current cache size."""
        return len(self._cache)
