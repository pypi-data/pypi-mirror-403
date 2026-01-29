"""
Pytest configuration and fixtures for PDF2TeX tests.
"""

import pytest
from pathlib import Path
from typing import Generator, Any
import tempfile
import shutil
from unittest.mock import Mock, MagicMock


# ============================================================================
# Path Fixtures
# ============================================================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    tmpdir = tempfile.mkdtemp(prefix="pdf2tex_test_")
    yield Path(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def sample_pdf_path(temp_dir: Path) -> Path:
    """Create a sample PDF path (not actual PDF)."""
    pdf_path = temp_dir / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 mock content")
    return pdf_path


@pytest.fixture
def output_dir(temp_dir: Path) -> Path:
    """Create output directory for test results."""
    output = temp_dir / "output"
    output.mkdir(parents=True, exist_ok=True)
    return output


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def mock_settings() -> dict[str, Any]:
    """Create mock settings for testing."""
    return {
        "extraction": {
            "device": "cpu",
            "batch_size": 2,
            "use_nougat": False,  # Disable for unit tests
            "use_ocr": False,
        },
        "chunking": {
            "chunk_size": 1000,
            "chunk_overlap": 100,
        },
        "rag": {
            "embedding_model": "test-model",
            "top_k": 5,
        },
        "generation": {
            "model_name": "test-model",
            "max_tokens": 1000,
        },
        "pipeline": {
            "num_workers": 1,
            "use_ray": False,
        },
    }


# ============================================================================
# Mock Model Fixtures
# ============================================================================

@pytest.fixture
def mock_embedding_model() -> Mock:
    """Create mock embedding model."""
    model = Mock()
    model.encode.return_value = [[0.1] * 1024]  # BGE-M3 dimension
    return model


@pytest.fixture
def mock_llm_response() -> Mock:
    """Create mock LLM response."""
    response = Mock()
    response.generated_text = r"\section{Test}\nContent here."
    return response


@pytest.fixture
def mock_cross_encoder() -> Mock:
    """Create mock cross-encoder model."""
    model = Mock()
    model.predict.return_value = [0.9, 0.7, 0.5]
    return model


# ============================================================================
# Data Fixtures
# ============================================================================

@pytest.fixture
def sample_text_blocks() -> list[dict[str, Any]]:
    """Create sample text blocks."""
    return [
        {
            "text": "Chapter 1: Introduction",
            "bbox": {"x0": 0, "y0": 0, "x1": 100, "y1": 20},
            "font_size": 24,
            "is_bold": True,
        },
        {
            "text": "This is the first paragraph of the introduction.",
            "bbox": {"x0": 0, "y0": 30, "x1": 200, "y1": 50},
            "font_size": 12,
            "is_bold": False,
        },
        {
            "text": "The equation $E = mc^2$ is famous.",
            "bbox": {"x0": 0, "y0": 60, "x1": 200, "y1": 80},
            "font_size": 12,
            "is_bold": False,
        },
    ]


@pytest.fixture
def sample_chunks() -> list[dict[str, Any]]:
    """Create sample chunks for testing."""
    return [
        {
            "id": "chunk_001",
            "content": "Introduction to the topic.",
            "metadata": {
                "document_id": "test_doc",
                "chapter_id": "ch1",
                "has_math": False,
            },
        },
        {
            "id": "chunk_002",
            "content": "The equation $x^2 + y^2 = r^2$ represents a circle.",
            "metadata": {
                "document_id": "test_doc",
                "chapter_id": "ch1",
                "has_math": True,
            },
        },
    ]


@pytest.fixture
def sample_latex_valid() -> str:
    """Valid LaTeX document for testing."""
    return r"""
\documentclass{article}
\usepackage{amsmath}

\begin{document}

\section{Introduction}

This is a test document. The equation $E = mc^2$ is famous.

\begin{equation}
    \int_0^1 x^2 dx = \frac{1}{3}
\end{equation}

\end{document}
"""


@pytest.fixture
def sample_latex_invalid() -> str:
    """Invalid LaTeX document for testing validation."""
    return r"""
\documentclass{article}

\begin{document}

\section{Introduction

Missing closing brace above.

\begin{itemize}
\item First item
% Missing \end{itemize}

Unclosed math: $x^2 + y^2

\end{document}
"""


# ============================================================================
# Async Fixtures
# ============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Skip Markers
# ============================================================================

def pytest_configure(config: pytest.Config) -> None:
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (require real PDFs)",
    )
    config.addinivalue_line(
        "markers",
        "requires_gpu: marks tests that require GPU",
    )
    config.addinivalue_line(
        "markers",
        "requires_api: marks tests that require external API (HuggingFace)",
    )
    config.addinivalue_line(
        "markers",
        "requires_services: marks tests that require Docker services (Qdrant, Redis)",
    )


# ============================================================================
# Test Utilities
# ============================================================================

def assert_valid_latex(latex: str) -> None:
    """Assert that LaTeX string has balanced delimiters."""
    # Check braces
    assert latex.count("{") == latex.count("}"), "Unbalanced braces"
    
    # Check brackets
    assert latex.count("[") == latex.count("]"), "Unbalanced brackets"
    
    # Check inline math
    dollar_count = latex.count("$") - latex.count(r"\$")
    assert dollar_count % 2 == 0, "Unbalanced $ delimiters"


def create_mock_pdf_content(num_pages: int = 10) -> list[dict[str, Any]]:
    """Create mock PDF content for testing."""
    pages = []
    for i in range(num_pages):
        pages.append({
            "page_num": i,
            "text": f"Page {i + 1} content. " * 100,
            "images": [],
            "tables": [],
        })
    return pages
