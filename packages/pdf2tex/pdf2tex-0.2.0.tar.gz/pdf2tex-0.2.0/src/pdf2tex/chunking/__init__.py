"""
Chunking layer for PDF2TeX.

Handles text splitting and chapter detection for RAG processing.
"""

from pdf2tex.chunking.chapter_detector import ChapterDetector
from pdf2tex.chunking.models import (
    Chapter,
    ChapterMetadata,
    Chunk,
    ChunkingResult,
    ChunkMetadata,
    ChunkType,
    HeadingLevel,
)
from pdf2tex.chunking.service import ChunkingService
from pdf2tex.chunking.splitter import MathAwareTextSplitter, TextSplitter

__all__ = [
    # Models
    "Chapter",
    "ChapterMetadata",
    "Chunk",
    "ChunkingResult",
    "ChunkMetadata",
    "ChunkType",
    "HeadingLevel",
    # Components
    "ChapterDetector",
    "MathAwareTextSplitter",
    "TextSplitter",
    # Service
    "ChunkingService",
]
