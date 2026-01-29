"""
Command-line interface for PDF2TeX.

Provides CLI commands for PDF to LaTeX conversion.
"""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from pdf2tex.config import Settings
from pdf2tex.pipeline.orchestrator import PDF2TeXOrchestrator

app = typer.Typer(
    name="pdf2tex",
    help="Convert PDF documents to LaTeX using RAG",
    add_completion=False,
)

console = Console()


@app.command()
def convert(
    pdf_path: Path = typer.Argument(..., help="Path to PDF file"),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
    job_id: Optional[str] = typer.Option(
        None, "--job-id", "-j", help="Job identifier"
    ),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug mode"),
) -> None:
    """
    Convert a PDF file to LaTeX.

    Example:
        pdf2tex convert document.pdf -o ./output
    """
    if not pdf_path.exists():
        console.print(f"[red]Error: File not found: {pdf_path}[/red]")
        raise typer.Exit(1)

    if not pdf_path.suffix.lower() == ".pdf":
        console.print("[red]Error: File must be a PDF[/red]")
        raise typer.Exit(1)

    # Configure settings
    settings = Settings()
    if debug:
        settings.debug = True

    output_dir = output_dir or Path("output")

    async def run_conversion() -> None:
        orchestrator = PDF2TeXOrchestrator(settings, output_dir)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("Converting...", total=100)

            def update_progress(p: dict) -> None:
                stage = p.get("stage", "")
                percent = p.get("percent", 0)
                message = p.get("message", "")
                progress.update(
                    task,
                    completed=percent,
                    description=f"[{stage}] {message}",
                )

            try:
                result = await orchestrator.convert(
                    pdf_path,
                    job_id=job_id,
                    progress_callback=update_progress,
                )

                if result.success:
                    progress.update(task, completed=100)
                    console.print("\n[green]✓ Conversion complete![/green]")
                    console.print(f"  Job ID: {result.job_id}")
                    console.print("  Output files:")
                    for f in result.output_files:
                        console.print(f"    - {f}")
                else:
                    console.print(f"\n[red]✗ Conversion failed: {result.error}[/red]")
                    raise typer.Exit(1)

            finally:
                await orchestrator.close()

    asyncio.run(run_conversion())


@app.command()
def status(
    job_id: str = typer.Argument(..., help="Job ID to check"),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
) -> None:
    """
    Check status of a conversion job.

    Example:
        pdf2tex status abc123
    """
    output_dir = output_dir or Path("output")
    settings = Settings()

    async def check_status() -> None:
        orchestrator = PDF2TeXOrchestrator(settings, output_dir)
        
        status = orchestrator.get_job_status(job_id)
        if not status:
            console.print(f"[red]Job not found: {job_id}[/red]")
            raise typer.Exit(1)

        # Display status table
        table = Table(title=f"Job Status: {job_id}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Status", status["status"])
        table.add_row("Progress", f"{status['progress_percent']:.1f}%")
        table.add_row("Current Stage", status["current_stage"])
        
        if status.get("error"):
            table.add_row("Error", f"[red]{status['error']}[/red]")

        console.print(table)

        # Stage details
        if status.get("stages"):
            stage_table = Table(title="Stage Details")
            stage_table.add_column("Stage")
            stage_table.add_column("Status")
            stage_table.add_column("Duration")

            for name, stage in status["stages"].items():
                status_style = {
                    "completed": "green",
                    "in_progress": "yellow",
                    "failed": "red",
                    "pending": "dim",
                }.get(stage["status"], "white")

                duration = ""
                if stage.get("started_at") and stage.get("completed_at"):
                    from datetime import datetime
                    start = datetime.fromisoformat(stage["started_at"])
                    end = datetime.fromisoformat(stage["completed_at"])
                    duration = f"{(end - start).total_seconds():.1f}s"

                stage_table.add_row(
                    name,
                    f"[{status_style}]{stage['status']}[/{status_style}]",
                    duration,
                )

            console.print(stage_table)

        await orchestrator.close()

    asyncio.run(check_status())


@app.command()
def resume(
    job_id: str = typer.Argument(..., help="Job ID to resume"),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
) -> None:
    """
    Resume a paused or failed job.

    Example:
        pdf2tex resume abc123
    """
    output_dir = output_dir or Path("output")
    settings = Settings()

    async def run_resume() -> None:
        orchestrator = PDF2TeXOrchestrator(settings, output_dir)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Resuming...", total=None)

            def update_progress(p: dict) -> None:
                message = p.get("message", "")
                progress.update(task, description=message)

            result = await orchestrator.resume(
                job_id,
                progress_callback=update_progress,
            )

            if result.success:
                console.print("[green]✓ Job resumed and completed![/green]")
            else:
                console.print(f"[red]✗ Resume failed: {result.error}[/red]")
                raise typer.Exit(1)

        await orchestrator.close()

    asyncio.run(run_resume())


@app.command()
def list_jobs(
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
) -> None:
    """
    List all conversion jobs.

    Example:
        pdf2tex list-jobs
    """
    output_dir = output_dir or Path("output")
    settings = Settings()

    async def show_jobs() -> None:
        orchestrator = PDF2TeXOrchestrator(settings, output_dir)
        
        jobs = orchestrator.list_jobs()
        
        if not jobs:
            console.print("[dim]No jobs found[/dim]")
            return

        table = Table(title="Conversion Jobs")
        table.add_column("Job ID")
        table.add_column("Status")
        table.add_column("Progress")
        table.add_column("Source")

        for job_id in jobs:
            status = orchestrator.get_job_status(job_id)
            if status:
                status_style = {
                    "completed": "green",
                    "in_progress": "yellow",
                    "failed": "red",
                    "pending": "dim",
                }.get(status["status"], "white")

                table.add_row(
                    job_id,
                    f"[{status_style}]{status['status']}[/{status_style}]",
                    f"{status['progress_percent']:.0f}%",
                    Path(status["source_path"]).name,
                )

        console.print(table)
        await orchestrator.close()

    asyncio.run(show_jobs())


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
) -> None:
    """
    Start the API server.

    Example:
        pdf2tex serve --port 8000
    """
    import uvicorn

    console.print(f"[green]Starting PDF2TeX API server on {host}:{port}[/green]")
    
    uvicorn.run(
        "pdf2tex.api.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def info() -> None:
    """
    Show PDF2TeX information and configuration.
    """
    from pdf2tex import __version__

    settings = Settings()

    console.print(f"[bold]PDF2TeX[/bold] v{__version__}")
    console.print()

    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    table.add_row("Debug Mode", str(settings.debug))
    table.add_row("Device", settings.extraction.device)
    table.add_row("Nougat Model", settings.extraction.nougat_model)
    table.add_row("Embedding Model", settings.rag.embedding_model)
    table.add_row("LLM Model", settings.generation.model_name)
    table.add_row("Chunk Size", str(settings.chunking.chunk_size))
    table.add_row("Workers", str(settings.pipeline.num_workers))

    console.print(table)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
