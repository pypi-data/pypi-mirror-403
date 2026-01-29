"""
Mathematical content extraction using Nougat and TexTeller.

Handles extraction of inline and display equations from PDF pages
with high accuracy for scientific documents.
"""

import asyncio
import re
import tempfile
from pathlib import Path
from typing import Any

import structlog
import torch
from PIL import Image

from pdf2tex.extraction.models import BoundingBox, ContentType, MathRegion

logger = structlog.get_logger(__name__)


class MathExtractor:
    """
    Extract mathematical equations from PDF pages using neural models.
    
    Uses Nougat as the primary model for scientific PDFs, with TexTeller
    as a fallback for individual equation images.
    """

    # Common LaTeX error patterns for auto-repair
    REPAIR_PATTERNS = [
        # Missing closing braces
        (r"\\frac\{([^}]+)\}\{([^}]+)$", r"\\frac{\1}{\2}"),
        # Unescaped underscores in text
        (r"(?<!\\)_(?![{])", r"\\_"),
        # Missing dollar signs for inline math
        (r"(?<![\\$])\\(?:alpha|beta|gamma|delta|epsilon|theta|lambda|mu|pi|sigma|omega)", 
         r"$\g<0>$"),
        # Double backslashes in wrong context
        (r"\\\\(?![a-zA-Z])", r"\\"),
    ]

    def __init__(
        self,
        model_name: str = "facebook/nougat-base",
        device: str | None = None,
        batch_size: int = 4,
    ) -> None:
        """
        Initialize the math extractor.

        Args:
            model_name: Hugging Face model name for Nougat
            device: Device to run models on (auto-detected if None)
            batch_size: Batch size for processing
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        self._nougat_model = None
        self._nougat_processor = None
        self._repair_regex = [
            (re.compile(p), r) for p, r in self.REPAIR_PATTERNS
        ]

    async def initialize(self) -> None:
        """Load models asynchronously."""
        await asyncio.to_thread(self._load_models)

    def _load_models(self) -> None:
        """Load Nougat model and processor."""
        try:
            from transformers import NougatProcessor, VisionEncoderDecoderModel
            
            logger.info("Loading Nougat model", model=self.model_name)
            
            self._nougat_processor = NougatProcessor.from_pretrained(self.model_name)
            self._nougat_model = VisionEncoderDecoderModel.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            )
            self._nougat_model.to(self.device)
            self._nougat_model.eval()
            
            logger.info("Nougat model loaded successfully", device=self.device)
            
        except ImportError as e:
            logger.error("Failed to import Nougat dependencies", error=str(e))
            raise
        except Exception as e:
            logger.error("Failed to load Nougat model", error=str(e))
            raise

    async def extract_from_page(
        self,
        page_image: Image.Image,
        page_num: int,
    ) -> list[MathRegion]:
        """
        Extract mathematical content from a page image.

        Args:
            page_image: PIL Image of the PDF page
            page_num: Page number for metadata

        Returns:
            List of extracted math regions
        """
        if self._nougat_model is None:
            await self.initialize()

        # Process with Nougat
        latex_output = await asyncio.to_thread(
            self._process_with_nougat, page_image
        )

        # Parse LaTeX output to identify math regions
        math_regions = self._parse_math_regions(latex_output, page_num)

        return math_regions

    def _process_with_nougat(self, image: Image.Image) -> str:
        """Process a page image with Nougat model."""
        if self._nougat_processor is None or self._nougat_model is None:
            raise RuntimeError("Nougat model not initialized")

        # Prepare input
        pixel_values = self._nougat_processor(
            images=image,
            return_tensors="pt",
        ).pixel_values.to(self.device)

        if self.device == "cuda":
            pixel_values = pixel_values.half()

        # Generate
        with torch.no_grad():
            outputs = self._nougat_model.generate(
                pixel_values,
                max_new_tokens=4096,
                do_sample=False,
                num_beams=1,
                pad_token_id=self._nougat_processor.tokenizer.pad_token_id,
                eos_token_id=self._nougat_processor.tokenizer.eos_token_id,
            )

        # Decode
        generated_text = self._nougat_processor.batch_decode(
            outputs, skip_special_tokens=True
        )[0]

        return generated_text

    def _parse_math_regions(
        self,
        latex_output: str,
        page_num: int,
    ) -> list[MathRegion]:
        """Parse Nougat output to extract individual math regions."""
        math_regions: list[MathRegion] = []

        # Pattern for display math ($$...$$, \[...\], equation environments)
        display_patterns = [
            r"\$\$(.*?)\$\$",
            r"\\\[(.*?)\\\]",
            r"\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}",
            r"\\begin\{align\*?\}(.*?)\\end\{align\*?\}",
            r"\\begin\{gather\*?\}(.*?)\\end\{gather\*?\}",
            r"\\begin\{eqnarray\*?\}(.*?)\\end\{eqnarray\*?\}",
        ]

        # Pattern for inline math ($...$)
        inline_pattern = r"(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)"

        # Extract display math
        for pattern in display_patterns:
            for match in re.finditer(pattern, latex_output, re.DOTALL):
                latex = match.group(1).strip()
                if latex:
                    region = MathRegion(
                        latex=latex,
                        content_type=ContentType.MATH_DISPLAY,
                        bbox=BoundingBox(x0=0, y0=0, x1=100, y1=100),  # Placeholder
                        source="nougat",
                        confidence=0.9,
                        metadata={"page": page_num, "raw_match": match.group(0)},
                    )
                    math_regions.append(region)

        # Extract inline math
        for match in re.finditer(inline_pattern, latex_output):
            latex = match.group(1).strip()
            if latex and len(latex) > 1:  # Skip single characters
                region = MathRegion(
                    latex=latex,
                    content_type=ContentType.MATH_INLINE,
                    bbox=BoundingBox(x0=0, y0=0, x1=50, y1=20),  # Placeholder
                    source="nougat",
                    confidence=0.85,
                    metadata={"page": page_num, "raw_match": match.group(0)},
                )
                math_regions.append(region)

        return math_regions

    async def extract_from_image(
        self,
        image: Image.Image | bytes,
        content_type: ContentType = ContentType.MATH_DISPLAY,
    ) -> MathRegion | None:
        """
        Extract math from a single equation image.

        Args:
            image: PIL Image or bytes of the equation
            content_type: Type of math content

        Returns:
            Extracted math region or None if failed
        """
        if isinstance(image, bytes):
            import io
            image = Image.open(io.BytesIO(image))

        try:
            # Use Nougat for single equation
            latex = await asyncio.to_thread(self._process_with_nougat, image)
            
            # Clean up the output
            latex = self._clean_latex(latex)
            
            if not latex:
                return None

            return MathRegion(
                latex=latex,
                content_type=content_type,
                bbox=BoundingBox(x0=0, y0=0, x1=image.width, y1=image.height),
                source="nougat",
                confidence=0.85,
            )

        except Exception as e:
            logger.error("Failed to extract math from image", error=str(e))
            return None

    def _clean_latex(self, latex: str) -> str:
        """Clean and normalize LaTeX output."""
        # Remove Nougat artifacts
        latex = re.sub(r"<[^>]+>", "", latex)  # Remove HTML-like tags
        latex = re.sub(r"\[MISSING_PAGE.*?\]", "", latex)
        latex = re.sub(r"\\footnote\{[^}]*\}", "", latex)
        
        # Normalize whitespace
        latex = " ".join(latex.split())
        
        return latex.strip()

    def repair_latex(self, latex: str) -> tuple[str, list[str]]:
        """
        Attempt to repair common LaTeX errors.

        Args:
            latex: LaTeX string to repair

        Returns:
            Tuple of (repaired_latex, list of applied fixes)
        """
        fixes_applied: list[str] = []
        repaired = latex

        for pattern, replacement in self._repair_regex:
            if pattern.search(repaired):
                repaired = pattern.sub(replacement, repaired)
                fixes_applied.append(f"Applied: {pattern.pattern}")

        # Balance braces
        open_braces = repaired.count("{")
        close_braces = repaired.count("}")
        if open_braces > close_braces:
            repaired += "}" * (open_braces - close_braces)
            fixes_applied.append(f"Added {open_braces - close_braces} closing braces")
        elif close_braces > open_braces:
            repaired = "{" * (close_braces - open_braces) + repaired
            fixes_applied.append(f"Added {close_braces - open_braces} opening braces")

        return repaired, fixes_applied

    async def validate_latex(self, latex: str) -> tuple[bool, list[str]]:
        """
        Validate LaTeX math expression.

        Args:
            latex: LaTeX string to validate

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors: list[str] = []

        # Check brace balance
        if latex.count("{") != latex.count("}"):
            errors.append("Unbalanced braces")

        # Check common command syntax
        unmatched_commands = re.findall(r"\\[a-zA-Z]+(?!\{)", latex)
        commands_needing_args = {"frac", "sqrt", "text", "mathrm", "mathbf", "mathit"}
        for cmd in unmatched_commands:
            cmd_name = cmd[1:]  # Remove backslash
            if cmd_name in commands_needing_args:
                if f"\\{cmd_name}{{" not in latex:
                    errors.append(f"Command \\{cmd_name} may need arguments")

        # Check for invalid characters
        invalid_chars = re.findall(r"[^\x00-\x7F]", latex)
        if invalid_chars:
            unique_invalid = set(invalid_chars)
            errors.append(f"Non-ASCII characters: {unique_invalid}")

        return len(errors) == 0, errors

    async def batch_extract(
        self,
        page_images: list[Image.Image],
        page_numbers: list[int],
    ) -> list[list[MathRegion]]:
        """
        Extract math from multiple pages in batch.

        Args:
            page_images: List of page images
            page_numbers: Corresponding page numbers

        Returns:
            List of math regions per page
        """
        results: list[list[MathRegion]] = []
        
        for i in range(0, len(page_images), self.batch_size):
            batch_images = page_images[i:i + self.batch_size]
            batch_pages = page_numbers[i:i + self.batch_size]
            
            batch_results = await asyncio.gather(
                *[
                    self.extract_from_page(img, page)
                    for img, page in zip(batch_images, batch_pages)
                ]
            )
            results.extend(batch_results)

        return results

    def get_model_info(self) -> dict[str, Any]:
        """Get information about loaded models."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "batch_size": self.batch_size,
            "loaded": self._nougat_model is not None,
        }
