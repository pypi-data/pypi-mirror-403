"""
OCR processing using PaddleOCR.

Handles text extraction from scanned PDF pages and images.
"""

import asyncio
from pathlib import Path
from typing import Any

import numpy as np
import structlog
from PIL import Image

from pdf2tex.extraction.models import BoundingBox, ContentType, TextBlock

logger = structlog.get_logger(__name__)


class OCRProcessor:
    """
    OCR processing for scanned content using PaddleOCR.
    
    Provides high-accuracy text recognition for pages that lack
    native text content.
    """

    def __init__(
        self,
        language: str = "en",
        use_gpu: bool = True,
        det_model_dir: str | None = None,
        rec_model_dir: str | None = None,
    ) -> None:
        """
        Initialize OCR processor.

        Args:
            language: Language code for OCR
            use_gpu: Whether to use GPU acceleration
            det_model_dir: Custom detection model directory
            rec_model_dir: Custom recognition model directory
        """
        self.language = language
        self.use_gpu = use_gpu
        self.det_model_dir = det_model_dir
        self.rec_model_dir = rec_model_dir
        
        self._ocr = None

    async def initialize(self) -> None:
        """Initialize OCR engine asynchronously."""
        await asyncio.to_thread(self._load_ocr)

    def _load_ocr(self) -> None:
        """Load PaddleOCR engine."""
        try:
            from paddleocr import PaddleOCR
            
            logger.info("Initializing PaddleOCR", language=self.language, gpu=self.use_gpu)
            
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.language,
                use_gpu=self.use_gpu,
                show_log=False,
                det_model_dir=self.det_model_dir,
                rec_model_dir=self.rec_model_dir,
            )
            
            logger.info("PaddleOCR initialized successfully")
            
        except ImportError as e:
            logger.error("Failed to import PaddleOCR", error=str(e))
            raise
        except Exception as e:
            logger.error("Failed to initialize PaddleOCR", error=str(e))
            raise

    async def process_image(
        self,
        image: Image.Image | np.ndarray | Path,
    ) -> list[TextBlock]:
        """
        Run OCR on an image.

        Args:
            image: PIL Image, numpy array, or path to image

        Returns:
            List of extracted text blocks
        """
        if self._ocr is None:
            await self.initialize()

        # Convert to numpy array if needed
        if isinstance(image, Path):
            image = Image.open(image)
        if isinstance(image, Image.Image):
            image_array = np.array(image)
        else:
            image_array = image

        # Run OCR
        results = await asyncio.to_thread(self._run_ocr, image_array)

        # Convert to TextBlocks
        text_blocks = self._convert_results(results)

        return text_blocks

    def _run_ocr(self, image: np.ndarray) -> list[Any]:
        """Run OCR inference."""
        if self._ocr is None:
            raise RuntimeError("OCR not initialized")
        
        result = self._ocr.ocr(image, cls=True)
        return result[0] if result and result[0] else []

    def _convert_results(self, results: list[Any]) -> list[TextBlock]:
        """Convert PaddleOCR results to TextBlocks."""
        text_blocks: list[TextBlock] = []

        for item in results:
            if not item or len(item) < 2:
                continue

            # PaddleOCR format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]], (text, confidence)
            points, (text, confidence) = item

            if not text or not text.strip():
                continue

            # Convert polygon to bounding box
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            bbox = BoundingBox(
                x0=min(x_coords),
                y0=min(y_coords),
                x1=max(x_coords),
                y1=max(y_coords),
            )

            text_block = TextBlock(
                content=text.strip(),
                content_type=ContentType.TEXT,
                bbox=bbox,
                confidence=float(confidence),
                metadata={"source": "paddleocr", "polygon": points},
            )
            text_blocks.append(text_block)

        return text_blocks

    async def process_page(
        self,
        page_image: Image.Image,
        page_num: int,
    ) -> tuple[list[TextBlock], str]:
        """
        Process a full page image.

        Args:
            page_image: PIL Image of the page
            page_num: Page number for metadata

        Returns:
            Tuple of (text_blocks, raw_text)
        """
        text_blocks = await self.process_image(page_image)

        # Sort blocks by position (top to bottom, left to right)
        text_blocks.sort(key=lambda b: (b.bbox.y0, b.bbox.x0))

        # Generate raw text
        raw_text = "\n".join(block.content for block in text_blocks)

        # Add page number to metadata
        for block in text_blocks:
            block.metadata["page"] = page_num

        return text_blocks, raw_text

    async def batch_process(
        self,
        images: list[Image.Image],
    ) -> list[list[TextBlock]]:
        """
        Process multiple images in batch.

        Args:
            images: List of PIL Images

        Returns:
            List of text blocks per image
        """
        results = await asyncio.gather(
            *[self.process_image(img) for img in images]
        )
        return list(results)

    def detect_text_regions(
        self,
        image: Image.Image | np.ndarray,
    ) -> list[BoundingBox]:
        """
        Detect text regions without full OCR.

        Args:
            image: Input image

        Returns:
            List of bounding boxes for text regions
        """
        if self._ocr is None:
            raise RuntimeError("OCR not initialized")

        if isinstance(image, Image.Image):
            image = np.array(image)

        # Run only detection
        det_result = self._ocr.ocr(image, det=True, rec=False, cls=False)
        
        regions: list[BoundingBox] = []
        if det_result and det_result[0]:
            for points in det_result[0]:
                x_coords = [p[0] for p in points]
                y_coords = [p[1] for p in points]
                regions.append(BoundingBox(
                    x0=min(x_coords),
                    y0=min(y_coords),
                    x1=max(x_coords),
                    y1=max(y_coords),
                ))

        return regions

    def is_scanned_page(
        self,
        page_image: Image.Image,
        native_char_count: int,
        threshold: int = 50,
    ) -> bool:
        """
        Determine if a page is scanned (needs OCR).

        Args:
            page_image: Image of the page
            native_char_count: Character count from native extraction
            threshold: Minimum chars to consider as native text

        Returns:
            True if page appears to be scanned
        """
        # If we have substantial native text, no need for OCR
        if native_char_count >= threshold:
            return False

        # Check if page has text regions
        regions = self.detect_text_regions(page_image)
        return len(regions) > 0

    def get_supported_languages(self) -> list[str]:
        """Get list of supported OCR languages."""
        return [
            "en", "ch", "french", "german", "korean", "japan",
            "chinese_cht", "ta", "te", "ka", "latin", "arabic",
            "cyrillic", "devanagari",
        ]

    def get_info(self) -> dict[str, Any]:
        """Get OCR processor information."""
        return {
            "language": self.language,
            "use_gpu": self.use_gpu,
            "initialized": self._ocr is not None,
            "supported_languages": self.get_supported_languages(),
        }
