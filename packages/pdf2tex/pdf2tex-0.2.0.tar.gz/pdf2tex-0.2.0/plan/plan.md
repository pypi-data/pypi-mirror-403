# PDF2TeX Module Plan

> **Version:** 1.0.0  
> **Date:** January 23, 2026  
> **Status:** Planning Phase

---

## 1. Executive Summary

PDF2TeX is a high-performance RAG-based module designed to convert large PDF documents (2000+ pages) into structured LaTeX files. The system leverages Hugging Face cloud infrastructure for LLM capabilities, prioritizes mathematical content accuracy, and produces one `.tex` file per chapter with a master document for compilation.

### Key Objectives

| Objective | Target | Priority |
|-----------|--------|----------|
| Processing Speed | < 90 min for 2000 pages | High |
| Math Accuracy | > 95% equation fidelity | Critical |
| Output Quality | Compilable LaTeX | Critical |
| Scalability | 10+ concurrent documents | Medium |

---

## 2. Architecture Overview

### 2.1 Design Principles

Following established software architecture best practices:

- **Modularity & Separation of Concerns**: Independent layers for extraction, chunking, RAG, and generation
- **Scalability**: Ray-based distributed processing with horizontal scaling
- **Security by Design**: Secure API keys, input validation, sandboxed LaTeX compilation
- **Simplicity**: Clear interfaces between components, minimal dependencies per module
- **Flexibility**: Provider-agnostic LLM layer, pluggable OCR/extraction backends

### 2.2 High-Level Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PDF2TeX Pipeline                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────┐ │
│   │   PDF    │───▶│ Extract  │───▶│  Chunk   │───▶│   RAG    │───▶│ LaTeX│ │
│   │  Input   │    │  + OCR   │    │  + Index │    │  + LLM   │    │Output│ │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────┘ │
│        │               │               │               │              │     │
│        │               ▼               ▼               ▼              │     │
│        │         ┌─────────────────────────────────────────────┐     │     │
│        │         │        Ray Distributed Workers              │     │     │
│        │         │   ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐       │     │     │
│        │         │   │ W1 │ │ W2 │ │ W3 │ │ W4 │ │ Wn │       │     │     │
│        │         │   └────┘ └────┘ └────┘ └────┘ └────┘       │     │     │
│        │         └─────────────────────────────────────────────┘     │     │
│        │                           │                                  │     │
│        ▼                           ▼                                  ▼     │
│   ┌──────────────────────────────────────────────────────────────────────┐ │
│   │                    Persistent Storage Layer                          │ │
│   │  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐           │ │
│   │  │ Qdrant  │    │  Redis  │    │ MinIO   │    │Postgres │           │ │
│   │  │ Vectors │    │  Queue  │    │  Files  │    │  State  │           │ │
│   │  └─────────┘    └─────────┘    └─────────┘    └─────────┘           │ │
│   └──────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Specifications

### 3.1 Extraction Layer

**Purpose**: Extract text, images, tables, and mathematical content from PDF pages.

#### Technology Stack

| Component | Tool | Rationale |
|-----------|------|-----------|
| Primary Parser | PyMuPDF (fitz) | Fastest native PDF extraction |
| Math Extraction | **Nougat** (Meta) | Neural PDF-to-LaTeX for equations |
| Complex Layouts | **Marker** | ML-based structure detection |
| OCR Engine | PaddleOCR | Best speed/accuracy for scanned pages |
| OCR Detection | Heuristic | Skip OCR for native text (< 50 chars/page triggers OCR) |

#### Math Content Strategy (Critical Path)

```
┌─────────────────────────────────────────────────────────────┐
│                 Math Extraction Pipeline                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   PDF Page ──▶ Detect Math Regions ──▶ Route to Processor   │
│                       │                                      │
│         ┌─────────────┼─────────────┐                       │
│         ▼             ▼             ▼                       │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│   │  Inline  │  │ Display  │  │  Table   │                 │
│   │   Math   │  │ Equation │  │   Math   │                 │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘                 │
│        │             │             │                        │
│        └─────────────┼─────────────┘                        │
│                      ▼                                       │
│              ┌──────────────┐                                │
│              │    Nougat    │  Neural equation recognition  │
│              │  + TexTeller │  Fallback for complex cases   │
│              └──────────────┘                                │
│                      │                                       │
│                      ▼                                       │
│              ┌──────────────┐                                │
│              │   Validate   │  Compile-check each equation  │
│              │   & Repair   │  Auto-fix common errors       │
│              └──────────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

**Key Features**:
- Nougat processes entire pages for scientific documents
- TexTeller as fallback for individual equation images
- LaTeX compilation validation for each extracted equation
- Auto-repair pipeline for common errors (missing braces, delimiters)

#### Interface

```python
@dataclass
class ExtractedPage:
    page_number: int
    text_blocks: list[TextBlock]
    math_regions: list[MathRegion]      # Detected equations
    tables: list[Table]
    figures: list[Figure]
    metadata: PageMetadata

