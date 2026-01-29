"""
Extraction layer for PDF2TeX.

This module handles PDF content extraction including text, images,
tables, and mathematical equations.
"""

from pdf2tex.extraction.math_extractor import MathExtractor
from pdf2tex.extraction.models import (
    BoundingBox,
    ContentType,
    ExtractionResult,
    ExtractedPage,
    FigureRegion,
    MathRegion,
    PageMetadata,
    TableRegion,
    TextBlock,
)
from pdf2tex.extraction.ocr import OCRProcessor
from pdf2tex.extraction.pdf_parser import PDFParser
from pdf2tex.extraction.service import ExtractionService

__all__ = [
    # Models
    "BoundingBox",
    "ContentType",
    "ExtractionResult",
    "ExtractedPage",
    "FigureRegion",
    "MathRegion",
    "PageMetadata",
    "TableRegion",
    "TextBlock",
    # Components
    "MathExtractor",
    "OCRProcessor",
    "PDFParser",
    # Service
    "ExtractionService",
]
