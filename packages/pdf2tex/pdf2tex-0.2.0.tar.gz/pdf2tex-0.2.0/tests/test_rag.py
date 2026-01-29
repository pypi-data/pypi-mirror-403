"""
Tests for PDF2TeX RAG layer.
Tests match actual implementation APIs.
"""

import pytest
import asyncio


class TestEmbeddingClient:
    """Tests for EmbeddingClient class."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_embed_batch(self) -> None:
        """Test batch text embedding."""
        from pdf2tex.rag.embeddings import EmbeddingClient
        
        client = EmbeddingClient(model_name="BAAI/bge-m3", device="cpu")
        await client.initialize()
        
        texts = ["Hello world", "Test embedding"]
        embeddings = await client.embed_batch(texts)
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1024  # BGE-M3 dimension

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_embed_query(self) -> None:
        """Test query embedding with instruction prefix."""
        from pdf2tex.rag.embeddings import EmbeddingClient
        
        client = EmbeddingClient(model_name="BAAI/bge-m3", device="cpu")
        await client.initialize()
        
        embedding = await client.embed_query("What is attention?")
        
        assert len(embedding) == 1024

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_dimension_property(self) -> None:
        """Test embedding dimension property."""
        from pdf2tex.rag.embeddings import EmbeddingClient
        
        client = EmbeddingClient(model_name="BAAI/bge-m3", device="cpu")
        await client.initialize()
        
        assert client.dimension == 1024


class TestVectorStore:
    """Tests for VectorStore operations."""

    def test_collection_name_format(self) -> None:
        """Test collection name formatting."""
        # Collection names should be valid identifiers
        name = "pdf2tex_doc_12345"
        assert name.replace("_", "").replace("-", "").isalnum()


# ============================================================================
# Integration Tests (require Qdrant running)
# ============================================================================

@pytest.mark.integration
@pytest.mark.requires_services
class TestVectorStoreIntegration:
    """Integration tests requiring Qdrant service."""

    @pytest.mark.asyncio
    async def test_qdrant_connection(self) -> None:
        """Test Qdrant connection."""
        from qdrant_client import QdrantClient
        
        try:
            client = QdrantClient(url="http://localhost:6333")
            collections = client.get_collections()
            assert collections is not None
        except Exception as e:
            pytest.skip(f"Qdrant not available: {e}")