class ExtractionService(Protocol):
    async def extract_page(self, pdf_path: Path, page: int) -> ExtractedPage: ...
    async def extract_batch(self, pdf_path: Path, pages: range) -> list[ExtractedPage]: ...
```

---

### 3.2 Chunking Layer

**Purpose**: Split extracted content into semantically meaningful chunks while preserving document structure.

#### Chunking Strategy

| Content Type | Strategy | Chunk Size |
|--------------|----------|------------|
| Body Text | Recursive paragraph split | 512 tokens |
| Equations | Preserve whole + context | Variable |
| Tables | Atomic (never split) | Variable |
| Figures | Caption + reference | 256 tokens |
| Code Blocks | Preserve whole | Variable |

#### Hierarchical Structure

```
Document
├── Chapter 1          ──▶  chapter_01.tex
│   ├── Section 1.1
│   │   ├── Chunk 1 (text)
│   │   ├── Chunk 2 (equation block)
│   │   └── Chunk 3 (text + table)
│   └── Section 1.2
│       └── ...
├── Chapter 2          ──▶  chapter_02.tex
│   └── ...
└── Appendix           ──▶  appendix.tex
```

#### Interface

```python
@dataclass
class Chunk:
    id: str
    content: str
    chunk_type: Literal["text", "math", "table", "figure", "code"]
    metadata: ChunkMetadata  # page, section, chapter, position
    embedding: np.ndarray | None

class ChunkingService(Protocol):
    def detect_chapters(self, pages: list[ExtractedPage]) -> list[Chapter]: ...
    def chunk_chapter(self, chapter: Chapter) -> list[Chunk]: ...
```

---

### 3.3 RAG Layer

**Purpose**: Index chunks for retrieval and provide context-aware generation support.

#### Technology Stack

| Component | Tool | Model/Config |
|-----------|------|--------------|
| Embeddings | Sentence-Transformers | `BAAI/bge-m3` (1024 dim) |
| Vector Store | Qdrant | HNSW index, cosine similarity |
| Reranker | Cross-encoder | `BAAI/bge-reranker-v2-m3` |

#### RAG Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      RAG Pipeline                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │   Indexing  │     │  Retrieval  │     │  Reranking  │   │
│  │   Pipeline  │     │   Engine    │     │   Layer     │   │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘   │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Qdrant                            │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │ Collection: {document_id}                    │    │   │
│  │  │ ├── Payload: chapter, section, page, type   │    │   │
│  │  │ └── Vector: 1024-dim BGE-M3 embedding       │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Retrieval Strategy

1. **Semantic Search**: Top-20 similar chunks via vector similarity
2. **Reranking**: Cross-encoder reranks to top-5
3. **Context Enrichment**: Include adjacent chunks for continuity
4. **Filter by Type**: Retrieve LaTeX examples for similar content types

#### Interface

```python
class RAGService(Protocol):
    async def index_document(self, doc_id: str, chunks: list[Chunk]) -> None: ...
    async def retrieve(
        self, 
        query: str, 
        doc_id: str,
        top_k: int = 5,
        filter_type: str | None = None
    ) -> list[RetrievedChunk]: ...
