"""
API layer for PDF2TeX.

Provides REST API for PDF to LaTeX conversion.
"""

from pdf2tex.api.app import create_app

__all__ = ["create_app"]
