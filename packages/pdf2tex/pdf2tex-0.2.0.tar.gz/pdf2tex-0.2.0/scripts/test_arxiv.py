#!/usr/bin/env python3
"""
Integration test script for PDF2TeX using arXiv papers.

This script tests the complete pipeline on real PDF documents.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

console = Console()


# ============================================================================
# Test Configuration
# ============================================================================

TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"
OUTPUT_DIR = Path(__file__).parent.parent / "test_output"

TEST_PDFS = [
    {
        "name": "Attention Is All You Need",
        "file": "attention.pdf",
        "arxiv_id": "1706.03762",
        "features": ["equations", "figures", "tables", "algorithms"],
        "expected_chapters": 7,  # ~7 sections
    },
    {
        "name": "Adam Optimizer",
        "file": "adam.pdf",
        "arxiv_id": "1412.6980",
        "features": ["dense_math", "algorithms", "theorems"],
        "expected_chapters": 6,
    },
]


# ============================================================================
# Test Helpers
# ============================================================================

def check_pdf_exists(pdf_info: dict) -> bool:
    """Check if test PDF exists."""
    pdf_path = TEST_DATA_DIR / pdf_info["file"]
    return pdf_path.exists()


def get_pdf_info(pdf_path: Path) -> dict:
    """Get basic PDF information."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        info = {
            "pages": doc.page_count,
            "title": doc.metadata.get("title", "Unknown"),
            "author": doc.metadata.get("author", "Unknown"),
            "size_mb": pdf_path.stat().st_size / (1024 * 1024),
        }
        doc.close()
        return info
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# Module Tests
# ============================================================================

async def test_extraction_module(pdf_path: Path) -> dict:
    """Test the extraction module."""
    from pdf2tex.config import Settings
    from pdf2tex.extraction.service import ExtractionService
    
    settings = Settings()
    service = ExtractionService(settings.extraction)
    
    start = time.perf_counter()
    result = await service.extract(pdf_path)
    elapsed = time.perf_counter() - start
    
    # Analyze results
    total_text = sum(len(p.text) for p in result.pages)
    math_regions = sum(len(p.math_regions) for p in result.pages)
    figures = sum(len(p.figures) for p in result.pages)
    tables = sum(len(p.tables) for p in result.pages)
    
    return {
        "success": True,
        "pages": result.total_pages,
        "total_chars": total_text,
        "math_regions": math_regions,
        "figures": figures,
        "tables": tables,
        "time_seconds": elapsed,
        "pages_per_second": result.total_pages / elapsed if elapsed > 0 else 0,
        "result": result,
    }


async def test_chunking_module(extraction_result) -> dict:
    """Test the chunking module."""
    from pdf2tex.config import Settings
    from pdf2tex.chunking.service import ChunkingService
    
    settings = Settings()
    service = ChunkingService(settings.chunking)
    
    start = time.perf_counter()
    result = await service.chunk_extraction_result(extraction_result, document_id="test_doc")
    elapsed = time.perf_counter() - start
    
    # Analyze chunks
    math_chunks = sum(1 for c in result.chunks if c.metadata.has_math)
    avg_chunk_size = sum(len(c.content) for c in result.chunks) / len(result.chunks) if result.chunks else 0
    
    return {
        "success": True,
        "total_chunks": len(result.chunks),
        "chapters_detected": len(result.chapters),
        "math_chunks": math_chunks,
        "avg_chunk_size": avg_chunk_size,
        "time_seconds": elapsed,
        "result": result,
    }


async def test_embedding_module(chunks: list, sample_size: int = 20) -> dict:
    """Test the embedding module."""
    from pdf2tex.config import Settings
    from pdf2tex.rag.embeddings import EmbeddingClient
    
    settings = Settings()
    client = EmbeddingClient(
        model_name=settings.rag.embedding_model,
        device=str(settings.extraction.device),
    )
    
    # Test on sample
    sample_chunks = chunks[:sample_size]
    texts = [c.content for c in sample_chunks]
    
    start = time.perf_counter()
    embeddings = client.embed_texts(texts)
    elapsed = time.perf_counter() - start
    
    return {
        "success": True,
        "texts_embedded": len(texts),
        "embedding_dim": len(embeddings[0]) if embeddings else 0,
        "time_seconds": elapsed,
        "texts_per_second": len(texts) / elapsed if elapsed > 0 else 0,
    }


