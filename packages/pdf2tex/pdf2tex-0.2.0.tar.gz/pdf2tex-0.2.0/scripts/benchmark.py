#!/usr/bin/env python3
"""
Script to benchmark PDF2TeX performance.
"""

import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def benchmark_extraction(pdf_path: Path, iterations: int = 3) -> dict:
    """Benchmark PDF extraction."""
    from pdf2tex.extraction.service import ExtractionService
    from pdf2tex.config import Settings
    
    settings = Settings()
    service = ExtractionService(settings.extraction)
    
    times = []
    for i in range(iterations):
        start = time.perf_counter()
        result = service.extract(pdf_path)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Extraction run {i + 1}: {elapsed:.2f}s ({result.total_pages} pages)")
    
    return {
        "mean": sum(times) / len(times),
        "min": min(times),
        "max": max(times),
        "pages": result.total_pages,
        "pages_per_sec": result.total_pages / (sum(times) / len(times)),
    }


def benchmark_chunking(pages: list, iterations: int = 3) -> dict:
    """Benchmark text chunking."""
    from pdf2tex.chunking.service import ChunkingService
    from pdf2tex.config import Settings
    
    settings = Settings()
    service = ChunkingService(settings.chunking)
    
    times = []
    for i in range(iterations):
        start = time.perf_counter()
        result = service.chunk_pages(pages, document_id="benchmark")
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Chunking run {i + 1}: {elapsed:.2f}s ({len(result.chunks)} chunks)")
    
    return {
        "mean": sum(times) / len(times),
        "min": min(times),
        "max": max(times),
        "chunks": len(result.chunks),
    }


def benchmark_embedding(chunks: list, iterations: int = 3) -> dict:
    """Benchmark embedding generation."""
    from pdf2tex.rag.embeddings import EmbeddingClient
    from pdf2tex.config import Settings
    
    settings = Settings()
    client = EmbeddingClient(
        model_name=settings.rag.embedding_model,
        device=str(settings.extraction.device),
    )
    
    texts = [c.content for c in chunks[:100]]  # Limit for benchmark
    
    times = []
    for i in range(iterations):
        start = time.perf_counter()
        embeddings = client.embed_texts(texts)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Embedding run {i + 1}: {elapsed:.2f}s ({len(texts)} texts)")
    
    return {
        "mean": sum(times) / len(times),
        "min": min(times),
        "max": max(times),
        "texts": len(texts),
        "texts_per_sec": len(texts) / (sum(times) / len(times)),
    }


def format_results(results: dict) -> str:
    """Format benchmark results."""
    lines = []
    lines.append("\n" + "=" * 60)
    lines.append("BENCHMARK RESULTS")
    lines.append("=" * 60)
    
    for stage, data in results.items():
        lines.append(f"\n{stage.upper()}")
        lines.append("-" * 40)
        for key, value in data.items():
            if isinstance(value, float):
                lines.append(f"  {key}: {value:.3f}")
            else:
                lines.append(f"  {key}: {value}")
    
    return "\n".join(lines)


def main() -> int:
    """Run benchmarks."""
    parser = argparse.ArgumentParser(description="Benchmark PDF2TeX performance")
    parser.add_argument("pdf_path", type=Path, help="Path to PDF file")
    parser.add_argument("--iterations", "-n", type=int, default=3, help="Number of iterations")
    parser.add_argument("--stages", nargs="+", default=["extraction", "chunking", "embedding"],
                        help="Stages to benchmark")
    args = parser.parse_args()
    
    if not args.pdf_path.exists():
        print(f"Error: PDF file not found: {args.pdf_path}")
        return 1
    
    print("=" * 60)
    print("PDF2TeX Performance Benchmark")
    print("=" * 60)
    print(f"PDF: {args.pdf_path}")
    print(f"Iterations: {args.iterations}")
    print(f"Stages: {', '.join(args.stages)}")
    
    results = {}
    pages = None
    chunks = None
    
    if "extraction" in args.stages:
        print("\nRunning extraction benchmark...")
        results["extraction"] = benchmark_extraction(args.pdf_path, args.iterations)
        
        # Get pages for next stages
        from pdf2tex.extraction.service import ExtractionService
        from pdf2tex.config import Settings
        settings = Settings()
        service = ExtractionService(settings.extraction)
        extraction_result = service.extract(args.pdf_path)
        pages = extraction_result.pages
    
    if "chunking" in args.stages and pages:
        print("\nRunning chunking benchmark...")
        results["chunking"] = benchmark_chunking(pages, args.iterations)
        
        # Get chunks for next stages
        from pdf2tex.chunking.service import ChunkingService
        from pdf2tex.config import Settings
        settings = Settings()
        service = ChunkingService(settings.chunking)
        chunking_result = service.chunk_pages(pages, document_id="benchmark")
        chunks = chunking_result.chunks
    
    if "embedding" in args.stages and chunks:
        print("\nRunning embedding benchmark...")
        results["embedding"] = benchmark_embedding(chunks, args.iterations)
    
    print(format_results(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
