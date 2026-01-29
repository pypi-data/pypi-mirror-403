"""
PDF parsing using PyMuPDF (fitz).

Provides fast, native PDF text extraction with font and layout information.
"""

import re
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
import structlog

from pdf2tex.extraction.models import (
    BoundingBox,
    ContentType,
    FigureRegion,
    PageMetadata,
    TextBlock,
)

logger = structlog.get_logger(__name__)


class PDFParser:
    """
    PDF text and layout extraction using PyMuPDF.
    
    Handles native text extraction, font detection, and image extraction.
    """

    # Heading detection patterns
    HEADING_PATTERNS = [
        r"^(Chapter|CHAPTER)\s+\d+",
        r"^(Section|SECTION)\s+\d+",
        r"^(Part|PART)\s+[IVXLCDM\d]+",
        r"^\d+\.\s+[A-Z]",
        r"^\d+\.\d+\s+[A-Z]",
    ]

    def __init__(
        self,
        *,
        extract_images: bool = True,
        image_dpi: int = 150,
        min_image_size: int = 100,
    ) -> None:
        """
        Initialize PDF parser.

        Args:
            extract_images: Whether to extract images from PDF
            image_dpi: DPI for image extraction
            min_image_size: Minimum image dimension to extract
        """
        self.extract_images = extract_images
        self.image_dpi = image_dpi
        self.min_image_size = min_image_size
        self._heading_regex = [re.compile(p) for p in self.HEADING_PATTERNS]

    def open_document(self, pdf_path: Path) -> fitz.Document:
        """
        Open a PDF document.

        Args:
            pdf_path: Path to PDF file

        Returns:
            PyMuPDF document object

        Raises:
            FileNotFoundError: If PDF doesn't exist
            ValueError: If file is not a valid PDF
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)
            if not doc.is_pdf:
                raise ValueError(f"Not a valid PDF: {pdf_path}")
            return doc
        except Exception as e:
            logger.error("Failed to open PDF", path=str(pdf_path), error=str(e))
            raise

    def get_page_count(self, pdf_path: Path) -> int:
        """Get total page count of a PDF."""
        with fitz.open(pdf_path) as doc:
            return len(doc)

    def extract_page_text(
        self,
        doc: fitz.Document,
        page_num: int,
    ) -> tuple[list[TextBlock], PageMetadata]:
        """
        Extract text blocks from a single page.

        Args:
            doc: Open PDF document
            page_num: Page number (0-indexed)

        Returns:
            Tuple of (text_blocks, page_metadata)
        """
        page = doc[page_num]
        rect = page.rect

        # Get text blocks with formatting info
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

        text_blocks: list[TextBlock] = []
        char_count = 0
        word_count = 0

        for block in blocks:
            if block["type"] != 0:  # Skip image blocks
                continue

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue

                    bbox = BoundingBox(
                        x0=span["bbox"][0],
                        y0=span["bbox"][1],
                        x1=span["bbox"][2],
                        y1=span["bbox"][3],
                    )

                    # Detect content type
                    content_type = self._classify_text_block(
                        text,
                        span.get("font", ""),
                        span.get("size", 12),
                    )

                    text_block = TextBlock(
                        content=text,
                        content_type=content_type,
                        bbox=bbox,
                        font_name=span.get("font"),
                        font_size=span.get("size"),
                        is_bold="Bold" in span.get("font", "") or "bold" in span.get("font", ""),
                        is_italic="Italic" in span.get("font", "") or "italic" in span.get("font", ""),
                        metadata={"color": span.get("color"), "flags": span.get("flags")},
                    )
                    text_blocks.append(text_block)

                    char_count += len(text)
                    word_count += len(text.split())

        # Create metadata
        metadata = PageMetadata(
            page_number=page_num + 1,  # 1-indexed for user display
            width=rect.width,
            height=rect.height,
            rotation=page.rotation,
            has_text=bool(text_blocks),
            has_images=self._page_has_images(page),
            char_count=char_count,
            word_count=word_count,
            is_scanned=char_count < 50 and self._page_has_images(page),
        )

        return text_blocks, metadata

    def extract_page_images(
        self,
        doc: fitz.Document,
        page_num: int,
    ) -> list[FigureRegion]:
        """
        Extract images from a single page.

        Args:
            doc: Open PDF document
            page_num: Page number (0-indexed)

        Returns:
            List of extracted figure regions
        """
        if not self.extract_images:
            return []

        page = doc[page_num]
        figures: list[FigureRegion] = []

        image_list = page.get_images(full=True)
        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]

            try:
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue

                image_bytes = base_image["image"]
                img_ext = base_image["ext"]
                width = base_image["width"]
                height = base_image["height"]

                # Skip small images (likely icons or artifacts)
                if width < self.min_image_size or height < self.min_image_size:
                    continue

                # Get image position on page
                img_rects = page.get_image_rects(xref)
                if img_rects:
                    rect = img_rects[0]
                    bbox = BoundingBox(
                        x0=rect.x0,
                        y0=rect.y0,
                        x1=rect.x1,
                        y1=rect.y1,
                    )
                else:
                    # Fallback: use full page
                    bbox = BoundingBox(x0=0, y0=0, x1=width, y1=height)

                figure = FigureRegion(
                    image_path=None,
                    image_data=image_bytes,
                    bbox=bbox,
                    format=img_ext,
                    width=width,
                    height=height,
                    dpi=self.image_dpi,
                    metadata={"xref": xref, "index": img_index},
                )
                figures.append(figure)

            except Exception as e:
                logger.warning(
                    "Failed to extract image",
                    page=page_num,
                    xref=xref,
                    error=str(e),
                )

        return figures

    def extract_raw_text(self, doc: fitz.Document, page_num: int) -> str:
        """Extract raw text from a page without formatting."""
        page = doc[page_num]
        return page.get_text("text")

    def _classify_text_block(
        self,
        text: str,
        font: str,
        size: float,
    ) -> ContentType:
        """Classify a text block by its content type."""
        # Check for heading patterns
        for pattern in self._heading_regex:
            if pattern.match(text):
                return ContentType.HEADING

        # Check for bold large text (likely heading)
        if "Bold" in font and size > 14:
            return ContentType.HEADING

        # Check for list items
        if re.match(r"^[\u2022\u2023\u25E6\u2043\u2219•\-\*]\s", text):
            return ContentType.LIST
        if re.match(r"^\d+[.)]\s", text):
            return ContentType.LIST

        # Check for footnote markers
        if re.match(r"^\[\d+\]$", text) or re.match(r"^\d+$", text) and size < 10:
            return ContentType.FOOTNOTE

        # Check for caption patterns
        if re.match(r"^(Figure|Fig\.|Table|Listing)\s+\d+", text, re.IGNORECASE):
            return ContentType.CAPTION

        # Check for code (monospace fonts)
        if any(m in font.lower() for m in ["mono", "courier", "consolas", "menlo"]):
            return ContentType.CODE

        return ContentType.TEXT

    def _page_has_images(self, page: fitz.Page) -> bool:
        """Check if page contains images."""
        return len(page.get_images()) > 0

    def get_document_metadata(self, doc: fitz.Document) -> dict[str, Any]:
        """Extract document-level metadata."""
        metadata = doc.metadata or {}
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "keywords": metadata.get("keywords", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
            "page_count": len(doc),
            "is_encrypted": doc.is_encrypted,
        }

    def get_toc(self, doc: fitz.Document) -> list[dict[str, Any]]:
        """
        Extract table of contents from PDF.

        Returns:
            List of TOC entries with level, title, and page number
        """
        toc = doc.get_toc()
        return [
            {"level": level, "title": title, "page": page}
            for level, title, page in toc
        ]
