"""
Prompt templates for LaTeX generation.

Provides structured prompts for different generation tasks.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Prompt:
    """A prompt template."""

    name: str
    system: str
    user_template: str
    description: str = ""


class PromptManager:
    """
    Manages prompt templates for LaTeX generation.
    
    Provides prompts for:
    - Document structure generation
    - Chapter content generation
    - Math expression formatting
    - Table conversion
    - Figure reference handling
    """

    # System prompts
    SYSTEM_LATEX_EXPERT = """You are an expert LaTeX document author with deep knowledge of:
- LaTeX document structure and best practices
- Mathematical typesetting with amsmath, amssymb, mathtools
- Professional document formatting
- Academic writing conventions

Your task is to generate high-quality LaTeX code that:
1. Is syntactically correct and compiles without errors
2. Follows LaTeX best practices and conventions
3. Produces professional, readable output
4. Preserves all mathematical expressions accurately

Always use:
- Proper document class and packages
- Semantic markup (\\section, \\subsection, etc.)
- Appropriate math environments (equation, align, gather)
- Consistent formatting throughout"""

    SYSTEM_MATH_SPECIALIST = """You are a mathematical typesetting specialist.
Your expertise includes:
- Converting mathematical notation to precise LaTeX
- Choosing appropriate math environments
- Handling complex equations and proofs
- Ensuring mathematical accuracy

Guidelines:
- Use \\[ \\] or equation environment for display math
- Use $ $ for inline math
- Use align/gather for multi-line equations
- Number important equations
- Use \\text{} for text within math mode"""

    SYSTEM_STRUCTURE_ANALYST = """You are a document structure analyst.
Analyze the provided content and identify:
- Logical chapter/section boundaries
- Heading hierarchy
- Content relationships
- Cross-references

Output structured information about document organization."""

    # User prompt templates
    TEMPLATES = {
        "generate_chapter": """Generate LaTeX code for the following chapter content.

Chapter Title: {title}
Chapter Number: {number}

Content to convert:
{content}

Context from other parts of the document:
{context}

Requirements:
- Use \\chapter{{{title}}} as the chapter heading
- Preserve all mathematical expressions exactly
- Use appropriate sectioning (\\section, \\subsection)
- Include proper labels for cross-referencing
- Format code blocks with listings or minted package

Output only the LaTeX code, no explanations.""",

        "generate_section": """Generate LaTeX for this section.

Section: {section_path}
Content:
{content}

Related context:
{context}

Requirements:
- Start with appropriate section command
- Preserve math expressions
- Add labels for cross-referencing

Output LaTeX code only.""",

        "format_math": """Convert this mathematical content to LaTeX.

Mathematical content:
{math_content}

Surrounding context:
{context}

Requirements:
- Use appropriate math environment
- Ensure equation numbers where appropriate
- Handle special symbols correctly

Output LaTeX only.""",

        "format_table": """Convert this table to LaTeX.

Table content:
{table_content}

Caption: {caption}

Requirements:
- Use tabular environment
- Add proper column formatting
- Include caption and label
- Handle merged cells if present

Output LaTeX only.""",

        "generate_preamble": """Generate a LaTeX preamble for a document with these characteristics:

Document type: {doc_type}
Title: {title}
Author: {author}
Contains math: {has_math}
Contains code: {has_code}
Contains figures: {has_figures}
Contains tables: {has_tables}

Required packages based on content:
{required_packages}

Generate a complete preamble with:
- documentclass declaration
- necessary packages
- custom commands if needed
- document information

Output LaTeX preamble only.""",

        "fix_latex_errors": """Fix the LaTeX errors in this code.

Original code:
{latex_code}

Errors reported:
{errors}

Provide corrected LaTeX code only, no explanations.""",

        "improve_formatting": """Improve the formatting of this LaTeX code.

Current code:
{latex_code}

Issues to address:
{issues}

