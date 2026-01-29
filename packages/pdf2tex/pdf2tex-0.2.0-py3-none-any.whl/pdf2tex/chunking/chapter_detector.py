"""
Chapter detection from PDF structure.

Analyzes TOC and heading patterns to identify document structure.
"""

import re
from dataclasses import dataclass
from typing import Any

import structlog

from pdf2tex.chunking.models import ChapterMetadata, HeadingLevel
from pdf2tex.extraction.models import ExtractionResult, TextBlock

logger = structlog.get_logger(__name__)


@dataclass
class TOCEntry:
    """Entry from table of contents."""

    title: str
    level: int
    page: int
    children: list["TOCEntry"]


@dataclass
class DetectedHeading:
    """A heading detected in the text."""

    title: str
    level: HeadingLevel
    page_number: int
    position: float  # Y position on page
    number: str | None = None


class ChapterDetector:
    """
    Detects chapter and section boundaries.
    
    Uses multiple strategies:
    1. PDF table of contents (most reliable)
    2. Font size/style analysis
    3. Heading pattern matching
    """

    # Common chapter/section patterns
    CHAPTER_PATTERNS = [
        r"^Chapter\s+(\d+|[IVXLCDM]+)[:\.]?\s*(.*)$",
        r"^CHAPTER\s+(\d+|[IVXLCDM]+)[:\.]?\s*(.*)$",
        r"^(\d+)\.\s+(.+)$",  # "1. Introduction"
        r"^Part\s+(\d+|[IVXLCDM]+)[:\.]?\s*(.*)$",
    ]

    SECTION_PATTERNS = [
        r"^(\d+\.\d+)\s+(.+)$",  # "1.1 Background"
        r"^(\d+\.\d+\.\d+)\s+(.+)$",  # "1.1.1 Details"
        r"^Section\s+(\d+)[:\.]?\s*(.*)$",
    ]

    def __init__(
        self,
        min_heading_font_ratio: float = 1.2,
        use_toc: bool = True,
        use_font_analysis: bool = True,
        use_patterns: bool = True,
    ) -> None:
        """
        Initialize chapter detector.

        Args:
            min_heading_font_ratio: Minimum font size ratio for headings
            use_toc: Whether to use PDF table of contents
            use_font_analysis: Whether to analyze fonts
            use_patterns: Whether to use pattern matching
        """
        self.min_heading_font_ratio = min_heading_font_ratio
        self.use_toc = use_toc
        self.use_font_analysis = use_font_analysis
        self.use_patterns = use_patterns

    def detect_chapters(
        self,
        extraction: ExtractionResult,
    ) -> list[ChapterMetadata]:
        """
        Detect chapters in extracted content.

        Args:
            extraction: PDF extraction result

        Returns:
            List of chapter metadata
        """
        document_id = extraction.source_path.stem

        # Try TOC first
        if self.use_toc and extraction.table_of_contents:
            chapters = self._from_toc(extraction.table_of_contents, document_id)
            if chapters:
                logger.info("Detected chapters from TOC", count=len(chapters))
                return chapters

        # Fall back to heading detection
        headings = self._detect_headings(extraction)
        if headings:
            chapters = self._headings_to_chapters(headings, document_id)
            logger.info("Detected chapters from headings", count=len(chapters))
            return chapters

        # Create single chapter if no structure found
        logger.warning("No chapter structure detected, creating single chapter")
        return [
            ChapterMetadata(
                chapter_id=f"{document_id}_ch_0",
                document_id=document_id,
                title="Document",
                number=1,
                level=HeadingLevel.CHAPTER,
                start_page=0,
                end_page=len(extraction.pages) - 1,
            )
        ]

    def _from_toc(
        self,
        toc: list[dict[str, Any]],
        document_id: str,
    ) -> list[ChapterMetadata]:
        """
        Convert PDF TOC to chapter metadata.

        Args:
            toc: Table of contents from PDF
            document_id: Document identifier

        Returns:
            List of chapter metadata
        """
        chapters: list[ChapterMetadata] = []
        
        for i, entry in enumerate(toc):
            level = entry.get("level", 1)
            title = entry.get("title", f"Chapter {i + 1}")
            page = entry.get("page", 0)

            # Map TOC level to heading level
            heading_level = self._toc_level_to_heading(level)

            # Determine end page (start of next entry or end of doc)
            end_page = page
            if i + 1 < len(toc):
                end_page = toc[i + 1].get("page", page) - 1

            chapter = ChapterMetadata(
                chapter_id=f"{document_id}_ch_{i}",
                document_id=document_id,
                title=title,
                number=i + 1,
                level=heading_level,
                start_page=page,
                end_page=end_page,
            )
            chapters.append(chapter)

        # Set parent relationships
        self._set_parent_relationships(chapters)

        return chapters

    def _toc_level_to_heading(self, toc_level: int) -> HeadingLevel:
        """Map TOC level to HeadingLevel."""
        level_map = {
            0: HeadingLevel.PART,
            1: HeadingLevel.CHAPTER,
            2: HeadingLevel.SECTION,
            3: HeadingLevel.SUBSECTION,
            4: HeadingLevel.SUBSUBSECTION,
            5: HeadingLevel.PARAGRAPH,
        }
        return level_map.get(toc_level, HeadingLevel.SECTION)

    def _detect_headings(
        self,
        extraction: ExtractionResult,
    ) -> list[DetectedHeading]:
        """
        Detect headings from text content.

        Args:
            extraction: PDF extraction result

        Returns:
            List of detected headings
        """
        headings: list[DetectedHeading] = []

        # Analyze fonts to find average
        all_fonts: list[float] = []
        for page in extraction.pages:
            for block in page.text_blocks:
                if block.font_size:
                    all_fonts.append(block.font_size)

        avg_font = sum(all_fonts) / len(all_fonts) if all_fonts else 12.0
        heading_threshold = avg_font * self.min_heading_font_ratio

        # Scan pages for headings
        for page in extraction.pages:
            for block in page.text_blocks:
                heading = self._is_heading(block, heading_threshold)
                if heading:
                    heading.page_number = page.page_number
                    headings.append(heading)

        return headings

    def _is_heading(
        self,
        block: TextBlock,
        font_threshold: float,
    ) -> DetectedHeading | None:
        """
        Check if text block is a heading.

        Args:
            block: Text block to check
            font_threshold: Minimum font size for heading

        Returns:
            DetectedHeading if block is a heading
        """
        text = block.content.strip()
        
        # Skip empty or very long text
        if not text or len(text) > 200:
            return None

        # Check font size
        is_large_font = block.font_size and block.font_size >= font_threshold
        is_bold = block.font_name and "bold" in block.font_name.lower()

        # Check patterns
        if self.use_patterns:
            # Chapter patterns
            for pattern in self.CHAPTER_PATTERNS:
                match = re.match(pattern, text, re.IGNORECASE)
                if match:
                    number = match.group(1) if match.groups() else None
                    title = match.group(2) if len(match.groups()) > 1 else text
                    return DetectedHeading(
                        title=title.strip() or text,
                        level=HeadingLevel.CHAPTER,
                        page_number=0,
                        position=block.bbox.y0,
                        number=number,
                    )

            # Section patterns
            for pattern in self.SECTION_PATTERNS:
                match = re.match(pattern, text)
                if match:
                    number = match.group(1)
                    title = match.group(2)
                    level = self._number_to_level(number)
                    return DetectedHeading(
                        title=title.strip(),
                        level=level,
                        page_number=0,
                        position=block.bbox.y0,
                        number=number,
                    )

        # Font-based detection
        if self.use_font_analysis and (is_large_font or is_bold):
            # Single line, not too long
            if "\n" not in text and len(text) < 100:
                level = HeadingLevel.SECTION if not is_bold else HeadingLevel.CHAPTER
                return DetectedHeading(
                    title=text,
                    level=level,
                    page_number=0,
                    position=block.bbox.y0,
                )

        return None

    def _number_to_level(self, number: str) -> HeadingLevel:
        """Map section number to heading level."""
        depth = number.count(".")
        level_map = {
            0: HeadingLevel.SECTION,
            1: HeadingLevel.SUBSECTION,
            2: HeadingLevel.SUBSUBSECTION,
        }
        return level_map.get(depth, HeadingLevel.PARAGRAPH)

    def _headings_to_chapters(
        self,
        headings: list[DetectedHeading],
        document_id: str,
    ) -> list[ChapterMetadata]:
        """
        Convert detected headings to chapter metadata.

        Args:
            headings: List of detected headings
            document_id: Document identifier

        Returns:
            List of chapter metadata
        """
        chapters: list[ChapterMetadata] = []

        for i, heading in enumerate(headings):
            # Determine end page
            end_page = heading.page_number
            if i + 1 < len(headings):
                end_page = headings[i + 1].page_number - 1

            chapter = ChapterMetadata(
                chapter_id=f"{document_id}_ch_{i}",
                document_id=document_id,
                title=heading.title,
                number=heading.number or str(i + 1),
                level=heading.level,
                start_page=heading.page_number,
                end_page=max(end_page, heading.page_number),
            )
            chapters.append(chapter)

        self._set_parent_relationships(chapters)
        return chapters

    def _set_parent_relationships(
        self,
        chapters: list[ChapterMetadata],
    ) -> None:
        """Set parent_id based on heading levels."""
        parent_stack: list[ChapterMetadata] = []

        for chapter in chapters:
            # Pop parents of same or lower level
            while parent_stack and parent_stack[-1].level.value >= chapter.level.value:
                parent_stack.pop()

            # Set parent
            if parent_stack:
                chapter.parent_id = parent_stack[-1].chapter_id

            parent_stack.append(chapter)

    def get_page_ranges(
        self,
        chapters: list[ChapterMetadata],
        total_pages: int,
    ) -> list[tuple[int, int]]:
        """
        Get page ranges for each chapter.

        Args:
            chapters: List of chapters
            total_pages: Total pages in document

        Returns:
            List of (start, end) page tuples
        """
        ranges: list[tuple[int, int]] = []

        for i, chapter in enumerate(chapters):
            start = chapter.start_page
            
            # End is next chapter start - 1, or document end
            if i + 1 < len(chapters):
                end = chapters[i + 1].start_page - 1
            else:
                end = total_pages - 1

            ranges.append((start, max(end, start)))

        return ranges
