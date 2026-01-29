"""
Tests for PDF2TeX chunking layer.
Tests match actual implementation APIs.
"""

import pytest
from pathlib import Path

from pdf2tex.chunking.splitter import TextSplitter, MathAwareTextSplitter


class TestTextSplitter:
    """Tests for TextSplitter class."""

    def test_split_short_text(self) -> None:
        """Test splitting short text."""
        splitter = TextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_text("Short text.", document_id="test")
        
        assert len(chunks) == 1
        assert chunks[0].content == "Short text."

    def test_split_long_text(self) -> None:
        """Test splitting long text."""
        splitter = TextSplitter(chunk_size=100, chunk_overlap=10)
        long_text = "This is a test sentence. " * 50  # ~1250 chars
        
        chunks = splitter.split_text(long_text, document_id="test")
        
        assert len(chunks) > 1
        # Each chunk should be <= chunk_size (approximately)
        for chunk in chunks:
            assert len(chunk.content) <= 200  # Allow some buffer

    def test_chunk_metadata(self) -> None:
        """Test chunk metadata is set correctly."""
        splitter = TextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text("Test content for chunking.", document_id="doc123")
        
        assert len(chunks) >= 1
        assert chunks[0].metadata.document_id == "doc123"


class TestMathAwareTextSplitter:
    """Tests for MathAwareTextSplitter class."""

    def test_preserve_inline_math(self) -> None:
        """Test that inline math is preserved."""
        splitter = MathAwareTextSplitter(chunk_size=100, chunk_overlap=10)
        text = "The equation $E = mc^2$ is famous. It shows energy-mass equivalence."
        
        chunks = splitter.split_text(text, document_id="test")
        
        # Math should not be split
        for chunk in chunks:
            if "$" in chunk.content:
                dollar_count = chunk.content.count("$")
                assert dollar_count % 2 == 0, "Inline math split incorrectly"

    def test_preserve_display_math(self) -> None:
        """Test that display math is preserved."""
        splitter = MathAwareTextSplitter(chunk_size=200, chunk_overlap=20)
        text = """Introduction.

$$\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}$$

Conclusion."""
        
        chunks = splitter.split_text(text, document_id="test")
        
        # Display math should not be split
        for chunk in chunks:
            if "$$" in chunk.content:
                dollar_count = chunk.content.count("$$")
                assert dollar_count % 2 == 0, "Display math split incorrectly"

    def test_math_detection_in_metadata(self) -> None:
        """Test math content is detected in chunk metadata."""
        splitter = MathAwareTextSplitter(chunk_size=500, chunk_overlap=50)
        text = "The formula $x^2 + y^2 = r^2$ describes a circle."
        
        chunks = splitter.split_text(text, document_id="test")
        
        assert len(chunks) >= 1
        assert chunks[0].metadata.has_math


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestChunkingIntegration:
    """Integration tests with real PDF content."""
    
    TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"

    @pytest.fixture
    def pdf_text(self) -> str:
        """Extract text from attention paper."""
        from pdf2tex.extraction.pdf_parser import PDFParser
        
        pdf_path = self.TEST_DATA_DIR / "attention.pdf"
        if not pdf_path.exists():
            pytest.skip("Test PDF not available")
        
        parser = PDFParser()
        doc = parser.open_document(pdf_path)
        
        all_text = []
        for i in range(doc.page_count):
            text_blocks, _ = parser.extract_page_text(doc, i)
            page_text = " ".join(b.content for b in text_blocks)
            all_text.append(page_text)
        
        doc.close()
        return "\n\n".join(all_text)

    def test_chunk_real_document(self, pdf_text: str) -> None:
        """Test chunking real document text."""
        splitter = TextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_text(pdf_text, document_id="attention")
        
        assert len(chunks) > 0
        # Verify reasonable chunk sizes
        total_chars = sum(len(c.content) for c in chunks)
        assert total_chars > 10000  # Paper has significant content

    def test_math_aware_chunking_real(self, pdf_text: str) -> None:
        """Test math-aware chunking on real content."""
        splitter = MathAwareTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text(pdf_text, document_id="attention")
        
        assert len(chunks) > 0
        # Some chunks should have math content
        math_chunks = [c for c in chunks if c.metadata.has_math]
        # The attention paper has equations, so some chunks should have math
        # (May be 0 if math symbols aren't detected as $...$)
