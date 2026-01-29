"""
RAG layer for PDF2TeX.

Handles embeddings, vector storage, and retrieval.
"""

from pdf2tex.rag.embeddings import EmbeddingClient
from pdf2tex.rag.reranker import Reranker
from pdf2tex.rag.service import RAGService
from pdf2tex.rag.vectorstore import VectorStore

__all__ = [
    "EmbeddingClient",
    "Reranker",
    "VectorStore",
    "RAGService",
]
