"""
Data models for the chunking layer.

Defines structures for text chunks, chapters, and metadata.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ChunkType(str, Enum):
    """Type of content chunk."""

    HEADER = "header"
    PARAGRAPH = "paragraph"
    MATH = "math"
    CODE = "code"
    TABLE = "table"
    FIGURE = "figure"
    LIST = "list"
    CAPTION = "caption"
    MIXED = "mixed"


class HeadingLevel(int, Enum):
    """Heading hierarchy levels."""

    PART = 0
    CHAPTER = 1
    SECTION = 2
    SUBSECTION = 3
    SUBSUBSECTION = 4
    PARAGRAPH = 5
    SUBPARAGRAPH = 6


@dataclass
class ChunkMetadata:
    """Metadata associated with a text chunk."""

    chunk_id: str
    document_id: str
    chapter_id: str | None = None
    section_path: list[str] = field(default_factory=list)
    page_numbers: list[int] = field(default_factory=list)
    chunk_type: ChunkType = ChunkType.PARAGRAPH
    heading_level: HeadingLevel | None = None
    has_math: bool = False
    has_code: bool = False
    has_table: bool = False
    has_figure: bool = False
    char_count: int = 0
    word_count: int = 0
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def section_string(self) -> str:
        """Get section path as string."""
        return " > ".join(self.section_path) if self.section_path else ""


@dataclass
class Chunk:
    """A chunk of text for embedding and retrieval."""

    content: str
    metadata: ChunkMetadata
    embedding: list[float] | None = None

    def __post_init__(self) -> None:
        """Calculate metadata values."""
        self.metadata.char_count = len(self.content)
        self.metadata.word_count = len(self.content.split())

    @property
    def id(self) -> str:
        """Get chunk ID."""
        return self.metadata.chunk_id

    @property
    def page_range(self) -> str:
        """Get page range as string."""
        pages = self.metadata.page_numbers
        if not pages:
            return ""
        if len(pages) == 1:
            return str(pages[0] + 1)  # 1-indexed for display
        return f"{pages[0] + 1}-{pages[-1] + 1}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "content": self.content,
            "metadata": {
                "chunk_id": self.metadata.chunk_id,
                "document_id": self.metadata.document_id,
                "chapter_id": self.metadata.chapter_id,
                "section_path": self.metadata.section_path,
                "page_numbers": self.metadata.page_numbers,
                "chunk_type": self.metadata.chunk_type.value,
                "heading_level": (
                    self.metadata.heading_level.value
                    if self.metadata.heading_level
                    else None
                ),
                "has_math": self.metadata.has_math,
                "has_code": self.metadata.has_code,
                "has_table": self.metadata.has_table,
                "has_figure": self.metadata.has_figure,
                "char_count": self.metadata.char_count,
                "word_count": self.metadata.word_count,
                "extra": self.metadata.extra,
            },
            "embedding": self.embedding,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Chunk":
        """Create from dictionary."""
        meta = data["metadata"]
        metadata = ChunkMetadata(
            chunk_id=meta["chunk_id"],
            document_id=meta["document_id"],
            chapter_id=meta.get("chapter_id"),
            section_path=meta.get("section_path", []),
            page_numbers=meta.get("page_numbers", []),
            chunk_type=ChunkType(meta.get("chunk_type", "paragraph")),
            heading_level=(
                HeadingLevel(meta["heading_level"])
                if meta.get("heading_level") is not None
                else None
            ),
            has_math=meta.get("has_math", False),
            has_code=meta.get("has_code", False),
            has_table=meta.get("has_table", False),
            has_figure=meta.get("has_figure", False),
            char_count=meta.get("char_count", 0),
            word_count=meta.get("word_count", 0),
            extra=meta.get("extra", {}),
        )
        return cls(
            content=data["content"],
            metadata=metadata,
            embedding=data.get("embedding"),
        )


@dataclass
class ChapterMetadata:
    """Metadata for a chapter."""

    chapter_id: str
    document_id: str
    title: str
    number: int | str | None = None
    level: HeadingLevel = HeadingLevel.CHAPTER
    start_page: int = 0
    end_page: int = 0
    parent_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chapter:
    """A chapter or section in the document."""

    title: str
    content: str
    chunks: list[Chunk]
    metadata: ChapterMetadata
    children: list["Chapter"] = field(default_factory=list)

    @property
    def id(self) -> str:
        """Get chapter ID."""
        return self.metadata.chapter_id

    @property
    def page_count(self) -> int:
        """Get number of pages in chapter."""
        return self.metadata.end_page - self.metadata.start_page + 1

    @property
    def chunk_count(self) -> int:
        """Get total chunks including nested chapters."""
        count = len(self.chunks)
        for child in self.children:
            count += child.chunk_count
        return count

    @property
    def all_chunks(self) -> list[Chunk]:
        """Get all chunks including from nested chapters."""
        result = list(self.chunks)
        for child in self.children:
            result.extend(child.all_chunks)
        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "content": self.content,
            "metadata": {
                "chapter_id": self.metadata.chapter_id,
                "document_id": self.metadata.document_id,
                "title": self.metadata.title,
                "number": self.metadata.number,
                "level": self.metadata.level.value,
                "start_page": self.metadata.start_page,
                "end_page": self.metadata.end_page,
                "parent_id": self.metadata.parent_id,
                "extra": self.metadata.extra,
            },
            "chunks": [c.to_dict() for c in self.chunks],
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class ChunkingResult:
    """Result of chunking operation."""

    document_id: str
    source_path: Path
    chapters: list[Chapter]
    all_chunks: list[Chunk]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_chunks(self) -> int:
        """Total number of chunks."""
        return len(self.all_chunks)

    @property
    def total_chapters(self) -> int:
        """Total number of top-level chapters."""
        return len(self.chapters)

    def get_chapter_by_id(self, chapter_id: str) -> Chapter | None:
        """Find chapter by ID."""
        for chapter in self.chapters:
            if chapter.id == chapter_id:
                return chapter
            # Check children recursively
            result = self._find_in_children(chapter.children, chapter_id)
            if result:
                return result
        return None

    def _find_in_children(
        self, children: list[Chapter], chapter_id: str
    ) -> Chapter | None:
        """Recursively find chapter in children."""
        for child in children:
            if child.id == chapter_id:
                return child
            result = self._find_in_children(child.children, chapter_id)
            if result:
                return result
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "document_id": self.document_id,
            "source_path": str(self.source_path),
            "chapters": [c.to_dict() for c in self.chapters],
            "metadata": self.metadata,
            "total_chunks": self.total_chunks,
            "total_chapters": self.total_chapters,
        }