```

---

### 3.4 Generation Layer

**Purpose**: Convert extracted content to LaTeX using LLM with RAG context.

#### Technology Stack

| Component | Provider | Model |
|-----------|----------|-------|
| Primary LLM | **Hugging Face Inference API** | `meta-llama/Llama-3.1-70B-Instruct` |
| Fallback LLM | Hugging Face Inference API | `mistralai/Mixtral-8x22B-Instruct-v0.1` |
| Math Specialist | Hugging Face Inference API | `deepseek-ai/deepseek-math-7b-instruct` |

#### Two-Stage Generation

```
┌─────────────────────────────────────────────────────────────┐
│                  LaTeX Generation Pipeline                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Input Chunk                                                │
│       │                                                      │
│       ▼                                                      │
│   ┌──────────────────────────────────────────────────────┐  │
│   │ Stage 1: Structure Extraction                         │  │
│   │ ┌────────────────────────────────────────────────┐   │  │
│   │ │ • Identify content type (theorem, proof, etc.) │   │  │
│   │ │ • Detect cross-references                      │   │  │
│   │ │ • Map to LaTeX environments                    │   │  │
│   │ └────────────────────────────────────────────────┘   │  │
│   └──────────────────────────────────────────────────────┘  │
│       │                                                      │
│       ▼                                                      │
│   ┌──────────────────────────────────────────────────────┐  │
│   │ Stage 2: LaTeX Synthesis                              │  │
│   │ ┌────────────────────────────────────────────────┐   │  │
│   │ │ • RAG retrieves similar LaTeX examples         │   │  │
│   │ │ • LLM generates LaTeX with few-shot context    │   │  │
│   │ │ • Structured output (JSON) for reliability     │   │  │
│   │ └────────────────────────────────────────────────┘   │  │
│   └──────────────────────────────────────────────────────┘  │
│       │                                                      │
│       ▼                                                      │
│   ┌──────────────────────────────────────────────────────┐  │
│   │ Stage 3: Validation & Repair                          │  │
│   │ ┌────────────────────────────────────────────────┐   │  │
│   │ │ • Bracket matching validation                  │   │  │
│   │ │ • LaTeX compilation check (latexmk dry-run)    │   │  │
│   │ │ • Auto-repair common errors                    │   │  │
│   │ │ • Retry with error feedback if failed          │   │  │
│   │ └────────────────────────────────────────────────┘   │  │
│   └──────────────────────────────────────────────────────┘  │
│       │                                                      │
│       ▼                                                      │
│   Valid LaTeX Output                                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Hugging Face Integration

```python
from huggingface_hub import InferenceClient

class HuggingFaceLLM:
    def __init__(self, model_id: str, token: str):
        self.client = InferenceClient(model=model_id, token=token)
    
    async def generate_latex(
        self,
        content: str,
        structure: ContentStructure,
        examples: list[str],  # RAG-retrieved examples
        system_prompt: str
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self._build_prompt(content, structure, examples)}
        ]
        response = await self.client.chat_completion(
            messages=messages,
            max_tokens=4096,
            temperature=0.1  # Low for deterministic output
        )
        return response.choices[0].message.content
```

#### Interface

```python
class GenerationService(Protocol):
    async def generate_chapter(
        self, 
        chapter: Chapter,
        chunks: list[Chunk],
        rag_context: list[RetrievedChunk]
    ) -> str: ...  # Returns complete chapter LaTeX
```

---

### 3.5 Pipeline Orchestrator

**Purpose**: Coordinate parallel processing and manage document conversion workflow.

#### Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   Pipeline Orchestrator                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   1. Document Intake                                         │
│      ├── Validate PDF                                        │
│      ├── Extract TOC / detect chapters                       │
│      └── Create processing plan                              │
│                                                              │
│   2. Parallel Extraction (Ray)                               │
│      ├── Dispatch pages to workers (batch_size=50)           │
│      ├── Workers run: PyMuPDF → Nougat → PaddleOCR          │
│      └── Aggregate extracted pages                           │
│                                                              │
│   3. Chunking & Indexing                                     │
│      ├── Split into chapters                                 │
│      ├── Chunk each chapter                                  │
│      └── Index chunks in Qdrant                              │
│                                                              │
│   4. Parallel Generation (Ray)                               │
│      ├── Process chapters in parallel                        │
│      ├── Each worker: RAG retrieve → LLM generate → validate │
│      └── Checkpoint after each chapter                       │
│                                                              │
│   5. Assembly                                                │
│      ├── Generate master.tex with \input{} statements        │
│      ├── Copy figures to output directory                    │
│      └── Compile final document                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Checkpointing & Resume

```python
@dataclass
class ProcessingState:
    document_id: str
    status: Literal["extracting", "chunking", "generating", "assembling", "complete", "failed"]
    completed_chapters: list[str]
    failed_chapters: list[str]
    last_checkpoint: datetime
    
class Orchestrator:
    async def resume(self, document_id: str) -> None:
        """Resume processing from last checkpoint"""
        state = await self.state_store.get(document_id)
        pending = set(state.all_chapters) - set(state.completed_chapters)
        await self.process_chapters(pending)
```

---

### 3.6 Output Structure

#### File Organization

```
output/{document_id}/
├── master.tex              # Main document with \input{} calls
├── preamble.tex            # Shared packages and macros
├── chapters/
│   ├── chapter_01.tex      # Chapter 1 content
│   ├── chapter_02.tex      # Chapter 2 content
│   ├── ...
│   └── appendix.tex        # Appendices
├── figures/
│   ├── fig_001.pdf
│   ├── fig_002.png
│   └── ...
├── tables/
│   └── ...
└── build/
    ├── master.pdf          # Compiled output
    └── master.log          # Compilation log
```

