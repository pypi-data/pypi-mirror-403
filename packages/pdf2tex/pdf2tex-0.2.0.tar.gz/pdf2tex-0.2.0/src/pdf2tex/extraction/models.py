"""
Data models for the extraction layer.

Defines the structure for extracted content including pages, text blocks,
mathematical regions, tables, and figures.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ContentType(str, Enum):
    """Types of content that can be extracted from a PDF."""

    TEXT = "text"
    MATH_INLINE = "math_inline"
    MATH_DISPLAY = "math_display"
    TABLE = "table"
    FIGURE = "figure"
    CODE = "code"
    HEADING = "heading"
    LIST = "list"
    CAPTION = "caption"
    FOOTNOTE = "footnote"
    REFERENCE = "reference"


@dataclass
class BoundingBox:
    """Bounding box coordinates for a content region."""

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        """Calculate width of bounding box."""
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        """Calculate height of bounding box."""
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        """Calculate area of bounding box."""
        return self.width * self.height

    def to_tuple(self) -> tuple[float, float, float, float]:
        """Convert to tuple format."""
        return (self.x0, self.y0, self.x1, self.y1)

    def overlaps(self, other: "BoundingBox", threshold: float = 0.5) -> bool:
        """Check if this box overlaps with another by threshold."""
        x_overlap = max(0, min(self.x1, other.x1) - max(self.x0, other.x0))
        y_overlap = max(0, min(self.y1, other.y1) - max(self.y0, other.y0))
        overlap_area = x_overlap * y_overlap
        min_area = min(self.area, other.area)
        return overlap_area / min_area >= threshold if min_area > 0 else False


@dataclass
class TextBlock:
    """A block of text extracted from a PDF page."""

    content: str
    content_type: ContentType
    bbox: BoundingBox
    font_name: str | None = None
    font_size: float | None = None
    is_bold: bool = False
    is_italic: bool = False
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_heading(self) -> bool:
        """Check if this text block is a heading."""
        return self.content_type == ContentType.HEADING

    @property
    def char_count(self) -> int:
        """Get character count."""
        return len(self.content)


@dataclass
class MathRegion:
    """A mathematical equation or expression extracted from a PDF."""

    latex: str
    content_type: ContentType  # MATH_INLINE or MATH_DISPLAY
    bbox: BoundingBox
    source: str = "nougat"  # nougat, texteller, or ocr
    confidence: float = 1.0
    is_validated: bool = False
    validation_errors: list[str] = field(default_factory=list)
    original_image: bytes | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_display(self) -> bool:
        """Check if this is a display equation."""
        return self.content_type == ContentType.MATH_DISPLAY

    @property
    def is_inline(self) -> bool:
        """Check if this is an inline equation."""
        return self.content_type == ContentType.MATH_INLINE


@dataclass
class TableRegion:
    """A table extracted from a PDF page."""

    content: str  # Markdown or LaTeX representation
    latex: str | None  # LaTeX tabular representation
    bbox: BoundingBox
    rows: int = 0
    cols: int = 0
    has_header: bool = False
    confidence: float = 1.0
    raw_data: list[list[str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FigureRegion:
    """A figure or image extracted from a PDF page."""

    image_path: Path | None
    image_data: bytes | None
    bbox: BoundingBox
    caption: str | None = None
    label: str | None = None
    format: str = "png"
    width: int = 0
    height: int = 0
    dpi: int = 150
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PageMetadata:
    """Metadata about an extracted PDF page."""

    page_number: int
    width: float
    height: float
    rotation: int = 0
    has_text: bool = True
    has_images: bool = False
    has_tables: bool = False
    has_math: bool = False
    is_scanned: bool = False
    ocr_applied: bool = False
    language: str | None = None
    char_count: int = 0
    word_count: int = 0


@dataclass
class ExtractedPage:
    """Complete extraction result for a single PDF page."""

    page_number: int
    text_blocks: list[TextBlock] = field(default_factory=list)
    math_regions: list[MathRegion] = field(default_factory=list)
    tables: list[TableRegion] = field(default_factory=list)
    figures: list[FigureRegion] = field(default_factory=list)
    metadata: PageMetadata | None = None
    raw_text: str = ""
    errors: list[str] = field(default_factory=list)

    @property
    def has_content(self) -> bool:
        """Check if page has any extracted content."""
        return bool(
            self.text_blocks or self.math_regions or self.tables or self.figures or self.raw_text
        )

    @property
    def total_blocks(self) -> int:
        """Get total number of content blocks."""
        return (
            len(self.text_blocks)
            + len(self.math_regions)
            + len(self.tables)
            + len(self.figures)
        )

    def get_text_content(self) -> str:
        """Get all text content concatenated."""
        if self.raw_text:
            return self.raw_text
        return "\n".join(block.content for block in self.text_blocks)

    def get_math_latex(self) -> list[str]:
        """Get all math regions as LaTeX strings."""
        return [region.latex for region in self.math_regions]

    def merge_blocks(self) -> list[TextBlock | MathRegion | TableRegion | FigureRegion]:
        """Merge all content blocks sorted by position (top to bottom, left to right)."""
        all_blocks: list[TextBlock | MathRegion | TableRegion | FigureRegion] = [
            *self.text_blocks,
            *self.math_regions,
            *self.tables,
            *self.figures,
        ]
        # Sort by y-position first, then x-position
        return sorted(all_blocks, key=lambda b: (b.bbox.y0, b.bbox.x0))


@dataclass
class ExtractionResult:
    """Complete extraction result for an entire document."""

    document_id: str
    source_path: Path
    total_pages: int
    pages: list[ExtractedPage] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def successful_pages(self) -> int:
        """Count pages with content."""
        return sum(1 for p in self.pages if p.has_content)

    @property
    def total_math_regions(self) -> int:
        """Count total math regions across all pages."""
        return sum(len(p.math_regions) for p in self.pages)

    @property
    def total_tables(self) -> int:
        """Count total tables across all pages."""
        return sum(len(p.tables) for p in self.pages)
