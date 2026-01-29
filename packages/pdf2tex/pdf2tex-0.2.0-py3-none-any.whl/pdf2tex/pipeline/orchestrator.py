"""
Main pipeline orchestrator.

Coordinates the complete PDF to LaTeX conversion workflow.
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

import structlog

from pdf2tex.chunking.models import ChunkingResult
from pdf2tex.chunking.service import ChunkingService
from pdf2tex.config import Settings
from pdf2tex.extraction.models import ExtractionResult
from pdf2tex.extraction.service import ExtractionService
from pdf2tex.generation.service import GeneratedDocument, GenerationService
from pdf2tex.pipeline.state import PipelineState, StateManager, StageStatus
from pdf2tex.pipeline.workers import WorkerPool
from pdf2tex.rag.service import RAGService

logger = structlog.get_logger(__name__)


@dataclass
class ConversionResult:
    """Result of PDF to LaTeX conversion."""

    success: bool
    job_id: str
    source_path: Path
    output_files: list[Path] = field(default_factory=list)
    state: PipelineState | None = None
    document: GeneratedDocument | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class PDF2TeXOrchestrator:
    """
    Main orchestrator for PDF to LaTeX conversion.
    
    Coordinates:
    - PDF extraction
    - Text chunking
    - RAG indexing
    - LaTeX generation
    - Output compilation
    """

    def __init__(
        self,
        settings: Settings | None = None,
        output_dir: Path | None = None,
    ) -> None:
        """
        Initialize orchestrator.

        Args:
            settings: Application settings
            output_dir: Output directory for results
        """
        self.settings = settings or Settings()
        self.output_dir = output_dir or Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # State management
        self._state_manager = StateManager(self.output_dir / ".state")

        # Services (lazy initialized)
        self._extraction_service: ExtractionService | None = None
        self._chunking_service: ChunkingService | None = None
        self._rag_service: RAGService | None = None
        self._generation_service: GenerationService | None = None
        self._worker_pool: WorkerPool | None = None

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all services."""
        if self._initialized:
            return

        logger.info("Initializing PDF2TeX orchestrator")

        # Initialize worker pool
        self._worker_pool = WorkerPool(
            num_workers=self.settings.pipeline.num_workers,
            use_ray=self.settings.pipeline.use_ray,
        )
        await self._worker_pool.initialize()

        # Initialize services
        self._extraction_service = ExtractionService(self.settings)
        await self._extraction_service.initialize()

        self._chunking_service = ChunkingService(self.settings)

        self._rag_service = RAGService(self.settings)
        await self._rag_service.initialize()

        self._generation_service = GenerationService(
            self.settings,
            rag_service=self._rag_service,
        )
        await self._generation_service.initialize()

        self._initialized = True
        logger.info("PDF2TeX orchestrator initialized")

    async def convert(
        self,
        pdf_path: Path | str,
        job_id: str | None = None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> ConversionResult:
        """
        Convert PDF to LaTeX.

        Args:
            pdf_path: Path to PDF file
            job_id: Optional job identifier
            progress_callback: Optional progress callback

        Returns:
            Conversion result
        """
        if not self._initialized:
            await self.initialize()

        pdf_path = Path(pdf_path)
        job_id = job_id or str(uuid4())[:8]

        # Create job output directory
        job_output_dir = self.output_dir / job_id
        job_output_dir.mkdir(parents=True, exist_ok=True)

        # Create pipeline state
        state = self._state_manager.create(job_id, pdf_path, job_output_dir)

        try:
            # Stage 1: Extraction
            await self._notify_progress(
                progress_callback, "extraction", 0, "Starting PDF extraction"
            )
            state.start_stage("extraction")
            
            extraction_result = await self._extraction_service.extract(
                pdf_path,
                progress_callback=lambda p: self._notify_progress(
                    progress_callback,
                    "extraction",
                    p.current_page / p.total_pages * 100 if p.total_pages else 0,
                    p.message,
                ),
            )
            
            state.complete_stage("extraction", {
                "pages": len(extraction_result.pages),
                "chars": extraction_result.total_chars,
            })

            # Stage 2: Chunking
            await self._notify_progress(
                progress_callback, "chunking", 0, "Chunking document"
            )
            state.start_stage("chunking")
            
            chunking_result = await self._chunking_service.chunk_document(
                extraction_result
            )
            
            state.complete_stage("chunking", {
                "chapters": len(chunking_result.chapters),
                "chunks": len(chunking_result.all_chunks),
            })

            # Stage 3: Indexing
            await self._notify_progress(
                progress_callback, "indexing", 0, "Indexing for RAG"
            )
            state.start_stage("indexing")
            
            index_stats = await self._rag_service.index_document(
                chunking_result,
                progress_callback=lambda p: self._notify_progress(
                    progress_callback,
                    "indexing",
                    p.get("current", 0) / p.get("total", 1) * 100,
                    "Generating embeddings",
                ),
            )
            
            state.complete_stage("indexing", index_stats)

            # Stage 4: Generation
            await self._notify_progress(
                progress_callback, "generation", 0, "Generating LaTeX"
            )
            state.start_stage("generation")
            
            generated_doc = await self._generation_service.generate_document(
                chunking_result,
                progress_callback=lambda p: self._notify_progress(
                    progress_callback,
                    "generation",
                    p.get("current", 0) / p.get("total", 1) * 100,
                    f"Generating chapter: {p.get('chapter', '')}",
                ),
            )
            
            state.complete_stage("generation", {
                "chapters_generated": len(generated_doc.chapters),
            })

            # Stage 5: Write output files
            await self._notify_progress(
                progress_callback, "compilation", 0, "Writing output files"
            )
            state.start_stage("compilation")
            
            output_files = await self._write_output(
                generated_doc, job_output_dir, pdf_path.stem
            )
            
            state.output_files = output_files
            state.complete_stage("compilation", {
                "files_written": len(output_files),
            })

            self._state_manager.update(state)

            return ConversionResult(
                success=True,
                job_id=job_id,
                source_path=pdf_path,
                output_files=output_files,
                state=state,
                document=generated_doc,
                metadata={
                    "pages": len(extraction_result.pages),
                    "chapters": len(chunking_result.chapters),
                    "chunks": len(chunking_result.all_chunks),
                },
            )

        except Exception as e:
            logger.error("Conversion failed", job_id=job_id, error=str(e))
            state.fail_stage(state.current_stage, str(e))
            self._state_manager.update(state)

            return ConversionResult(
                success=False,
                job_id=job_id,
                source_path=pdf_path,
                state=state,
                error=str(e),
            )

    async def _write_output(
        self,
        document: GeneratedDocument,
        output_dir: Path,
        doc_name: str,
    ) -> list[Path]:
        """Write generated document to files."""
        output_files: list[Path] = []

        # Write main document
        main_file = output_dir / f"{doc_name}.tex"
        main_content = self._build_main_document(document, doc_name)
        main_file.write_text(main_content)
        output_files.append(main_file)

        # Write chapter files
        chapters_dir = output_dir / "chapters"
        chapters_dir.mkdir(exist_ok=True)

        for chapter in document.chapters:
            chapter_file = chapters_dir / f"chapter_{chapter.number}.tex"
            chapter_file.write_text(chapter.latex_content)
            output_files.append(chapter_file)

        logger.info("Output files written", count=len(output_files))
        return output_files

    def _build_main_document(
        self,
        document: GeneratedDocument,
        doc_name: str,
    ) -> str:
        """Build main LaTeX document."""
        lines = [document.preamble]
        
        # Add document begin
        if "\\begin{document}" not in document.preamble:
            lines.append("\n\\begin{document}")

        # Include chapters
        for chapter in document.chapters:
            lines.append(f"\\input{{chapters/chapter_{chapter.number}}}")

        # Add bibliography if present
        if document.bibliography:
            lines.append("\n\\bibliographystyle{plain}")
            lines.append("\\bibliography{references}")

        # Add appendices
        for appendix in document.appendices:
            lines.append(f"\\input{{{appendix}}}")

        # End document
        lines.append("\n\\end{document}")

        return "\n".join(lines)

    async def resume(
        self,
        job_id: str,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> ConversionResult:
        """
        Resume a paused or failed conversion.

        Args:
            job_id: Job identifier
            progress_callback: Optional progress callback

        Returns:
            Conversion result
        """
        state = self._state_manager.get(job_id)
        if not state:
            return ConversionResult(
                success=False,
                job_id=job_id,
                source_path=Path(),
                error=f"Job not found: {job_id}",
            )

        if not state.can_resume():
            return ConversionResult(
                success=state.is_complete,
                job_id=job_id,
                source_path=state.source_path,
                state=state,
                error="Job cannot be resumed" if not state.is_complete else None,
            )

        # Resume from next pending stage
        return await self.convert(
            state.source_path,
            job_id=job_id,
            progress_callback=progress_callback,
        )

    async def _notify_progress(
        self,
        callback: Callable[[dict[str, Any]], None] | None,
        stage: str,
        percent: float,
        message: str,
    ) -> None:
        """Send progress notification."""
        if callback:
            try:
                progress = {
                    "stage": stage,
                    "percent": percent,
                    "message": message,
                }
                if asyncio.iscoroutinefunction(callback):
                    await callback(progress)
                else:
                    callback(progress)
            except Exception as e:
                logger.warning("Progress callback failed", error=str(e))

    def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """Get status of a job."""
        state = self._state_manager.get(job_id)
        if state:
            return state.to_dict()
        return None

    def list_jobs(self) -> list[str]:
        """List all job IDs."""
        return self._state_manager.list_jobs()

    async def get_status(self) -> dict[str, Any]:
        """Get orchestrator status."""
        return {
            "initialized": self._initialized,
            "output_dir": str(self.output_dir),
            "active_jobs": len(self._state_manager.list_jobs()),
            "services": {
                "extraction": self._extraction_service.get_status() if self._extraction_service else None,
                "chunking": self._chunking_service.get_status() if self._chunking_service else None,
                "rag": await self._rag_service.get_status() if self._rag_service else None,
                "generation": self._generation_service.get_status() if self._generation_service else None,
            },
        }

    async def close(self) -> None:
        """Shutdown all services."""
        if self._extraction_service:
            await self._extraction_service.close()
        if self._rag_service:
            await self._rag_service.close()
        if self._generation_service:
            await self._generation_service.close()
        if self._worker_pool:
            await self._worker_pool.shutdown()

        self._initialized = False
        logger.info("PDF2TeX orchestrator shutdown")
