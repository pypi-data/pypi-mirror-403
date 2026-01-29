"""
FastAPI application for PDF2TeX.

Provides REST endpoints for conversion operations.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

import structlog
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from pdf2tex.config import Settings
from pdf2tex.pipeline.orchestrator import PDF2TeXOrchestrator

logger = structlog.get_logger(__name__)

# Global orchestrator instance
_orchestrator: PDF2TeXOrchestrator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan management."""
    global _orchestrator
    
    settings = Settings()
    _orchestrator = PDF2TeXOrchestrator(settings)
    await _orchestrator.initialize()
    
    logger.info("API started")
    yield
    
    if _orchestrator:
        await _orchestrator.close()
    logger.info("API shutdown")


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Create FastAPI application.

    Args:
        settings: Optional application settings

    Returns:
        FastAPI application instance
    """
    app = FastAPI(
        title="PDF2TeX API",
        description="Convert PDF documents to LaTeX using RAG",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(conversion_router)
    app.include_router(jobs_router)
    app.include_router(health_router)

    return app


# Pydantic models
class ConversionRequest(BaseModel):
    """Request to start a conversion."""

    pdf_url: str | None = None
    options: dict[str, Any] = {}


class ConversionResponse(BaseModel):
    """Response from conversion request."""

    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    """Status of a conversion job."""

    job_id: str
    status: str
    progress: float
    current_stage: str
    error: str | None = None
    output_files: list[str] = []


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    services: dict[str, Any]


# Routers
from fastapi import APIRouter

conversion_router = APIRouter(prefix="/convert", tags=["conversion"])
jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])
health_router = APIRouter(prefix="/health", tags=["health"])


@conversion_router.post("/", response_model=ConversionResponse)
async def start_conversion(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> ConversionResponse:
    """
    Start PDF to LaTeX conversion.

    Upload a PDF file to begin conversion.
    """
    if not _orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")

    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    # Save uploaded file
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / file.filename
    content = await file.read()
    file_path.write_bytes(content)

    # Generate job ID
    from uuid import uuid4
    job_id = str(uuid4())[:8]

    # Start conversion in background
    background_tasks.add_task(
        run_conversion,
        job_id,
        file_path,
    )

    return ConversionResponse(
        job_id=job_id,
        status="started",
        message=f"Conversion started for {file.filename}",
    )


async def run_conversion(job_id: str, pdf_path: Path) -> None:
    """Run conversion in background."""
    if _orchestrator:
        await _orchestrator.convert(pdf_path, job_id=job_id)


@conversion_router.post("/url", response_model=ConversionResponse)
async def convert_from_url(
    request: ConversionRequest,
    background_tasks: BackgroundTasks,
) -> ConversionResponse:
    """
    Start conversion from URL.

    Provide a URL to a PDF file for conversion.
    """
    if not _orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")

    if not request.pdf_url:
        raise HTTPException(status_code=400, detail="PDF URL required")

    # Download file
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(request.pdf_url)
            response.raise_for_status()
            
            # Save to uploads
            upload_dir = Path("uploads")
            upload_dir.mkdir(exist_ok=True)
            
            filename = Path(request.pdf_url).name or "document.pdf"
            file_path = upload_dir / filename
            file_path.write_bytes(response.content)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download PDF: {e}")

    # Generate job ID
    from uuid import uuid4
    job_id = str(uuid4())[:8]

    # Start conversion
    background_tasks.add_task(run_conversion, job_id, file_path)

    return ConversionResponse(
        job_id=job_id,
        status="started",
        message=f"Conversion started from URL",
    )


@jobs_router.get("/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str) -> JobStatus:
    """Get status of a conversion job."""
    if not _orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")

    status = _orchestrator.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatus(
        job_id=job_id,
        status=status["status"],
        progress=status["progress_percent"],
        current_stage=status["current_stage"],
        error=status.get("error"),
        output_files=[str(p) for p in status.get("output_files", [])],
    )


@jobs_router.get("/")
async def list_jobs() -> list[str]:
    """List all job IDs."""
    if not _orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")

    return _orchestrator.list_jobs()


@jobs_router.get("/{job_id}/output/{filename}")
async def get_output_file(job_id: str, filename: str) -> FileResponse:
    """Download an output file."""
    if not _orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")

    status = _orchestrator.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")

    output_files = status.get("output_files", [])
    
    for file_path in output_files:
        path = Path(file_path)
        if path.name == filename:
            if path.exists():
                return FileResponse(
                    path=path,
                    filename=filename,
                    media_type="application/x-tex",
                )
    
    raise HTTPException(status_code=404, detail="File not found")


@jobs_router.get("/{job_id}/download")
async def download_all(job_id: str) -> FileResponse:
    """Download all output files as ZIP."""
    if not _orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")

    status = _orchestrator.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")

    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not complete")

    # Create ZIP
    import zipfile
    import tempfile
    
    output_files = status.get("output_files", [])
    if not output_files:
        raise HTTPException(status_code=404, detail="No output files")

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        with zipfile.ZipFile(tmp.name, "w") as zf:
            for file_path in output_files:
                path = Path(file_path)
                if path.exists():
                    zf.write(path, path.name)
        
        return FileResponse(
            path=tmp.name,
            filename=f"{job_id}_output.zip",
            media_type="application/zip",
        )


@jobs_router.post("/{job_id}/resume", response_model=ConversionResponse)
async def resume_job(
    job_id: str,
    background_tasks: BackgroundTasks,
) -> ConversionResponse:
    """Resume a paused or failed job."""
    if not _orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")

    status = _orchestrator.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")

    background_tasks.add_task(
        lambda: asyncio.run(_orchestrator.resume(job_id))
    )

    return ConversionResponse(
        job_id=job_id,
        status="resuming",
        message="Job resuming",
    )


@health_router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    services = {}
    
    if _orchestrator:
        try:
            status = await _orchestrator.get_status()
            services = status.get("services", {})
        except Exception:
            pass

    return HealthResponse(
        status="healthy" if _orchestrator and _orchestrator._initialized else "degraded",
        version="0.1.0",
        services=services,
    )


@health_router.get("/ready")
async def readiness_check() -> JSONResponse:
    """Readiness probe for Kubernetes."""
    if _orchestrator and _orchestrator._initialized:
        return JSONResponse({"ready": True})
    return JSONResponse({"ready": False}, status_code=503)


@health_router.get("/live")
async def liveness_check() -> JSONResponse:
    """Liveness probe for Kubernetes."""
    return JSONResponse({"alive": True})


# Main entry point
def main() -> None:
    """Run the API server."""
    import uvicorn
    
    settings = Settings()
    
    uvicorn.run(
        "pdf2tex.api.app:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