async def test_validator_module(sample_latex: str = None) -> dict:
    """Test the LaTeX validator module."""
    from pdf2tex.generation.validator import LaTeXValidator
    
    validator = LaTeXValidator()
    
    # Test with sample LaTeX
    if sample_latex is None:
        sample_latex = r"""
\documentclass{article}
\usepackage{amsmath}
\begin{document}
\section{Introduction}
The famous equation $E = mc^2$ relates energy and mass.
\begin{equation}
    \int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
\end{equation}
\end{document}
"""
    
    start = time.perf_counter()
    result = await validator.validate(sample_latex)
    elapsed = time.perf_counter() - start
    
    # Test quick_check
    quick_result = validator.quick_check(sample_latex)
    
    # Test repair
    broken_latex = r"\begin{equation} x^2 \begin{itemize}"
    repaired, repairs = validator.repair_common_issues(broken_latex)
    
    return {
        "success": True,
        "validation_passed": result.valid,
        "errors": len(result.errors),
        "warnings": len(result.warnings),
        "quick_check_passed": quick_result,
        "repair_test_fixes": len(repairs),
        "time_seconds": elapsed,
    }


async def test_llm_connection() -> dict:
    """Test LLM API connection (without full generation)."""
    from pdf2tex.config import Settings
    import httpx
    
    settings = Settings()
    token = settings.generation.huggingface_api_token
    
    if not token:
        return {"success": False, "error": "No HuggingFace token configured"}
    
    # Test API connectivity
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api-inference.huggingface.co/models/{settings.generation.model_name}",
                headers={"Authorization": f"Bearer {token.get_secret_value()}"},
                timeout=10,
            )
            
            if resp.status_code == 200:
                return {"success": True, "model": settings.generation.model_name, "status": "ready"}
            elif resp.status_code == 503:
                return {"success": True, "model": settings.generation.model_name, "status": "loading"}
            else:
                return {"success": False, "status_code": resp.status_code}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# Main Test Runner
# ============================================================================

async def run_module_tests(pdf_path: Path) -> dict:
    """Run all module tests on a PDF."""
    results = {}
    
    # Test extraction
    console.print("\n[bold cyan]Testing Extraction Module...[/bold cyan]")
    try:
        results["extraction"] = await test_extraction_module(pdf_path)
        console.print(f"  ✓ Extracted {results['extraction']['pages']} pages in {results['extraction']['time_seconds']:.2f}s")
        console.print(f"    - Math regions: {results['extraction']['math_regions']}")
        console.print(f"    - Figures: {results['extraction']['figures']}")
        console.print(f"    - Tables: {results['extraction']['tables']}")
    except Exception as e:
        results["extraction"] = {"success": False, "error": str(e)}
        console.print(f"  ✗ Extraction failed: {e}")
        return results
    
    # Test chunking
    console.print("\n[bold cyan]Testing Chunking Module...[/bold cyan]")
    try:
        results["chunking"] = await test_chunking_module(results["extraction"]["result"])
        console.print(f"  ✓ Created {results['chunking']['total_chunks']} chunks in {results['chunking']['time_seconds']:.2f}s")
        console.print(f"    - Chapters detected: {results['chunking']['chapters_detected']}")
        console.print(f"    - Math chunks: {results['chunking']['math_chunks']}")
    except Exception as e:
        results["chunking"] = {"success": False, "error": str(e)}
        console.print(f"  ✗ Chunking failed: {e}")
        return results
    
    # Test embeddings
    console.print("\n[bold cyan]Testing Embedding Module...[/bold cyan]")
    try:
        results["embedding"] = await test_embedding_module(results["chunking"]["result"].chunks)
        console.print(f"  ✓ Embedded {results['embedding']['texts_embedded']} texts in {results['embedding']['time_seconds']:.2f}s")
        console.print(f"    - Embedding dimension: {results['embedding']['embedding_dim']}")
        console.print(f"    - Throughput: {results['embedding']['texts_per_second']:.1f} texts/s")
    except Exception as e:
        results["embedding"] = {"success": False, "error": str(e)}
        console.print(f"  ✗ Embedding failed: {e}")
    
    # Test validator
    console.print("\n[bold cyan]Testing Validator Module...[/bold cyan]")
    try:
        results["validator"] = await test_validator_module()
        console.print(f"  ✓ Validation test passed in {results['validator']['time_seconds']:.4f}s")
        console.print(f"    - Sample validation: {'passed' if results['validator']['validation_passed'] else 'failed'}")
        console.print(f"    - Quick check: {'passed' if results['validator']['quick_check_passed'] else 'failed'}")
    except Exception as e:
        results["validator"] = {"success": False, "error": str(e)}
        console.print(f"  ✗ Validator failed: {e}")
    
    # Test LLM connection
    console.print("\n[bold cyan]Testing LLM Connection...[/bold cyan]")
    try:
        results["llm"] = await test_llm_connection()
        if results["llm"]["success"]:
            console.print(f"  ✓ LLM API connected: {results['llm'].get('model', 'unknown')}")
            console.print(f"    - Status: {results['llm'].get('status', 'unknown')}")
        else:
            console.print(f"  ✗ LLM connection failed: {results['llm'].get('error', 'unknown')}")
    except Exception as e:
        results["llm"] = {"success": False, "error": str(e)}
        console.print(f"  ✗ LLM test failed: {e}")
    
    return results


