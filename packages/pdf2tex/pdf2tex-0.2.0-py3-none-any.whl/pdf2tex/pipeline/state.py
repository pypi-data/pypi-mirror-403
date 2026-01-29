"""
Pipeline state management.

Tracks progress and status of conversion jobs.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class StageStatus(str, Enum):
    """Status of a pipeline stage."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """Result of a pipeline stage."""

    stage_name: str
    status: StageStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineState:
    """
    State of a conversion pipeline.
    
    Tracks progress through all stages and enables resume.
    """

    job_id: str
    source_path: Path
    output_dir: Path
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Stage results
    extraction: StageResult | None = None
    chunking: StageResult | None = None
    indexing: StageResult | None = None
    generation: StageResult | None = None
    compilation: StageResult | None = None
    
    # Intermediate data paths
    extraction_path: Path | None = None
    chunking_path: Path | None = None
    
    # Overall status
    status: StageStatus = StageStatus.PENDING
    error: str | None = None
    
    # Progress tracking
    current_stage: str = "pending"
    progress_percent: float = 0.0
    
    # Results
    output_files: list[Path] = field(default_factory=list)
    
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize stage results."""
        if self.extraction is None:
            self.extraction = StageResult(stage_name="extraction", status=StageStatus.PENDING)
        if self.chunking is None:
            self.chunking = StageResult(stage_name="chunking", status=StageStatus.PENDING)
        if self.indexing is None:
            self.indexing = StageResult(stage_name="indexing", status=StageStatus.PENDING)
        if self.generation is None:
            self.generation = StageResult(stage_name="generation", status=StageStatus.PENDING)
        if self.compilation is None:
            self.compilation = StageResult(stage_name="compilation", status=StageStatus.PENDING)

    @property
    def stages(self) -> list[StageResult]:
        """Get all stages in order."""
        return [
            self.extraction,
            self.chunking,
            self.indexing,
            self.generation,
            self.compilation,
        ]

    @property
    def is_complete(self) -> bool:
        """Check if all stages are complete."""
        return all(
            s.status in (StageStatus.COMPLETED, StageStatus.SKIPPED)
            for s in self.stages
        )

    @property
    def is_failed(self) -> bool:
        """Check if any stage failed."""
        return any(s.status == StageStatus.FAILED for s in self.stages)

    @property
    def elapsed_time(self) -> float:
        """Get total elapsed time in seconds."""
        if not self.stages[0].started_at:
            return 0.0
        
        end_time = datetime.now()
        for stage in reversed(self.stages):
            if stage.completed_at:
                end_time = stage.completed_at
                break
        
        return (end_time - self.stages[0].started_at).total_seconds()

    def start_stage(self, stage_name: str) -> None:
        """Mark a stage as started."""
        stage = self._get_stage(stage_name)
        if stage:
            stage.status = StageStatus.IN_PROGRESS
            stage.started_at = datetime.now()
            self.current_stage = stage_name
            self.status = StageStatus.IN_PROGRESS
            self.updated_at = datetime.now()
            logger.info("Stage started", stage=stage_name, job_id=self.job_id)

    def complete_stage(
        self,
        stage_name: str,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        """Mark a stage as completed."""
        stage = self._get_stage(stage_name)
        if stage:
            stage.status = StageStatus.COMPLETED
            stage.completed_at = datetime.now()
            if metrics:
                stage.metrics = metrics
            self._update_progress()
            self.updated_at = datetime.now()
            logger.info(
                "Stage completed",
                stage=stage_name,
                job_id=self.job_id,
                duration=(
                    (stage.completed_at - stage.started_at).total_seconds()
                    if stage.started_at
                    else 0
                ),
            )

    def fail_stage(self, stage_name: str, error: str) -> None:
        """Mark a stage as failed."""
        stage = self._get_stage(stage_name)
        if stage:
            stage.status = StageStatus.FAILED
            stage.completed_at = datetime.now()
            stage.error = error
            self.status = StageStatus.FAILED
            self.error = f"Stage {stage_name} failed: {error}"
            self.updated_at = datetime.now()
            logger.error(
                "Stage failed",
                stage=stage_name,
                job_id=self.job_id,
                error=error,
            )

    def skip_stage(self, stage_name: str, reason: str = "") -> None:
        """Mark a stage as skipped."""
        stage = self._get_stage(stage_name)
        if stage:
            stage.status = StageStatus.SKIPPED
            stage.metrics["skip_reason"] = reason
            self._update_progress()
            self.updated_at = datetime.now()

    def _get_stage(self, stage_name: str) -> StageResult | None:
        """Get stage by name."""
        return getattr(self, stage_name, None)

    def _update_progress(self) -> None:
        """Update overall progress percentage."""
        completed = sum(
            1 for s in self.stages
            if s.status in (StageStatus.COMPLETED, StageStatus.SKIPPED)
        )
        self.progress_percent = (completed / len(self.stages)) * 100

        if self.is_complete:
            self.status = StageStatus.COMPLETED
            self.current_stage = "complete"

    def get_next_stage(self) -> str | None:
        """Get next stage to run."""
        stage_order = ["extraction", "chunking", "indexing", "generation", "compilation"]
        for stage_name in stage_order:
            stage = self._get_stage(stage_name)
            if stage and stage.status == StageStatus.PENDING:
                return stage_name
        return None

    def can_resume(self) -> bool:
        """Check if pipeline can be resumed."""
        return not self.is_complete and not self.is_failed

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "source_path": str(self.source_path),
            "output_dir": str(self.output_dir),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.value,
            "current_stage": self.current_stage,
            "progress_percent": self.progress_percent,
            "error": self.error,
            "stages": {
                s.stage_name: {
                    "status": s.status.value,
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                    "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                    "error": s.error,
                    "metrics": s.metrics,
                }
                for s in self.stages
            },
            "output_files": [str(p) for p in self.output_files],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineState":
        """Create from dictionary."""
        state = cls(
            job_id=data["job_id"],
            source_path=Path(data["source_path"]),
            output_dir=Path(data["output_dir"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            status=StageStatus(data["status"]),
            current_stage=data["current_stage"],
            progress_percent=data["progress_percent"],
            error=data.get("error"),
            output_files=[Path(p) for p in data.get("output_files", [])],
            metadata=data.get("metadata", {}),
        )

        # Restore stage results
        for stage_name, stage_data in data.get("stages", {}).items():
            stage = state._get_stage(stage_name)
            if stage:
                stage.status = StageStatus(stage_data["status"])
                if stage_data.get("started_at"):
                    stage.started_at = datetime.fromisoformat(stage_data["started_at"])
                if stage_data.get("completed_at"):
                    stage.completed_at = datetime.fromisoformat(stage_data["completed_at"])
                stage.error = stage_data.get("error")
                stage.metrics = stage_data.get("metrics", {})

        return state

    def save(self, path: Path | None = None) -> Path:
        """Save state to file."""
        if path is None:
            path = self.output_dir / f"{self.job_id}_state.json"
        
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))
        
        return path

    @classmethod
    def load(cls, path: Path) -> "PipelineState":
        """Load state from file."""
        data = json.loads(path.read_text())
        return cls.from_dict(data)


class StateManager:
    """
    Manages pipeline states across jobs.
    """

    def __init__(self, state_dir: Path) -> None:
        """
        Initialize state manager.

        Args:
            state_dir: Directory for state files
        """
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._states: dict[str, PipelineState] = {}

    def create(
        self,
        job_id: str,
        source_path: Path,
        output_dir: Path,
    ) -> PipelineState:
        """Create new pipeline state."""
        state = PipelineState(
            job_id=job_id,
            source_path=source_path,
            output_dir=output_dir,
        )
        self._states[job_id] = state
        state.save()
        return state

    def get(self, job_id: str) -> PipelineState | None:
        """Get state by job ID."""
        if job_id in self._states:
            return self._states[job_id]
        
        # Try to load from file
        state_file = self.state_dir / f"{job_id}_state.json"
        if state_file.exists():
            state = PipelineState.load(state_file)
            self._states[job_id] = state
            return state
        
        return None

    def update(self, state: PipelineState) -> None:
        """Update and persist state."""
        self._states[state.job_id] = state
        state.save()

    def list_jobs(self) -> list[str]:
        """List all job IDs."""
        job_ids = set(self._states.keys())
        
        for state_file in self.state_dir.glob("*_state.json"):
            job_id = state_file.stem.replace("_state", "")
            job_ids.add(job_id)
        
        return list(job_ids)

    def cleanup_completed(self, max_age_days: int = 7) -> int:
        """Remove old completed states."""
        cutoff = datetime.now().timestamp() - (max_age_days * 86400)
        removed = 0
        
        for state_file in self.state_dir.glob("*_state.json"):
            if state_file.stat().st_mtime < cutoff:
                try:
                    state = PipelineState.load(state_file)
                    if state.is_complete:
                        state_file.unlink()
                        job_id = state_file.stem.replace("_state", "")
                        self._states.pop(job_id, None)
                        removed += 1
                except Exception:
                    pass
        
        return removed
