#!/usr/bin/env python3
"""
Script to run the PDF2TeX development server.
"""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import uvicorn


def main() -> None:
    """Run the development server."""
    uvicorn.run(
        "pdf2tex.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src/pdf2tex"],
        log_level="info",
    )


if __name__ == "__main__":
    main()