def print_summary(all_results: dict) -> None:
    """Print test summary table."""
    table = Table(title="PDF2TeX Module Test Results")
    table.add_column("PDF", style="cyan")
    table.add_column("Extraction", justify="center")
    table.add_column("Chunking", justify="center")
    table.add_column("Embedding", justify="center")
    table.add_column("Validator", justify="center")
    table.add_column("LLM", justify="center")
    
    for pdf_name, results in all_results.items():
        row = [pdf_name]
        for module in ["extraction", "chunking", "embedding", "validator", "llm"]:
            if module in results:
                if results[module].get("success"):
                    row.append("[green]✓[/green]")
                else:
                    row.append("[red]✗[/red]")
            else:
                row.append("[yellow]–[/yellow]")
        table.add_row(*row)
    
    console.print("\n")
    console.print(table)


async def main() -> int:
    """Run all tests."""
    console.print(Panel.fit(
        "[bold blue]PDF2TeX Integration Tests[/bold blue]\n"
        "Testing modules with arXiv papers",
        border_style="blue",
    ))
    
    # Check test data
    console.print("\n[bold]Checking test PDFs...[/bold]")
    available_pdfs = []
    for pdf_info in TEST_PDFS:
        pdf_path = TEST_DATA_DIR / pdf_info["file"]
        if pdf_path.exists():
            info = get_pdf_info(pdf_path)
            console.print(f"  ✓ {pdf_info['name']}: {info.get('pages', '?')} pages, {info.get('size_mb', 0):.2f} MB")
            available_pdfs.append(pdf_info)
        else:
            console.print(f"  ✗ {pdf_info['name']}: not found at {pdf_path}")
    
    if not available_pdfs:
        console.print("[red]No test PDFs available. Run download first.[/red]")
        return 1
    
    # Run tests on each PDF
    all_results = {}
    for pdf_info in available_pdfs:
        pdf_path = TEST_DATA_DIR / pdf_info["file"]
        console.print(f"\n{'='*60}")
        console.print(f"[bold]Testing: {pdf_info['name']}[/bold]")
        console.print(f"arXiv: {pdf_info['arxiv_id']}")
        console.print(f"Expected features: {', '.join(pdf_info['features'])}")
        console.print('='*60)
        
        results = await run_module_tests(pdf_path)
        all_results[pdf_info["name"]] = results
    
    # Print summary
    print_summary(all_results)
    
    # Check overall success
    total_tests = 0
    passed_tests = 0
    for results in all_results.values():
        for module, result in results.items():
            if isinstance(result, dict):
                total_tests += 1
                if result.get("success"):
                    passed_tests += 1
    
    console.print(f"\n[bold]Overall: {passed_tests}/{total_tests} tests passed[/bold]")
    
    if passed_tests == total_tests:
        console.print("[green]All tests passed! ✓[/green]")
        return 0
    else:
        console.print("[yellow]Some tests failed. Check logs above.[/yellow]")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
