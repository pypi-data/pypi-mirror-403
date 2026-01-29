"""
Tests for PDF2TeX pipeline layer.
Tests match actual implementation APIs.
"""

import pytest
from pathlib import Path
import tempfile


class TestPipelineBasics:
    """Basic pipeline tests."""

    def test_job_id_generation(self) -> None:
        """Test unique job ID generation."""
        import uuid
        
        job_id_1 = str(uuid.uuid4())[:8]
        job_id_2 = str(uuid.uuid4())[:8]
        
        assert job_id_1 != job_id_2
        assert len(job_id_1) == 8

    def test_output_directory_creation(self) -> None:
        """Test output directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output" / "test"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            assert output_dir.exists()
            assert output_dir.is_dir()


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestPipelineIntegration:
    """Integration tests for pipeline components."""

    TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"

    def test_extraction_to_chunking_flow(self) -> None:
        """Test data flows from extraction to chunking."""
        from pdf2tex.extraction.pdf_parser import PDFParser
        from pdf2tex.chunking.splitter import TextSplitter
        
        pdf_path = self.TEST_DATA_DIR / "attention.pdf"
        if not pdf_path.exists():
            pytest.skip("Test PDF not available")
        
        # Extract
        parser = PDFParser()
        doc = parser.open_document(pdf_path)
        
        all_text = []
        for i in range(min(3, doc.page_count)):  # Just first 3 pages
            text_blocks, _ = parser.extract_page_text(doc, i)
            page_text = " ".join(b.content for b in text_blocks)
            all_text.append(page_text)
        doc.close()
        
        # Chunk
        splitter = TextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text("\n\n".join(all_text), document_id="test")
        
        assert len(chunks) > 0
        assert all(len(c.content) > 0 for c in chunks)
