"""
Hierarchical text splitter for chunking.

Implements semantic-aware splitting that preserves document structure.
"""

import hashlib
import re
from typing import Any

import structlog

from pdf2tex.chunking.models import Chunk, ChunkMetadata, ChunkType, HeadingLevel
from pdf2tex.extraction.models import ExtractedPage, MathRegion, TextBlock

logger = structlog.get_logger(__name__)


class TextSplitter:
    """
    Semantic-aware text splitter.
    
    Features:
    - Respects sentence and paragraph boundaries
    - Preserves math expressions intact
    - Handles code blocks
    - Maintains section context
    """

    # Patterns for splitting
    SENTENCE_ENDINGS = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
    PARAGRAPH_BREAK = re.compile(r"\n\s*\n")
    MATH_BLOCK = re.compile(r"\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]")
    INLINE_MATH = re.compile(r"\$[^$]+\$|\\\(.*?\\\)")

    def __init__(
        self,
        chunk_size: int = 1500,
        chunk_overlap: int = 150,
        min_chunk_size: int = 100,
        preserve_math: bool = True,
        preserve_code: bool = True,
    ) -> None:
        """
        Initialize text splitter.

        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
            min_chunk_size: Minimum chunk size
            preserve_math: Keep math expressions intact
            preserve_code: Keep code blocks intact
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.preserve_math = preserve_math
        self.preserve_code = preserve_code

    def split_pages(
        self,
        pages: list[ExtractedPage],
        document_id: str,
        chapter_id: str | None = None,
        section_path: list[str] | None = None,
    ) -> list[Chunk]:
        """
        Split multiple pages into chunks.

        Args:
            pages: List of extracted pages
            document_id: Document identifier
            chapter_id: Optional chapter identifier
            section_path: Optional section hierarchy

        Returns:
            List of chunks
        """
        # Combine page content
        combined_text = ""
        page_mapping: list[tuple[int, int, int]] = []  # (start, end, page_num)

        for page in pages:
            start = len(combined_text)
            page_text = self._page_to_text(page)
            combined_text += page_text
            end = len(combined_text)
            page_mapping.append((start, end, page.page_number))

            if page_text and not page_text.endswith("\n"):
                combined_text += "\n\n"

        # Split text
        text_chunks = self._split_text(combined_text)

        # Convert to Chunk objects
        chunks: list[Chunk] = []
        for i, text in enumerate(text_chunks):
            # Determine page numbers
            chunk_start = combined_text.find(text)
            chunk_end = chunk_start + len(text)
            page_nums = self._get_page_numbers(chunk_start, chunk_end, page_mapping)

            # Detect content type
            chunk_type = self._detect_chunk_type(text)

            # Create metadata
            metadata = ChunkMetadata(
                chunk_id=self._generate_chunk_id(document_id, i, text),
                document_id=document_id,
                chapter_id=chapter_id,
                section_path=section_path or [],
                page_numbers=page_nums,
                chunk_type=chunk_type,
                has_math=bool(self.INLINE_MATH.search(text) or self.MATH_BLOCK.search(text)),
                has_code=self._has_code(text),
            )

            chunks.append(Chunk(content=text, metadata=metadata))

        return chunks

    def split_text(
        self,
        text: str,
        document_id: str,
        chapter_id: str | None = None,
        section_path: list[str] | None = None,
        page_numbers: list[int] | None = None,
    ) -> list[Chunk]:
        """
        Split text into chunks.

        Args:
            text: Text to split
            document_id: Document identifier
            chapter_id: Optional chapter identifier
            section_path: Optional section hierarchy
            page_numbers: Optional page numbers

        Returns:
            List of chunks
        """
        text_chunks = self._split_text(text)

        chunks: list[Chunk] = []
        for i, chunk_text in enumerate(text_chunks):
            chunk_type = self._detect_chunk_type(chunk_text)

            metadata = ChunkMetadata(
                chunk_id=self._generate_chunk_id(document_id, i, chunk_text),
                document_id=document_id,
                chapter_id=chapter_id,
                section_path=section_path or [],
                page_numbers=page_numbers or [],
                chunk_type=chunk_type,
                has_math=bool(
                    self.INLINE_MATH.search(chunk_text) or 
                    self.MATH_BLOCK.search(chunk_text)
                ),
                has_code=self._has_code(chunk_text),
            )

            chunks.append(Chunk(content=chunk_text, metadata=metadata))

        return chunks

    def _split_text(self, text: str) -> list[str]:
        """
        Core splitting logic.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        # Protect special content
        protected_ranges = self._find_protected_ranges(text)

        # Split by paragraphs first
        paragraphs = self.PARAGRAPH_BREAK.split(text)
        
        chunks: list[str] = []
        current_chunk = ""

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # Check if adding paragraph exceeds limit
            if len(current_chunk) + len(paragraph) + 2 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Save current chunk if valid
                if current_chunk and len(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk)

                # Handle long paragraphs
                if len(paragraph) > self.chunk_size:
                    sub_chunks = self._split_long_paragraph(paragraph, protected_ranges)
                    if sub_chunks:
                        chunks.extend(sub_chunks[:-1])
                        current_chunk = sub_chunks[-1]
                    else:
                        current_chunk = paragraph[:self.chunk_size]
                else:
                    # Start new chunk with overlap
                    overlap = self._get_overlap(current_chunk) if current_chunk else ""
                    current_chunk = overlap + paragraph if overlap else paragraph

        # Add final chunk
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append(current_chunk)

        return chunks

    def _split_long_paragraph(
        self,
        paragraph: str,
        protected_ranges: list[tuple[int, int]],
    ) -> list[str]:
        """
        Split a long paragraph by sentences.

        Args:
            paragraph: Paragraph to split
            protected_ranges: Ranges of protected content

        Returns:
            List of sub-chunks
        """
        # Try sentence splitting
        sentences = self.SENTENCE_ENDINGS.split(paragraph)
        
        if len(sentences) <= 1:
            # Force split at chunk_size
            return self._force_split(paragraph)

        chunks: list[str] = []
        current = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current) + len(sentence) + 1 <= self.chunk_size:
                current = (current + " " + sentence).strip()
            else:
                if current:
                    chunks.append(current)
                current = sentence

        if current:
            chunks.append(current)

        return chunks

    def _force_split(self, text: str) -> list[str]:
        """Force split text at chunk size boundaries."""
        chunks: list[str] = []
        
        while len(text) > self.chunk_size:
            # Find split point
            split_at = self.chunk_size
            
            # Try to split at word boundary
            space_idx = text.rfind(" ", 0, split_at)
            if space_idx > self.chunk_size // 2:
                split_at = space_idx

            chunks.append(text[:split_at].strip())
            text = text[split_at:].strip()

        if text:
            chunks.append(text)

        return chunks

    def _find_protected_ranges(self, text: str) -> list[tuple[int, int]]:
        """Find ranges that should not be split."""
        ranges: list[tuple[int, int]] = []

        if self.preserve_math:
            # Block math
            for match in self.MATH_BLOCK.finditer(text):
                ranges.append((match.start(), match.end()))
            # Inline math
            for match in self.INLINE_MATH.finditer(text):
                ranges.append((match.start(), match.end()))

        if self.preserve_code:
            # Code blocks (markdown style)
            for match in re.finditer(r"```[\s\S]*?```", text):
                ranges.append((match.start(), match.end()))

        return sorted(ranges)

    def _get_overlap(self, text: str) -> str:
        """Get overlap text from end of chunk."""
        if not text or self.chunk_overlap == 0:
            return ""

        if len(text) <= self.chunk_overlap:
            return text + " "

        # Try to start at sentence boundary
        overlap_text = text[-self.chunk_overlap:]
        sentence_start = overlap_text.find(". ")
        
        if sentence_start > 0 and sentence_start < len(overlap_text) // 2:
            return overlap_text[sentence_start + 2:] + " "
        
        # Try word boundary
        space_idx = overlap_text.find(" ")
        if space_idx > 0:
            return overlap_text[space_idx + 1:] + " "

        return overlap_text + " "

    def _get_page_numbers(
        self,
        start: int,
        end: int,
        page_mapping: list[tuple[int, int, int]],
    ) -> list[int]:
        """Get page numbers for character range."""
        pages: list[int] = []
        
        for pstart, pend, page_num in page_mapping:
            if pstart <= start < pend or pstart < end <= pend or (start <= pstart and end >= pend):
                if page_num not in pages:
                    pages.append(page_num)

        return sorted(pages)

    def _page_to_text(self, page: ExtractedPage) -> str:
        """Convert page to text with math content."""
        parts: list[str] = []

        # Add text blocks
        for block in page.text_blocks:
            parts.append(block.content)

        # Integrate math regions
        for math_region in page.math_regions:
            if math_region.is_display:
                parts.append(f"\n$$\n{math_region.latex}\n$$\n")
            else:
                # Already inline in text usually
                pass

        return "\n".join(parts)

    def _detect_chunk_type(self, text: str) -> ChunkType:
        """Detect the type of content in chunk."""
        text_lower = text.lower()

        # Check for math dominance
        math_chars = len("".join(self.MATH_BLOCK.findall(text)))
        if math_chars > len(text) * 0.5:
            return ChunkType.MATH

        # Check for code
        if "```" in text or text.count("    ") > 3:
            return ChunkType.CODE

        # Check for table-like content
        if text.count("|") > 5 or text.count("\t") > 5:
            return ChunkType.TABLE

        # Check for list
        list_markers = len(re.findall(r"^\s*[-*•]\s", text, re.MULTILINE))
        numbered_list = len(re.findall(r"^\s*\d+\.\s", text, re.MULTILINE))
        if list_markers + numbered_list > 3:
            return ChunkType.LIST

        # Check for heading
        if len(text) < 100 and not text.endswith("."):
            return ChunkType.HEADER

        return ChunkType.PARAGRAPH

    def _has_code(self, text: str) -> bool:
        """Check if text contains code."""
        return "```" in text or bool(re.search(r"^\s{4,}\S", text, re.MULTILINE))

    def _generate_chunk_id(
        self,
        document_id: str,
        index: int,
        content: str,
    ) -> str:
        """Generate unique chunk ID."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{document_id}_chunk_{index}_{content_hash}"


class MathAwareTextSplitter(TextSplitter):
    """
    Text splitter with enhanced math handling.
    
    Ensures mathematical expressions are kept intact and
    properly formatted for LaTeX output.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with math preservation enabled."""
        kwargs.setdefault("preserve_math", True)
        super().__init__(**kwargs)

    def split_with_math(
        self,
        pages: list[ExtractedPage],
        document_id: str,
        chapter_id: str | None = None,
    ) -> list[Chunk]:
        """
        Split pages preserving math regions.

        Args:
            pages: Extracted pages
            document_id: Document identifier
            chapter_id: Optional chapter ID

        Returns:
            List of chunks with math preserved
        """
        # Extract math regions for reference
        all_math: dict[int, list[MathRegion]] = {}
        for page in pages:
            if page.math_regions:
                all_math[page.page_number] = page.math_regions

        # Regular split
        chunks = self.split_pages(pages, document_id, chapter_id)

        # Mark chunks with significant math
        for chunk in chunks:
            if chunk.metadata.has_math:
                chunk.metadata.extra["math_count"] = len(
                    self.MATH_BLOCK.findall(chunk.content)
                ) + len(self.INLINE_MATH.findall(chunk.content))

        return chunks
