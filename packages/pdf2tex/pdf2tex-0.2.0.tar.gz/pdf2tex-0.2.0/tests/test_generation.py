"""
Tests for PDF2TeX generation layer.
Tests match actual implementation APIs.
"""

import pytest
import asyncio


class TestLaTeXValidator:
    """Tests for LaTeXValidator class."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        from pdf2tex.generation.validator import LaTeXValidator
        return LaTeXValidator()

    @pytest.mark.asyncio
    async def test_valid_latex(self, validator) -> None:
        """Test valid LaTeX passes validation."""
        latex = r"""
\documentclass{article}
\begin{document}
Hello, World!
\end{document}
"""
        result = await validator.validate(latex)
        assert result.valid

    @pytest.mark.asyncio
    async def test_unclosed_environment(self, validator) -> None:
        """Test unclosed environment detection."""
        latex = r"""
\begin{itemize}
\item First item
\item Second item
"""
        result = await validator.validate(latex)
        assert not result.valid
        assert any("Unclosed" in e.message for e in result.errors)

    @pytest.mark.asyncio
    async def test_mismatched_environments(self, validator) -> None:
        """Test mismatched environment detection."""
        latex = r"""
\begin{itemize}
\item Item
\end{enumerate}
"""
        result = await validator.validate(latex)
        assert not result.valid

    @pytest.mark.asyncio
    async def test_unbalanced_math_delimiters(self, validator) -> None:
        """Test unbalanced math delimiter detection."""
        latex = r"The equation $x^2 + y^2 is important."
        result = await validator.validate(latex)
        assert not result.valid
        assert any("$" in e.message or "math" in e.message.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_valid_math(self, validator) -> None:
        """Test valid math passes validation."""
        latex = r"The equation $x^2 + y^2 = r^2$ describes a circle."
        result = await validator.validate(latex)
        assert result.valid

    @pytest.mark.asyncio
    async def test_display_math(self, validator) -> None:
        """Test display math validation."""
        latex = r"""
Simple display math:
$$x^2 + y^2 = r^2$$
"""
        result = await validator.validate(latex)
        assert result.valid

    @pytest.mark.asyncio
    async def test_nested_environments(self, validator) -> None:
        """Test nested environment validation."""
        latex = r"""
\begin{theorem}
Let $f$ be continuous. Then:
\begin{equation}
\int_a^b f(x) dx = F(b) - F(a)
\end{equation}
\end{theorem}
"""
        result = await validator.validate(latex)
        assert result.valid

    def test_quick_check_valid(self, validator) -> None:
        """Test quick_check with valid LaTeX."""
        latex = r"\begin{equation}x^2\end{equation}"
        assert validator.quick_check(latex)

    def test_quick_check_invalid(self, validator) -> None:
        """Test quick_check with invalid LaTeX."""
        # Unclosed environment
        assert not validator.quick_check(r"\begin{equation}x^2")
        # Unbalanced braces
        assert not validator.quick_check(r"\frac{1}{2")
        # Unbalanced math
        assert not validator.quick_check(r"$x^2")

    def test_repair_common_issues(self, validator) -> None:
        """Test repair functionality."""
        # Test multiple line breaks repair
        latex = r"text\\\\\\\\more text"
        repaired, repairs = validator.repair_common_issues(latex)
        
        assert len(repairs) > 0 or repaired != latex


class TestValidationResult:
    """Tests for ValidationResult structure."""

    @pytest.mark.asyncio
    async def test_result_structure(self) -> None:
        """Test validation result has expected structure."""
        from pdf2tex.generation.validator import LaTeXValidator
        
        validator = LaTeXValidator()
        result = await validator.validate(r"\documentclass{article}")
        
        assert hasattr(result, "valid")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "info")
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestValidatorWithRealLatex:
    """Integration tests with real LaTeX samples."""

    @pytest.mark.asyncio
    async def test_arxiv_style_latex(self) -> None:
        """Test validation of arXiv-style LaTeX."""
        from pdf2tex.generation.validator import LaTeXValidator
        
        validator = LaTeXValidator()
        latex = r"""
\documentclass{article}
\usepackage{amsmath,amssymb,graphicx}

\begin{document}

\section{Introduction}

The Transformer follows this overall architecture using stacked self-attention
and point-wise, fully connected layers for both the encoder and decoder.

\begin{equation}
\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V
\end{equation}

\end{document}
"""
        result = await validator.validate(latex)
        assert result.valid, f"Errors: {[e.message for e in result.errors]}"

    @pytest.mark.asyncio
    async def test_math_heavy_latex(self) -> None:
        """Test validation of math-heavy LaTeX."""
        from pdf2tex.generation.validator import LaTeXValidator
        
        validator = LaTeXValidator()
        latex = r"""
\documentclass{article}
\usepackage{amsmath}

\begin{document}

\begin{align}
m_t &= \beta_1 m_{t-1} + (1 - \beta_1) g_t \\
v_t &= \beta_2 v_{t-1} + (1 - \beta_2) g_t^2
\end{align}

\end{document}
"""
        result = await validator.validate(latex)
        assert result.valid, f"Errors: {[e.message for e in result.errors]}"