#### Master Document Template

```latex
% master.tex
\documentclass[11pt,a4paper]{book}
\input{preamble}

\begin{document}

\frontmatter
\tableofcontents

\mainmatter
\input{chapters/chapter_01}
\input{chapters/chapter_02}
% ... auto-generated \input{} statements

\appendix
\input{chapters/appendix}

\backmatter
\bibliography{references}

\end{document}
```

---

## 4. Project Structure

```
pdf2tex/
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile
├── README.md
│
├── src/
│   └── pdf2tex/
│       ├── __init__.py
│       ├── config.py                 # Pydantic settings
│       │
│       ├── extraction/
│       │   ├── __init__.py
│       │   ├── service.py            # ExtractionService implementation
│       │   ├── pdf_parser.py         # PyMuPDF wrapper
│       │   ├── math_extractor.py     # Nougat + TexTeller integration
│       │   ├── ocr.py                # PaddleOCR wrapper
│       │   └── models.py             # ExtractedPage, MathRegion, etc.
│       │
│       ├── chunking/
│       │   ├── __init__.py
│       │   ├── service.py            # ChunkingService implementation
│       │   ├── splitter.py           # Hierarchical text splitter
│       │   ├── chapter_detector.py   # TOC/heading analysis
│       │   └── models.py             # Chunk, Chapter, etc.
│       │
│       ├── rag/
│       │   ├── __init__.py
│       │   ├── service.py            # RAGService implementation
│       │   ├── embeddings.py         # BGE-M3 embedding client
│       │   ├── vectorstore.py        # Qdrant client wrapper
│       │   ├── reranker.py           # Cross-encoder reranker
│       │   └── models.py             # RetrievedChunk, etc.
│       │
│       ├── generation/
│       │   ├── __init__.py
│       │   ├── service.py            # GenerationService implementation
│       │   ├── llm.py                # HuggingFace LLM client
│       │   ├── prompts.py            # System prompts and templates
│       │   ├── templates/            # LaTeX templates
│       │   │   ├── master.tex.jinja
│       │   │   ├── preamble.tex.jinja
│       │   │   └── chapter.tex.jinja
│       │   ├── validator.py          # LaTeX compilation checker
│       │   └── models.py             # ContentStructure, etc.
│       │
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── orchestrator.py       # Main pipeline coordinator
│       │   ├── workers.py            # Ray worker definitions
│       │   ├── state.py              # Processing state management
│       │   └── assembler.py          # Final document assembly
│       │
│       └── api/
│           ├── __init__.py
│           ├── app.py                # FastAPI application
│           ├── routes.py             # API endpoints
│           ├── schemas.py            # Request/response models
│           └── deps.py               # Dependency injection
│
├── tests/
│   ├── conftest.py
│   ├── fixtures/                     # Sample PDFs
│   ├── test_extraction/
│   ├── test_chunking/
│   ├── test_rag/
│   ├── test_generation/
│   └── test_pipeline/
│
└── scripts/
    ├── cli.py                        # Command-line interface
    ├── benchmark.py                  # Performance testing
    └── setup_infra.sh                # Docker setup script
```

---

## 5. Dependencies

```toml
[project]
name = "pdf2tex"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    # PDF Processing
    "pymupdf>=1.24.0",
    "pdfplumber>=0.11.0",
    "pdf2image>=1.17.0",
    
    # Math Extraction (Critical)
    "nougat-ocr>=0.1.0",
    "transformers>=4.40.0",
    
    # OCR
    "paddleocr>=2.7.0",
    "paddlepaddle>=2.6.0",
    
    # Embeddings & RAG
    "sentence-transformers>=2.7.0",
    "qdrant-client>=1.9.0",
    "torch>=2.2.0",
    
    # LLM (Hugging Face)
    "huggingface-hub>=0.23.0",
    
    # Parallel Processing
    "ray[default]>=2.20.0",
    
    # API & Infrastructure
    "fastapi>=0.111.0",
    "uvicorn>=0.29.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.2.0",
    "redis>=5.0.0",
    "sqlalchemy>=2.0.0",
    "asyncpg>=0.29.0",
    
    # LaTeX Processing
    "jinja2>=3.1.0",
    
    # Utilities
    "structlog>=24.1.0",
    "typer>=0.12.0",
    "rich>=13.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
]
```

---

