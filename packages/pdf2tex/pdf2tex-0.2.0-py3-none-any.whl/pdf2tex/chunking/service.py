"""
Chunking service coordinating chapter detection and text splitting.
"""

import asyncio
from pathlib import Path
from typing import Any

import structlog

from pdf2tex.chunking.chapter_detector import ChapterDetector
from pdf2tex.chunking.models import (
    Chapter,
    ChapterMetadata,
    Chunk,
    ChunkingResult,
    HeadingLevel,
)
from pdf2tex.chunking.splitter import MathAwareTextSplitter, TextSplitter
from pdf2tex.config import ChunkingSettings, Settings
from pdf2tex.extraction.models import ExtractionResult, ExtractedPage

logger = structlog.get_logger(__name__)


class ChunkingService:
    """
    Orchestrates document chunking.
    
    Combines chapter detection with text splitting to create
    a hierarchical chunk structure.
    """

    def __init__(
        self,
        settings: Settings | None = None,
    ) -> None:
        """
        Initialize chunking service.

        Args:
            settings: Application settings
        """
        self.settings = settings or Settings()
        self.chunking_settings: ChunkingSettings = self.settings.chunking

        # Initialize components
        self._chapter_detector = ChapterDetector(
            use_toc=self.chunking_settings.use_toc,
            use_font_analysis=self.chunking_settings.use_font_analysis,
        )

        self._splitter = MathAwareTextSplitter(
            chunk_size=self.chunking_settings.chunk_size,
            chunk_overlap=self.chunking_settings.chunk_overlap,
            min_chunk_size=self.chunking_settings.min_chunk_size,
        )

    async def chunk_document(
        self,
        extraction: ExtractionResult,
    ) -> ChunkingResult:
        """
        Chunk an extracted document.

        Args:
            extraction: PDF extraction result

        Returns:
            Chunking result with chapters and chunks
        """
        document_id = extraction.source_path.stem
        
        logger.info(
            "Starting chunking",
            document_id=document_id,
            pages=len(extraction.pages),
        )

        # Detect chapters
        chapter_metas = self._chapter_detector.detect_chapters(extraction)
        
        # Get page ranges for chapters
        page_ranges = self._chapter_detector.get_page_ranges(
            chapter_metas, len(extraction.pages)
        )

        # Process chapters
        chapters: list[Chapter] = []
        all_chunks: list[Chunk] = []

        for chapter_meta, (start_page, end_page) in zip(chapter_metas, page_ranges):
            # Get pages for this chapter
            chapter_pages = extraction.pages[start_page : end_page + 1]
            
            if not chapter_pages:
                continue

            # Build section path
            section_path = self._build_section_path(chapter_meta, chapter_metas)

            # Chunk chapter content
            chunks = await asyncio.to_thread(
                self._splitter.split_with_math,
                chapter_pages,
                document_id,
                chapter_meta.chapter_id,
            )

            # Update section path in chunks
            for chunk in chunks:
                chunk.metadata.section_path = section_path

            # Build chapter content
            chapter_content = "\n\n".join(c.content for c in chunks)

            chapter = Chapter(
                title=chapter_meta.title,
                content=chapter_content,
                chunks=chunks,
                metadata=chapter_meta,
            )

            # Only add top-level chapters to list
            if chapter_meta.parent_id is None:
                chapters.append(chapter)
            else:
                # Find parent and add as child
                parent = self._find_chapter(chapters, chapter_meta.parent_id)
                if parent:
                    parent.children.append(chapter)
                else:
                    chapters.append(chapter)

            all_chunks.extend(chunks)

        result = ChunkingResult(
            document_id=document_id,
            source_path=extraction.source_path,
            chapters=chapters,
            all_chunks=all_chunks,
            metadata={
                "total_pages": len(extraction.pages),
                "total_chunks": len(all_chunks),
                "total_chapters": len(chapters),
                "chunk_settings": {
                    "chunk_size": self.chunking_settings.chunk_size,
                    "chunk_overlap": self.chunking_settings.chunk_overlap,
                },
            },
        )

        logger.info(
            "Chunking complete",
            chapters=len(chapters),
            chunks=len(all_chunks),
        )

        return result

    def _build_section_path(
        self,
        chapter_meta: ChapterMetadata,
        all_chapters: list[ChapterMetadata],
    ) -> list[str]:
        """Build section path for chapter."""
        path: list[str] = []
        current = chapter_meta

        while current:
            path.insert(0, current.title)
            if current.parent_id:
                current = next(
                    (c for c in all_chapters if c.chapter_id == current.parent_id),
                    None,  # type: ignore
                )
            else:
                break

        return path

    def _find_chapter(
        self,
        chapters: list[Chapter],
        chapter_id: str,
    ) -> Chapter | None:
        """Find chapter by ID in hierarchy."""
        for chapter in chapters:
            if chapter.id == chapter_id:
                return chapter
            found = self._find_chapter(chapter.children, chapter_id)
            if found:
                return found
        return None

    async def chunk_pages(
        self,
        pages: list[ExtractedPage],
        document_id: str,
    ) -> list[Chunk]:
        """
        Chunk pages without chapter detection.

        Args:
            pages: List of extracted pages
            document_id: Document identifier

        Returns:
            List of chunks
        """
        chunks = await asyncio.to_thread(
            self._splitter.split_pages,
            pages,
            document_id,
        )
        return chunks

    def chunk_text(
        self,
        text: str,
        document_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        """
        Chunk raw text.

        Args:
            text: Text to chunk
            document_id: Document identifier
            metadata: Optional metadata

        Returns:
            List of chunks
        """
        chunks = self._splitter.split_text(text, document_id)
        
        if metadata:
            for chunk in chunks:
                chunk.metadata.extra.update(metadata)

        return chunks

    def estimate_chunks(
        self,
        char_count: int,
    ) -> int:
        """
        Estimate number of chunks for character count.

        Args:
            char_count: Total character count

        Returns:
            Estimated chunk count
        """
        effective_size = self.chunking_settings.chunk_size - self.chunking_settings.chunk_overlap
        return max(1, char_count // effective_size)

    def get_status(self) -> dict[str, Any]:
        """Get service status."""
        return {
            "settings": {
                "chunk_size": self.chunking_settings.chunk_size,
                "chunk_overlap": self.chunking_settings.chunk_overlap,
                "min_chunk_size": self.chunking_settings.min_chunk_size,
                "use_toc": self.chunking_settings.use_toc,
            },
        }
