"""
Tests for PDF2TeX extraction layer.
Tests match actual implementation APIs.
"""

import pytest
from pathlib import Path

from pdf2tex.extraction.models import (
    BoundingBox,
    ContentType,
    TextBlock,
    MathRegion,
    PageMetadata,
)


class TestBoundingBox:
    """Tests for BoundingBox model."""

    def test_create_bbox(self) -> None:
        """Test bounding box creation."""
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=50)
        assert bbox.width == 100
        assert bbox.height == 50
        assert bbox.area == 5000

    def test_bbox_to_tuple(self) -> None:
        """Test bounding box tuple conversion."""
        bbox = BoundingBox(x0=10, y0=20, x1=30, y1=40)
        assert bbox.to_tuple() == (10, 20, 30, 40)

    def test_bbox_overlaps(self) -> None:
        """Test bounding box overlap detection."""
        bbox1 = BoundingBox(x0=0, y0=0, x1=100, y1=100)
        bbox2 = BoundingBox(x0=50, y0=50, x1=150, y1=150)
        bbox3 = BoundingBox(x0=200, y0=200, x1=300, y1=300)

        # bbox1 and bbox2 overlap significantly
        assert bbox1.overlaps(bbox2, threshold=0.1)
        # bbox1 and bbox3 don't overlap
        assert not bbox1.overlaps(bbox3)


class TestTextBlock:
    """Tests for TextBlock model."""

    def test_create_text_block(self) -> None:
        """Test text block creation."""
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=20)
        block = TextBlock(
            content="Hello World",
            content_type=ContentType.TEXT,
            bbox=bbox,
        )
        assert block.content == "Hello World"
        assert block.content_type == ContentType.TEXT
        assert block.char_count == 11

    def test_text_block_is_heading(self) -> None:
        """Test heading detection."""
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=20)
        heading = TextBlock(
            content="Chapter 1",
            content_type=ContentType.HEADING,
            bbox=bbox,
        )
        text = TextBlock(
            content="Normal text",
            content_type=ContentType.TEXT,
            bbox=bbox,
        )
        
        assert heading.is_heading
        assert not text.is_heading

    def test_text_block_confidence(self) -> None:
        """Test text block confidence."""
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=20)
        block = TextBlock(
            content="Test",
            content_type=ContentType.TEXT,
            bbox=bbox,
            confidence=0.95,
        )
        assert block.confidence == 0.95


class TestMathRegion:
    """Tests for MathRegion model."""

    def test_create_math_region(self) -> None:
        """Test math region creation."""
        bbox = BoundingBox(x0=0, y0=0, x1=200, y1=50)
        math = MathRegion(
            latex=r"\int_0^1 x^2 dx",
            content_type=ContentType.MATH_DISPLAY,
            bbox=bbox,
        )
        assert math.latex == r"\int_0^1 x^2 dx"
        assert math.is_display

    def test_inline_math(self) -> None:
        """Test inline math detection."""
        bbox = BoundingBox(x0=0, y0=0, x1=50, y1=20)
        inline = MathRegion(
            latex=r"x^2",
            content_type=ContentType.MATH_INLINE,
            bbox=bbox,
        )
        display = MathRegion(
            latex=r"x^2",
            content_type=ContentType.MATH_DISPLAY,
            bbox=bbox,
        )
        
        assert inline.is_inline
        assert not inline.is_display
        assert display.is_display
        assert not display.is_inline


class TestContentType:
    """Tests for ContentType enum."""

    def test_content_types(self) -> None:
        """Test content type values."""
        assert ContentType.TEXT.value == "text"
        assert ContentType.MATH_INLINE.value == "math_inline"
        assert ContentType.MATH_DISPLAY.value == "math_display"
        assert ContentType.TABLE.value == "table"
        assert ContentType.HEADING.value == "heading"


class TestPageMetadata:
    """Tests for PageMetadata model."""

    def test_create_metadata(self) -> None:
        """Test page metadata creation."""
        meta = PageMetadata(
            page_number=1,
            width=612.0,
            height=792.0,
        )
        assert meta.page_number == 1
        assert meta.width == 612.0
        assert meta.height == 792.0

    def test_metadata_flags(self) -> None:
        """Test metadata boolean flags."""
        meta = PageMetadata(
            page_number=1,
            width=612.0,
            height=792.0,
            has_text=True,
            has_images=True,
            is_scanned=False,
        )
        assert meta.has_text
        assert meta.has_images
        assert not meta.is_scanned


# ============================================================================
# Integration Tests (require real PDF)
# ============================================================================

@pytest.mark.integration
class TestPDFParserIntegration:
    """Integration tests with real PDF files."""
    
    TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"

    @pytest.fixture
    def attention_pdf(self) -> Path:
        """Get attention paper PDF path."""
        pdf_path = self.TEST_DATA_DIR / "attention.pdf"
        if not pdf_path.exists():
            pytest.skip("Test PDF not available")
        return pdf_path

    def test_open_document(self, attention_pdf: Path) -> None:
        """Test opening PDF document."""
        from pdf2tex.extraction.pdf_parser import PDFParser
        
        parser = PDFParser()
        doc = parser.open_document(attention_pdf)
        
        assert doc.page_count == 15
        doc.close()

    def test_extract_page_text(self, attention_pdf: Path) -> None:
        """Test extracting text from a page."""
        from pdf2tex.extraction.pdf_parser import PDFParser
        
        parser = PDFParser()
        doc = parser.open_document(attention_pdf)
        
        text_blocks, metadata = parser.extract_page_text(doc, 0)
        
        assert len(text_blocks) > 0
        assert metadata.page_number == 1
        assert metadata.has_text
        
        # Check content
        full_text = " ".join(b.content for b in text_blocks)
        assert "attention" in full_text.lower()
        
        doc.close()

    def test_get_toc(self, attention_pdf: Path) -> None:
        """Test table of contents extraction."""
        from pdf2tex.extraction.pdf_parser import PDFParser
        
        parser = PDFParser()
        doc = parser.open_document(attention_pdf)
        
        toc = parser.get_toc(doc)
        # arXiv papers may or may not have embedded TOC
        assert isinstance(toc, list)
        
        doc.close()

    def test_get_document_metadata(self, attention_pdf: Path) -> None:
        """Test document metadata extraction."""
        from pdf2tex.extraction.pdf_parser import PDFParser
        
        parser = PDFParser()
        doc = parser.open_document(attention_pdf)
        
        metadata = parser.get_document_metadata(doc)
        
        assert "page_count" in metadata
        assert metadata["page_count"] == 15
        assert "creator" in metadata
        
        doc.close()
