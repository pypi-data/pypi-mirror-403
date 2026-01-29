"""
Generation service coordinating LaTeX generation.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog

from pdf2tex.chunking.models import Chapter, ChunkingResult
from pdf2tex.config import GenerationSettings, Settings
from pdf2tex.generation.llm import GenerationConfig, LLMClient, LLMResponse
from pdf2tex.generation.prompts import PromptManager
from pdf2tex.generation.validator import LaTeXValidator, ValidationResult
from pdf2tex.rag.service import RAGService

logger = structlog.get_logger(__name__)


@dataclass
class GeneratedChapter:
    """A generated LaTeX chapter."""

    title: str
    number: int | str
    latex_content: str
    validation: ValidationResult
    source_chapter: Chapter
    metadata: dict[str, Any]


@dataclass
class GeneratedDocument:
    """A complete generated LaTeX document."""

    preamble: str
    chapters: list[GeneratedChapter]
    bibliography: str | None
    appendices: list[str]
    metadata: dict[str, Any]


class GenerationService:
    """
    Orchestrates LaTeX generation from document chunks.
    
    Coordinates:
    - LLM interaction
    - Prompt management
    - LaTeX validation
    - RAG-enhanced generation
    """

    def __init__(
        self,
        settings: Settings | None = None,
        rag_service: RAGService | None = None,
    ) -> None:
        """
        Initialize generation service.

        Args:
            settings: Application settings
            rag_service: RAG service for context retrieval
        """
        self.settings = settings or Settings()
        self.generation_settings: GenerationSettings = self.settings.generation
        self.rag_service = rag_service

        # Initialize components
        self._llm_client: LLMClient | None = None
        self._prompt_manager: PromptManager | None = None
        self._validator: LaTeXValidator | None = None
        
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all generation components."""
        if self._initialized:
            return

        logger.info("Initializing generation service")

        # Get API key
        api_key = self.generation_settings.huggingface_api_key
        if api_key:
            api_key = api_key.get_secret_value()

        # Initialize LLM client
        self._llm_client = LLMClient(
            api_key=api_key,
            model_name=self.generation_settings.model_name,
            fallback_models=self.generation_settings.fallback_models,
            timeout=self.generation_settings.timeout,
        )
        await self._llm_client.initialize()

        # Initialize prompt manager
        self._prompt_manager = PromptManager()

        # Initialize validator
        self._validator = LaTeXValidator(
            check_compilation=self.generation_settings.validate_output,
        )

        self._initialized = True
        logger.info("Generation service initialized")

    async def generate_document(
        self,
        chunking_result: ChunkingResult,
        progress_callback: Any | None = None,
    ) -> GeneratedDocument:
        """
        Generate complete LaTeX document.

        Args:
            chunking_result: Chunking result with chapters
            progress_callback: Optional progress callback

        Returns:
            Generated document
        """
        if not self._initialized:
            await self.initialize()

        document_id = chunking_result.document_id
        logger.info(
            "Generating document",
            document_id=document_id,
            chapters=len(chunking_result.chapters),
        )

        # Analyze document properties
        doc_properties = self._analyze_document(chunking_result)

        # Generate preamble
        preamble = await self._generate_preamble(doc_properties)

        # Generate chapters
        generated_chapters: list[GeneratedChapter] = []
        
        for i, chapter in enumerate(chunking_result.chapters):
            if progress_callback:
                await progress_callback({
                    "phase": "generation",
                    "current": i,
                    "total": len(chunking_result.chapters),
                    "chapter": chapter.title,
                })

            gen_chapter = await self._generate_chapter(
                chapter,
                document_id,
                i + 1,
            )
            generated_chapters.append(gen_chapter)

        return GeneratedDocument(
            preamble=preamble,
            chapters=generated_chapters,
            bibliography=None,
            appendices=[],
            metadata={
                "document_id": document_id,
                "source_path": str(chunking_result.source_path),
                **doc_properties,
            },
        )

    async def generate_chapter(
        self,
        chapter: Chapter,
        document_id: str,
        chapter_number: int,
    ) -> GeneratedChapter:
        """
        Generate a single chapter.

        Args:
            chapter: Chapter to generate
            document_id: Document identifier
            chapter_number: Chapter number

        Returns:
            Generated chapter
        """
        if not self._initialized:
            await self.initialize()

        return await self._generate_chapter(chapter, document_id, chapter_number)

    async def _generate_chapter(
        self,
        chapter: Chapter,
        document_id: str,
        chapter_number: int,
    ) -> GeneratedChapter:
        """Internal chapter generation."""
        logger.info(
            "Generating chapter",
            title=chapter.title,
            number=chapter_number,
        )

        # Get context from RAG if available
        context = ""
        if self.rag_service:
            try:
                context_chunks = await self.rag_service.retrieve_for_chapter(
                    chapter.content,
                    document_id,
                    top_k=10,
                )
                context = "\n\n".join(
                    f"[Context from {c.metadata.section_string or 'document'}]\n{c.content}"
                    for c in context_chunks[:5]
                )
            except Exception as e:
                logger.warning("Failed to retrieve context", error=str(e))

        # Create prompt
        prompt = self._prompt_manager.get_chapter_prompt(
            title=chapter.title,
            number=chapter_number,
            content=chapter.content,
            context=context,
        )

        # Generate with LLM
        config = GenerationConfig(
            max_tokens=self.generation_settings.max_tokens,
            temperature=self.generation_settings.temperature,
        )

        response = await self._llm_client.generate(
            prompt.user_template,
            system_prompt=prompt.system,
            config=config,
        )

        latex_content = self._clean_latex_output(response.content)

        # Validate
        validation = await self._validator.validate(latex_content, is_fragment=True)

        # Attempt repair if invalid
        if not validation.valid and self.generation_settings.validate_output:
            latex_content, validation = await self._repair_latex(
                latex_content, validation
            )

        return GeneratedChapter(
            title=chapter.title,
            number=chapter_number,
            latex_content=latex_content,
            validation=validation,
            source_chapter=chapter,
            metadata={
                "model": response.model,
                "context_chunks": len(context.split("[Context from")) - 1,
            },
        )

    async def _generate_preamble(
        self,
        doc_properties: dict[str, Any],
    ) -> str:
        """Generate document preamble."""
        prompt = self._prompt_manager.get_preamble_prompt(
            doc_type=doc_properties.get("doc_type", "book"),
            title=doc_properties.get("title", "Document"),
            author=doc_properties.get("author", ""),
            has_math=doc_properties.get("has_math", True),
            has_code=doc_properties.get("has_code", False),
            has_figures=doc_properties.get("has_figures", True),
            has_tables=doc_properties.get("has_tables", True),
        )

        config = GenerationConfig(
            max_tokens=1024,
            temperature=0.1,
        )

        response = await self._llm_client.generate(
            prompt.user_template,
            system_prompt=prompt.system,
            config=config,
        )

        return self._clean_latex_output(response.content)

    def _analyze_document(
        self,
        chunking_result: ChunkingResult,
    ) -> dict[str, Any]:
        """Analyze document properties."""
        has_math = any(
            chunk.metadata.has_math
            for chunk in chunking_result.all_chunks
        )
        has_code = any(
            chunk.metadata.has_code
            for chunk in chunking_result.all_chunks
        )
        has_tables = any(
            chunk.metadata.has_table
            for chunk in chunking_result.all_chunks
        )

        return {
            "title": chunking_result.document_id.replace("_", " ").title(),
            "has_math": has_math,
            "has_code": has_code,
            "has_tables": has_tables,
            "has_figures": True,
            "doc_type": "book" if len(chunking_result.chapters) > 3 else "article",
            "total_chapters": len(chunking_result.chapters),
            "total_chunks": len(chunking_result.all_chunks),
        }

    def _clean_latex_output(self, content: str) -> str:
        """Clean LLM output to pure LaTeX."""
        # Remove markdown code fences
        content = content.strip()
        
        if content.startswith("```latex"):
            content = content[8:]
        elif content.startswith("```"):
            content = content[3:]
        
        if content.endswith("```"):
            content = content[:-3]

        return content.strip()

    async def _repair_latex(
        self,
        latex_content: str,
        validation: ValidationResult,
    ) -> tuple[str, ValidationResult]:
        """Attempt to repair invalid LaTeX."""
        # Try auto-repair first
        repaired, repairs = self._validator.repair_common_issues(latex_content)
        
        if repairs:
            new_validation = await self._validator.validate(repaired, is_fragment=True)
            if new_validation.valid:
                logger.info("Auto-repair successful", repairs=repairs)
                return repaired, new_validation

        # Try LLM-based repair
        error_messages = [e.message for e in validation.errors[:5]]
        prompt = self._prompt_manager.get_fix_prompt(latex_content, error_messages)

        config = GenerationConfig(
            max_tokens=self.generation_settings.max_tokens,
            temperature=0.1,
        )

        try:
            response = await self._llm_client.generate(
                prompt.user_template,
                system_prompt=prompt.system,
                config=config,
            )

            fixed_content = self._clean_latex_output(response.content)
            new_validation = await self._validator.validate(fixed_content, is_fragment=True)

            if new_validation.valid or len(new_validation.errors) < len(validation.errors):
                logger.info("LLM repair improved code")
                return fixed_content, new_validation

        except Exception as e:
            logger.warning("LLM repair failed", error=str(e))

        # Return original if repair failed
        return latex_content, validation

    async def regenerate_chapter(
        self,
        chapter: GeneratedChapter,
        feedback: str,
    ) -> GeneratedChapter:
        """
        Regenerate chapter with feedback.

        Args:
            chapter: Previously generated chapter
            feedback: User feedback for improvement

        Returns:
            Regenerated chapter
        """
        if not self._initialized:
            await self.initialize()

        prompt = f"""Improve the following LaTeX chapter based on feedback.

Current LaTeX:
{chapter.latex_content}

Feedback:
{feedback}

Generate improved LaTeX code."""

        config = GenerationConfig(
            max_tokens=self.generation_settings.max_tokens,
            temperature=0.3,
        )

        response = await self._llm_client.generate(
            prompt,
            system_prompt=self._prompt_manager.SYSTEM_LATEX_EXPERT,
            config=config,
        )

        latex_content = self._clean_latex_output(response.content)
        validation = await self._validator.validate(latex_content, is_fragment=True)

        return GeneratedChapter(
            title=chapter.title,
            number=chapter.number,
            latex_content=latex_content,
            validation=validation,
            source_chapter=chapter.source_chapter,
            metadata={
                **chapter.metadata,
                "regenerated": True,
                "feedback": feedback,
            },
        )

    def get_status(self) -> dict[str, Any]:
        """Get service status."""
        return {
            "initialized": self._initialized,
            "settings": {
                "model": self.generation_settings.model_name,
                "max_tokens": self.generation_settings.max_tokens,
                "temperature": self.generation_settings.temperature,
            },
        }

    async def close(self) -> None:
        """Close all connections."""
        if self._llm_client:
            await self._llm_client.close()
        
        self._llm_client = None
        self._prompt_manager = None
        self._validator = None
        self._initialized = False
        
        logger.info("Generation service closed")
