"""
Extraction service coordinating all extraction components.

Provides unified interface for PDF content extraction.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog
from PIL import Image

from pdf2tex.config import ExtractionSettings, Settings
from pdf2tex.extraction.math_extractor import MathExtractor
from pdf2tex.extraction.models import (
    ContentType,
    ExtractionResult,
    ExtractedPage,
    MathRegion,
    PageMetadata,
    TextBlock,
)
from pdf2tex.extraction.ocr import OCRProcessor
from pdf2tex.extraction.pdf_parser import PDFParser

logger = structlog.get_logger(__name__)


@dataclass
class ExtractionProgress:
    """Progress information for extraction."""

    current_page: int
    total_pages: int
    phase: str
    message: str


class ExtractionService:
    """
    Orchestrates PDF extraction using multiple components.
    
    Coordinates:
    - PDF parsing (native text, images, TOC)
    - Math extraction (Nougat neural model)
    - OCR (PaddleOCR for scanned pages)
    """

    def __init__(
        self,
        settings: Settings | None = None,
    ) -> None:
        """
        Initialize extraction service.

        Args:
            settings: Application settings
        """
        self.settings = settings or Settings()
        self.extraction_settings: ExtractionSettings = self.settings.extraction

        # Initialize components
        self._pdf_parser: PDFParser | None = None
        self._math_extractor: MathExtractor | None = None
        self._ocr_processor: OCRProcessor | None = None
        
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all extraction components."""
        if self._initialized:
            return

        logger.info("Initializing extraction service")

        # Initialize math extractor
        if self.extraction_settings.use_nougat:
            self._math_extractor = MathExtractor(
                model_name=self.extraction_settings.nougat_model,
                device=self.extraction_settings.device,
            )
            await self._math_extractor.initialize()

        # Initialize OCR processor
        self._ocr_processor = OCRProcessor(
            language="en",
            use_gpu=self.extraction_settings.device.startswith("cuda"),
        )
        await self._ocr_processor.initialize()

        self._initialized = True
        logger.info("Extraction service initialized")

    async def extract(
        self,
        pdf_path: Path | str,
        progress_callback: Any | None = None,
    ) -> ExtractionResult:
        """
        Extract all content from a PDF.

        Args:
            pdf_path: Path to PDF file
            progress_callback: Optional callback for progress updates

        Returns:
            Complete extraction result
        """
        if not self._initialized:
            await self.initialize()

        pdf_path = Path(pdf_path)
        logger.info("Starting extraction", pdf_path=str(pdf_path))

        # Open PDF
        pdf_parser = PDFParser(pdf_path)

        try:
            # Get metadata
            metadata = pdf_parser.get_metadata()
            toc = pdf_parser.extract_toc()
            total_pages = pdf_parser.page_count

            logger.info(
                "PDF opened",
                pages=total_pages,
                title=metadata.get("title"),
            )

            # Process pages
            pages: list[ExtractedPage] = []
            batch_size = self.extraction_settings.extraction_batch_size

            for batch_start in range(0, total_pages, batch_size):
                batch_end = min(batch_start + batch_size, total_pages)
                
                # Report progress
                if progress_callback:
                    progress = ExtractionProgress(
                        current_page=batch_start,
                        total_pages=total_pages,
                        phase="extraction",
                        message=f"Processing pages {batch_start + 1}-{batch_end}",
                    )
                    await progress_callback(progress)

                # Process batch
                batch_pages = await self._process_batch(
                    pdf_parser,
                    list(range(batch_start, batch_end)),
                )
                pages.extend(batch_pages)

            # Create result
            result = ExtractionResult(
                source_path=pdf_path,
                pages=pages,
                metadata=metadata,
                table_of_contents=toc,
            )

            logger.info(
                "Extraction complete",
                pages=len(pages),
                total_chars=result.total_chars,
            )

            return result

        finally:
            pdf_parser.close()

    async def _process_batch(
        self,
        parser: PDFParser,
        page_numbers: list[int],
    ) -> list[ExtractedPage]:
        """
        Process a batch of pages.

        Args:
            parser: PDF parser instance
            page_numbers: Page numbers to process

        Returns:
            List of extracted pages
        """
        # Render page images for math extraction and OCR
        page_images: list[Image.Image] = []
        for page_num in page_numbers:
            img = parser.render_page(
                page_num,
                dpi=self.extraction_settings.dpi,
            )
            page_images.append(img)

        # Extract native text first
        native_extractions = [
            parser.extract_page(page_num)
            for page_num in page_numbers
        ]

        # Extract math content
        math_regions_list: list[list[MathRegion]] = []
        if self._math_extractor and self.extraction_settings.use_nougat:
            math_regions_list = await self._math_extractor.batch_extract(
                page_images, page_numbers
            )
        else:
            math_regions_list = [[] for _ in page_numbers]

        # Check for scanned pages needing OCR
        ocr_results: list[tuple[list[TextBlock], str]] = []
        for i, (page_num, native) in enumerate(zip(page_numbers, native_extractions)):
            native_char_count = sum(
                len(block.content)
                for block in native["text_blocks"]
            )
            
            if (
                self._ocr_processor
                and self._ocr_processor.is_scanned_page(
                    page_images[i],
                    native_char_count,
                    threshold=self.extraction_settings.min_text_length,
                )
            ):
                logger.debug("Scanned page detected, running OCR", page=page_num)
                ocr_blocks, ocr_text = await self._ocr_processor.process_page(
                    page_images[i], page_num
                )
                ocr_results.append((ocr_blocks, ocr_text))
            else:
                ocr_results.append(([], ""))

        # Combine results
        extracted_pages: list[ExtractedPage] = []
        for i, page_num in enumerate(page_numbers):
            native = native_extractions[i]
            math_regions = math_regions_list[i]
            ocr_blocks, ocr_text = ocr_results[i]

            # Merge text blocks
            text_blocks = native["text_blocks"]
            if ocr_blocks:
                text_blocks = self._merge_text_blocks(text_blocks, ocr_blocks)

            # Build raw text
            if ocr_text:
                raw_text = ocr_text
            else:
                raw_text = "\n".join(
                    block.content for block in text_blocks
                )

            # Create page metadata
            page_meta = PageMetadata(
                page_number=page_num,
                width=native["width"],
                height=native["height"],
                has_images=len(native["images"]) > 0,
                has_tables=any(
                    block.content_type == ContentType.TABLE
                    for block in text_blocks
                ),
                has_math=len(math_regions) > 0,
                char_count=len(raw_text),
            )

            page = ExtractedPage(
                page_number=page_num,
                text_blocks=text_blocks,
                math_regions=math_regions,
                figure_regions=native.get("figures", []),
                table_regions=native.get("tables", []),
                images=native["images"],
                raw_text=raw_text,
                metadata=page_meta,
            )
            extracted_pages.append(page)

        return extracted_pages

    def _merge_text_blocks(
        self,
        native_blocks: list[TextBlock],
        ocr_blocks: list[TextBlock],
    ) -> list[TextBlock]:
        """
        Merge native and OCR text blocks.

        Args:
            native_blocks: Blocks from native extraction
            ocr_blocks: Blocks from OCR

        Returns:
            Merged list of text blocks
        """
        if not native_blocks:
            return ocr_blocks
        if not ocr_blocks:
            return native_blocks

        # Use OCR blocks for regions not covered by native
        merged = list(native_blocks)
        
        for ocr_block in ocr_blocks:
            # Check if OCR block overlaps with any native block
            overlaps = False
            for native_block in native_blocks:
                if ocr_block.bbox.overlaps(native_block.bbox):
                    overlaps = True
                    break
            
            if not overlaps:
                merged.append(ocr_block)

        # Sort by position
        merged.sort(key=lambda b: (b.bbox.y0, b.bbox.x0))
        return merged

    async def extract_pages(
        self,
        pdf_path: Path | str,
        page_numbers: list[int],
    ) -> list[ExtractedPage]:
        """
        Extract specific pages from a PDF.

        Args:
            pdf_path: Path to PDF file
            page_numbers: Page numbers to extract

        Returns:
            List of extracted pages
        """
        if not self._initialized:
            await self.initialize()

        pdf_path = Path(pdf_path)
        pdf_parser = PDFParser(pdf_path)

        try:
            return await self._process_batch(pdf_parser, page_numbers)
        finally:
            pdf_parser.close()

    async def extract_text_only(
        self,
        pdf_path: Path | str,
    ) -> str:
        """
        Quick text-only extraction.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Concatenated text from all pages
        """
        pdf_path = Path(pdf_path)
        pdf_parser = PDFParser(pdf_path)

        try:
            all_text: list[str] = []
            for page_num in range(pdf_parser.page_count):
                extraction = pdf_parser.extract_page(page_num)
                page_text = "\n".join(
                    block.content
                    for block in extraction["text_blocks"]
                )
                all_text.append(page_text)
            return "\n\n".join(all_text)
        finally:
            pdf_parser.close()

    def get_pdf_info(
        self,
        pdf_path: Path | str,
    ) -> dict[str, Any]:
        """
        Get basic PDF information without full extraction.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with PDF metadata
        """
        pdf_path = Path(pdf_path)
        pdf_parser = PDFParser(pdf_path)

        try:
            metadata = pdf_parser.get_metadata()
            toc = pdf_parser.extract_toc()
            
            return {
                "path": str(pdf_path),
                "page_count": pdf_parser.page_count,
                "metadata": metadata,
                "table_of_contents": toc,
                "has_toc": len(toc) > 0,
            }
        finally:
            pdf_parser.close()

    def get_status(self) -> dict[str, Any]:
        """Get service status."""
        return {
            "initialized": self._initialized,
            "components": {
                "math_extractor": self._math_extractor is not None,
                "ocr_processor": self._ocr_processor is not None,
            },
            "settings": {
                "use_nougat": self.extraction_settings.use_nougat,
                "device": self.extraction_settings.device,
                "batch_size": self.extraction_settings.extraction_batch_size,
            },
        }

    async def close(self) -> None:
        """Clean up resources."""
        self._pdf_parser = None
        self._math_extractor = None
        self._ocr_processor = None
        self._initialized = False
        logger.info("Extraction service closed")