## 6. API Specification

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/documents` | Submit PDF for conversion |
| `GET` | `/documents/{id}` | Get document status |
| `GET` | `/documents/{id}/progress` | Get detailed progress |
| `GET` | `/documents/{id}/output` | Download output files |
| `POST` | `/documents/{id}/resume` | Resume failed conversion |
| `DELETE` | `/documents/{id}` | Cancel and cleanup |

### Example Request

```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@textbook.pdf" \
  -F "config={\"output_format\": \"chapter_per_file\", \"math_priority\": \"high\"}"
```

### Example Response

```json
{
  "document_id": "doc_abc123",
  "status": "processing",
  "progress": {
    "stage": "extraction",
    "pages_processed": 150,
    "total_pages": 2000,
    "chapters_completed": 0,
    "total_chapters": 25,
    "estimated_time_remaining": "45 minutes"
  }
}
```

---

## 7. Performance Targets

### Processing Time Breakdown (2000 pages, 20 workers)

| Stage | Sequential | Parallel (20 workers) |
|-------|------------|----------------------|
| PDF Extraction | 30 min | 2 min |
| Math Extraction (Nougat) | 4 hours | 15 min |
| OCR (if needed) | 6 hours | 20 min |
| Embedding | 40 min | 3 min |
| LLM Generation | 8 hours | 30 min |
| Validation | 20 min | 2 min |
| **Total** | **~19 hours** | **~72 min** |

### Resource Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 8 cores | 32 cores |
| RAM | 32 GB | 64 GB |
| GPU | 1x RTX 3080 | 2x RTX 4090 |
| Storage | 100 GB SSD | 500 GB NVMe |

---

## 8. Quality Assurance

### Validation Pipeline

1. **Syntax Check**: Regex-based bracket/delimiter matching
2. **Compilation Check**: `latexmk -pdf -halt-on-error -interaction=nonstopmode`
3. **Math Validation**: Compile equations in isolation
4. **Visual Diff**: Optional PDF comparison with original

### Error Handling Strategy

```python
class ValidationError(Exception):
    def __init__(self, latex: str, errors: list[str], suggestions: list[str]):
        self.latex = latex
        self.errors = errors
        self.suggestions = suggestions

async def generate_with_retry(chunk: Chunk, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        latex = await llm.generate(chunk)
        try:
            await validator.validate(latex)
            return latex
        except ValidationError as e:
            # Feed error back to LLM for self-correction
            chunk = chunk.with_error_context(e.errors, e.suggestions)
    raise ConversionError(f"Failed after {max_retries} attempts")
```

---

## 9. Security Considerations

| Concern | Mitigation |
|---------|------------|
| API Key Exposure | Environment variables, secrets manager |
| Malicious PDFs | Sandboxed extraction, input validation |
| LaTeX Injection | Restricted commands, sandboxed compilation |
| Data Privacy | Optional local LLM mode, data encryption |

---

## 10. Future Enhancements

- [ ] Web UI for document upload and monitoring
- [ ] Support for additional input formats (DOCX, EPUB)
- [ ] Custom LaTeX template configuration
- [ ] Fine-tuned math extraction model on domain-specific content
- [ ] Real-time streaming output preview
- [ ] Multi-language document support

---

## 11. Architecture Decision Records (ADRs)

### ADR-001: Hugging Face as LLM Provider

**Context**: Need reliable, scalable LLM access for LaTeX generation.

**Decision**: Use Hugging Face Inference API with Llama 3.1 70B as primary model.

**Rationale**:
- Cost-effective compared to OpenAI/Anthropic for high-volume processing
- Access to specialized models (deepseek-math for equations)
- Option to deploy dedicated endpoints for production
- No vendor lock-in, can switch to self-hosted models

**Consequences**: 
- May have higher latency than dedicated API providers
- Rate limits require careful batching strategy

---

### ADR-002: Nougat for Math Extraction

**Context**: Mathematical content accuracy is critical.

**Decision**: Use Meta's Nougat model as primary math extraction tool.

**Rationale**:
- Purpose-built for scientific PDF to LaTeX conversion
- Handles complex equations, matrices, and multi-line formulas
- Trained on arXiv papers with high equation fidelity
- Open-source, can be fine-tuned if needed

**Consequences**:
- Requires GPU for efficient processing
- Adds model loading overhead

---

### ADR-003: One .tex File Per Chapter

**Context**: Need to define output structure for large documents.

**Decision**: Generate separate `.tex` files per chapter with a master document.

**Rationale**:
- Enables parallel chapter processing and writing
- Easier debugging and manual editing
- Supports incremental compilation
- Better version control granularity
- Matches standard LaTeX book structure

**Consequences**:
- Requires careful cross-reference management
- Assembly step needed to create master document
