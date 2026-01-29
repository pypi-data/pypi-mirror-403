"""
Configuration management for PDF2TeX.

Uses Pydantic Settings for type-safe configuration with environment variable support.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExtractionSettings(BaseSettings):
    """Settings for the extraction layer."""

    model_config = SettingsConfigDict(env_prefix="EXTRACTION_")

    # OCR settings
    ocr_threshold: int = Field(
        default=50,
        description="Minimum characters per page to skip OCR",
    )
    ocr_language: str = Field(default="en", description="OCR language code")
    ocr_use_gpu: bool = Field(default=True, description="Use GPU for OCR")

    # Nougat settings
    nougat_model: str = Field(
        default="facebook/nougat-base",
        description="Nougat model for math extraction",
    )
    nougat_batch_size: int = Field(default=4, description="Batch size for Nougat")

    # Processing
    max_pages_per_batch: int = Field(
        default=50,
        description="Maximum pages per extraction batch",
    )


class ChunkingSettings(BaseSettings):
    """Settings for the chunking layer."""

    model_config = SettingsConfigDict(env_prefix="CHUNKING_")

    # Chunk sizes by content type
    text_chunk_size: int = Field(default=512, description="Token size for text chunks")
    text_chunk_overlap: int = Field(default=64, description="Overlap between text chunks")
    caption_chunk_size: int = Field(default=256, description="Token size for captions")

    # Chapter detection
    min_chapter_pages: int = Field(default=5, description="Minimum pages for a chapter")
    heading_patterns: list[str] = Field(
        default=["Chapter", "CHAPTER", "Part", "PART", "Section"],
        description="Patterns to detect chapter headings",
    )


class RAGSettings(BaseSettings):
    """Settings for the RAG layer."""

    model_config = SettingsConfigDict(env_prefix="RAG_")

    # Embedding model
    embedding_model: str = Field(
        default="BAAI/bge-m3",
        description="Sentence transformer model for embeddings",
    )
    embedding_dimension: int = Field(default=1024, description="Embedding vector dimension")

    # Reranker
    reranker_model: str = Field(
        default="BAAI/bge-reranker-v2-m3",
        description="Cross-encoder model for reranking",
    )

    # Retrieval settings
    retrieval_top_k: int = Field(default=20, description="Initial retrieval count")
    rerank_top_k: int = Field(default=5, description="Final reranked count")
    include_adjacent_chunks: bool = Field(
        default=True,
        description="Include adjacent chunks for context",
    )


class GenerationSettings(BaseSettings):
    """Settings for the generation layer."""

    model_config = SettingsConfigDict(env_prefix="GENERATION_")

    # Primary LLM
    primary_model: str = Field(
        default="meta-llama/Llama-3.1-70B-Instruct",
        description="Primary LLM model",
    )
    fallback_model: str = Field(
        default="mistralai/Mixtral-8x22B-Instruct-v0.1",
        description="Fallback LLM model",
    )
    math_model: str = Field(
        default="deepseek-ai/deepseek-math-7b-instruct",
        description="Specialized math LLM",
    )

    # Generation parameters
    max_tokens: int = Field(default=4096, description="Maximum generation tokens")
    temperature: float = Field(default=0.1, description="Generation temperature")
    top_p: float = Field(default=0.95, description="Top-p sampling")

    # Validation
    max_retries: int = Field(default=3, description="Max retries on validation failure")
    compile_check: bool = Field(default=True, description="Run LaTeX compile check")


class PipelineSettings(BaseSettings):
    """Settings for the pipeline orchestrator."""

    model_config = SettingsConfigDict(env_prefix="PIPELINE_")

    # Worker settings
    num_extraction_workers: int = Field(default=5, description="Extraction workers")
    num_chunking_workers: int = Field(default=5, description="Chunking workers")
    num_generation_workers: int = Field(default=5, description="Generation workers")

    # GPU allocation
    extraction_gpu_fraction: float = Field(
        default=0.25,
        description="GPU fraction per extraction worker",
    )
    generation_gpu_fraction: float = Field(
        default=0.5,
        description="GPU fraction per generation worker",
    )

    # Checkpointing
    checkpoint_interval: int = Field(
        default=10,
        description="Checkpoint every N chapters",
    )
    enable_resume: bool = Field(default=True, description="Enable resume from checkpoint")


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="pdf2tex", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level",
    )

    # Paths
    output_dir: Path = Field(
        default=Path("./output"),
        description="Default output directory",
    )
    temp_dir: Path = Field(
        default=Path("/tmp/pdf2tex"),
        description="Temporary files directory",
    )

    # Hugging Face
    huggingface_token: SecretStr = Field(
        ...,
        description="Hugging Face API token",
    )

    # Database
    postgres_url: str = Field(
        default="postgresql+asyncpg://pdf2tex:password@localhost:5432/pdf2tex",
        description="PostgreSQL connection URL",
    )

    # Vector Store
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant server URL",
    )
    qdrant_api_key: SecretStr | None = Field(
        default=None,
        description="Qdrant API key (optional)",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL",
    )

    # MinIO
    minio_endpoint: str = Field(
        default="localhost:9000",
        description="MinIO endpoint",
    )
    minio_access_key: str = Field(default="minioadmin", description="MinIO access key")
    minio_secret_key: SecretStr = Field(
        default=SecretStr("minioadmin"),
        description="MinIO secret key",
    )
    minio_bucket: str = Field(default="pdf2tex", description="MinIO bucket name")
    minio_secure: bool = Field(default=False, description="Use HTTPS for MinIO")

    # Ray
    ray_address: str | None = Field(
        default=None,
        description="Ray cluster address (None for local)",
    )

    # Sub-settings
    extraction: ExtractionSettings = Field(default_factory=ExtractionSettings)
    chunking: ChunkingSettings = Field(default_factory=ChunkingSettings)
    rag: RAGSettings = Field(default_factory=RAGSettings)
    generation: GenerationSettings = Field(default_factory=GenerationSettings)
    pipeline: PipelineSettings = Field(default_factory=PipelineSettings)

    @field_validator("output_dir", "temp_dir", mode="before")
    @classmethod
    def ensure_path(cls, v: str | Path) -> Path:
        """Ensure path is a Path object."""
        return Path(v) if isinstance(v, str) else v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