Provide improved LaTeX code only.""",
    }

    def __init__(
        self,
        custom_templates_dir: Path | None = None,
    ) -> None:
        """
        Initialize prompt manager.

        Args:
            custom_templates_dir: Directory for custom templates
        """
        self.templates = dict(self.TEMPLATES)
        
        if custom_templates_dir and custom_templates_dir.exists():
            self._load_custom_templates(custom_templates_dir)

    def _load_custom_templates(self, directory: Path) -> None:
        """Load custom templates from directory."""
        for file in directory.glob("*.txt"):
            name = file.stem
            content = file.read_text()
            self.templates[name] = content
            logger.info("Loaded custom template", name=name)

    def get_prompt(
        self,
        name: str,
        **kwargs: Any,
    ) -> Prompt:
        """
        Get a formatted prompt.

        Args:
            name: Template name
            **kwargs: Template variables

        Returns:
            Formatted Prompt object
        """
        if name not in self.templates:
            raise ValueError(f"Unknown template: {name}")

        template = self.templates[name]
        
        # Determine system prompt
        if "math" in name.lower():
            system = self.SYSTEM_MATH_SPECIALIST
        elif "structure" in name.lower():
            system = self.SYSTEM_STRUCTURE_ANALYST
        else:
            system = self.SYSTEM_LATEX_EXPERT

        # Format template
        try:
            user_prompt = template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")

        return Prompt(
            name=name,
            system=system,
            user_template=user_prompt,
        )

    def get_chapter_prompt(
        self,
        title: str,
        number: int | str,
        content: str,
        context: str = "",
    ) -> Prompt:
        """Get prompt for chapter generation."""
        return self.get_prompt(
            "generate_chapter",
            title=title,
            number=number,
            content=content,
            context=context or "No additional context provided.",
        )

    def get_math_prompt(
        self,
        math_content: str,
        context: str = "",
    ) -> Prompt:
        """Get prompt for math formatting."""
        return self.get_prompt(
            "format_math",
            math_content=math_content,
            context=context or "No additional context provided.",
        )

    def get_preamble_prompt(
        self,
        doc_type: str = "book",
        title: str = "Document",
        author: str = "",
        has_math: bool = True,
        has_code: bool = False,
        has_figures: bool = True,
        has_tables: bool = True,
    ) -> Prompt:
        """Get prompt for preamble generation."""
        # Determine required packages
        packages = ["inputenc", "fontenc", "geometry", "hyperref"]
        if has_math:
            packages.extend(["amsmath", "amssymb", "mathtools"])
        if has_code:
            packages.extend(["listings", "xcolor"])
        if has_figures:
            packages.extend(["graphicx", "float"])
        if has_tables:
            packages.extend(["booktabs", "array"])

        return self.get_prompt(
            "generate_preamble",
            doc_type=doc_type,
            title=title,
            author=author,
            has_math=str(has_math),
            has_code=str(has_code),
            has_figures=str(has_figures),
            has_tables=str(has_tables),
            required_packages=", ".join(packages),
        )

    def get_fix_prompt(
        self,
        latex_code: str,
        errors: list[str],
    ) -> Prompt:
        """Get prompt for fixing LaTeX errors."""
        return self.get_prompt(
            "fix_latex_errors",
            latex_code=latex_code,
            errors="\n".join(f"- {e}" for e in errors),
        )

    def add_template(
        self,
        name: str,
        template: str,
    ) -> None:
        """Add a custom template."""
        self.templates[name] = template
        logger.info("Added custom template", name=name)

    def list_templates(self) -> list[str]:
        """List available template names."""
        return list(self.templates.keys())

    def get_template_info(self, name: str) -> dict[str, Any]:
        """Get information about a template."""
        if name not in self.templates:
            raise ValueError(f"Unknown template: {name}")

        template = self.templates[name]
        
        # Extract variables
        import re
        variables = re.findall(r"\{(\w+)\}", template)

        return {
            "name": name,
            "variables": list(set(variables)),
            "length": len(template),
        }
