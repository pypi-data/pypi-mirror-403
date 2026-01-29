"""
PDF2TeX - High-performance RAG-based PDF to LaTeX conversion.

This module provides a complete pipeline for converting large PDF documents
into structured LaTeX files using Retrieval-Augmented Generation.
"""

from pdf2tex.config import Settings
from pdf2tex.pipeline.orchestrator import PDF2TeXOrchestrator

__version__ = "0.1.0"
__all__ = ["PDF2TeXOrchestrator", "Settings", "__version__"]
