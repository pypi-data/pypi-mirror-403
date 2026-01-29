"""
LaTeX validation and error checking.

Validates generated LaTeX code for correctness.
"""

import asyncio
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ValidationError:
    """A LaTeX validation error."""

    line: int | None
    message: str
    severity: str  # error, warning, info
    code: str | None = None


@dataclass
class ValidationResult:
    """Result of LaTeX validation."""

    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)
    info: dict[str, Any] = field(default_factory=dict)


class LaTeXValidator:
    """
    Validates LaTeX code for correctness.
    
    Performs:
    - Syntax validation
    - Environment matching
    - Command validation
    - Optional compilation test
    """

    # Common LaTeX environment pairs
    ENVIRONMENTS = [
        "document", "equation", "align", "gather", "multline",
        "figure", "table", "tabular", "itemize", "enumerate",
        "theorem", "lemma", "proof", "definition", "example",
        "abstract", "center", "flushleft", "flushright",
        "minipage", "array", "matrix", "pmatrix", "bmatrix",
        "cases", "split", "aligned", "gathered",
    ]

    # Paired delimiters
    DELIMITERS = [
        (r"\{", r"\}"),
        (r"\[", r"\]"),
        (r"\(", r"\)"),
        ("\\begin{", "\\end{"),
        ("$", "$"),
        ("$$", "$$"),
    ]

    # Common issues to check
    ISSUE_PATTERNS = [
        (r"\\\\\\\\", "Multiple consecutive line breaks"),
        (r"(?<!\\)%(?!.*$)", "Unescaped percent sign"),
        (r"(?<!\\)&(?!.*\\\\)", "Ampersand outside tabular"),
        (r"\\label\{[^}]*\s[^}]*\}", "Space in label name"),
        (r"\\ref\{[^}]*\s[^}]*\}", "Space in reference name"),
    ]

    def __init__(
        self,
        latex_compiler: str = "pdflatex",
        compile_timeout: int = 30,
        check_compilation: bool = False,
    ) -> None:
        """
        Initialize validator.

        Args:
            latex_compiler: LaTeX compiler to use
            compile_timeout: Compilation timeout in seconds
            check_compilation: Whether to test compilation
        """
        self.latex_compiler = latex_compiler
        self.compile_timeout = compile_timeout
        self.check_compilation = check_compilation

    async def validate(
        self,
        latex_code: str,
        is_fragment: bool = False,
    ) -> ValidationResult:
        """
        Validate LaTeX code.

        Args:
            latex_code: LaTeX code to validate
            is_fragment: Whether code is a fragment (not full document)

        Returns:
            Validation result
        """
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        # Basic syntax checks
        syntax_errors = self._check_syntax(latex_code)
        errors.extend(syntax_errors)

        # Environment matching
        env_errors = self._check_environments(latex_code)
        errors.extend(env_errors)

        # Delimiter matching
        delim_errors = self._check_delimiters(latex_code)
        errors.extend(delim_errors)

        # Pattern-based checks
        pattern_warnings = self._check_patterns(latex_code)
        warnings.extend(pattern_warnings)

        # Math mode checks
        math_errors = self._check_math(latex_code)
        errors.extend(math_errors)

        # Optional compilation test
        if self.check_compilation and not is_fragment and not errors:
            compile_result = await self._test_compilation(latex_code)
            if not compile_result["success"]:
                errors.append(
                    ValidationError(
                        line=compile_result.get("line"),
                        message=compile_result.get("error", "Compilation failed"),
                        severity="error",
                        code="COMPILE_ERROR",
                    )
                )

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            info={
                "line_count": latex_code.count("\n") + 1,
                "char_count": len(latex_code),
                "has_math": "$" in latex_code or "\\[" in latex_code,
            },
        )

    def _check_syntax(self, code: str) -> list[ValidationError]:
        """Check basic syntax."""
        errors: list[ValidationError] = []

        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            # Check for unmatched braces on line
            open_braces = line.count("{") - line.count("\\{")
            close_braces = line.count("}") - line.count("\\}")
            
            # Simple heuristic: significant imbalance
            if abs(open_braces - close_braces) > 3:
                errors.append(
                    ValidationError(
                        line=i,
                        message="Possible brace imbalance",
                        severity="warning",
                        code="BRACE_IMBALANCE",
                    )
                )

        return errors

    def _check_environments(self, code: str) -> list[ValidationError]:
        """Check environment matching."""
        errors: list[ValidationError] = []

        # Find all begin/end pairs
        begin_pattern = re.compile(r"\\begin\{(\w+)\}")
        end_pattern = re.compile(r"\\end\{(\w+)\}")

        begins = [(m.group(1), m.start()) for m in begin_pattern.finditer(code)]
        ends = [(m.group(1), m.start()) for m in end_pattern.finditer(code)]

        # Stack-based matching
        stack: list[tuple[str, int]] = []
        
        events = sorted(
            [(pos, "begin", name) for name, pos in begins] +
            [(pos, "end", name) for name, pos in ends],
            key=lambda x: x[0],
        )

        for pos, event_type, name in events:
            line_num = code[:pos].count("\n") + 1
            
            if event_type == "begin":
                stack.append((name, line_num))
            else:
                if not stack:
                    errors.append(
                        ValidationError(
                            line=line_num,
                            message=f"Unmatched \\end{{{name}}}",
                            severity="error",
                            code="UNMATCHED_END",
                        )
                    )
                elif stack[-1][0] != name:
                    errors.append(
                        ValidationError(
                            line=line_num,
                            message=f"Environment mismatch: expected \\end{{{stack[-1][0]}}}, got \\end{{{name}}}",
                            severity="error",
                            code="ENV_MISMATCH",
                        )
                    )
                else:
                    stack.pop()

        # Check for unclosed environments
        for name, line_num in stack:
            errors.append(
                ValidationError(
                    line=line_num,
                    message=f"Unclosed environment: {name}",
                    severity="error",
                    code="UNCLOSED_ENV",
                )
            )

        return errors

    def _check_delimiters(self, code: str) -> list[ValidationError]:
        """Check delimiter matching."""
        errors: list[ValidationError] = []

        # Check math delimiters
        inline_math = len(re.findall(r"(?<!\\)\$(?!\$)", code))
        if inline_math % 2 != 0:
            errors.append(
                ValidationError(
                    line=None,
                    message="Unmatched $ delimiter",
                    severity="error",
                    code="UNMATCHED_MATH",
                )
            )

        display_math = code.count("$$")
        if display_math % 2 != 0:
            errors.append(
                ValidationError(
                    line=None,
                    message="Unmatched $$ delimiter",
                    severity="error",
                    code="UNMATCHED_DISPLAY",
                )
            )

        # Check \[ \]
        open_bracket = len(re.findall(r"\\\[", code))
        close_bracket = len(re.findall(r"\\\]", code))
        if open_bracket != close_bracket:
            errors.append(
                ValidationError(
                    line=None,
                    message="Unmatched \\[ or \\] delimiter",
                    severity="error",
                    code="UNMATCHED_BRACKET",
                )
            )

        return errors

    def _check_patterns(self, code: str) -> list[ValidationError]:
        """Check for common issues."""
        warnings: list[ValidationError] = []

        for pattern, message in self.ISSUE_PATTERNS:
            matches = list(re.finditer(pattern, code))
            for match in matches:
                line_num = code[:match.start()].count("\n") + 1
                warnings.append(
                    ValidationError(
                        line=line_num,
                        message=message,
                        severity="warning",
                    )
                )

        return warnings

    def _check_math(self, code: str) -> list[ValidationError]:
        """Check math mode content."""
        errors: list[ValidationError] = []

        # Find math regions
        math_regions = []
        
        # Inline math
        for match in re.finditer(r"\$([^$]+)\$", code):
            math_regions.append((match.group(1), match.start()))
        
        # Display math
        for match in re.finditer(r"\$\$([^$]+)\$\$", code):
            math_regions.append((match.group(1), match.start()))
        
        for match in re.finditer(r"\\\[(.+?)\\\]", code, re.DOTALL):
            math_regions.append((match.group(1), match.start()))

        for math_content, pos in math_regions:
            line_num = code[:pos].count("\n") + 1
            
            # Check for text without \text{}
            text_matches = re.findall(r"\b[a-zA-Z]{4,}\b", math_content)
            for text in text_matches:
                if text not in ["sin", "cos", "tan", "log", "exp", "lim", "max", "min", "sup", "inf"]:
                    if f"\\text{{{text}}}" not in math_content and f"\\mathrm{{{text}}}" not in math_content:
                        errors.append(
                            ValidationError(
                                line=line_num,
                                message=f"Possible unformatted text in math: '{text}'",
                                severity="warning",
                            )
                        )
                        break  # One warning per region

        return errors

    async def _test_compilation(self, code: str) -> dict[str, Any]:
        """Test actual compilation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_file = Path(tmpdir) / "test.tex"
            tex_file.write_text(code)

            try:
                result = await asyncio.to_thread(
                    subprocess.run,
                    [
                        self.latex_compiler,
                        "-interaction=nonstopmode",
                        "-halt-on-error",
                        str(tex_file),
                    ],
                    cwd=tmpdir,
                    capture_output=True,
                    timeout=self.compile_timeout,
                )

                if result.returncode == 0:
                    return {"success": True}

                # Parse error from log
                log_file = Path(tmpdir) / "test.log"
                if log_file.exists():
                    log_content = log_file.read_text()
                    error_match = re.search(r"^! (.+)$", log_content, re.MULTILINE)
                    line_match = re.search(r"l\.(\d+)", log_content)
                    
                    return {
                        "success": False,
                        "error": error_match.group(1) if error_match else "Unknown error",
                        "line": int(line_match.group(1)) if line_match else None,
                    }

                return {"success": False, "error": "Compilation failed"}

            except subprocess.TimeoutExpired:
                return {"success": False, "error": "Compilation timeout"}
            except Exception as e:
                return {"success": False, "error": str(e)}

    def quick_check(self, code: str) -> bool:
        """Quick validation without detailed errors."""
        # Environment matching
        begins = len(re.findall(r"\\begin\{", code))
        ends = len(re.findall(r"\\end\{", code))
        if begins != ends:
            return False

        # Math delimiter matching
        dollars = len(re.findall(r"(?<!\\)\$(?!\$)", code))
        if dollars % 2 != 0:
            return False

        # Basic brace balance
        open_braces = code.count("{") - code.count("\\{")
        close_braces = code.count("}") - code.count("\\}")
        if open_braces != close_braces:
            return False

        return True

    def repair_common_issues(self, code: str) -> tuple[str, list[str]]:
        """
        Attempt to repair common issues.

        Args:
            code: LaTeX code

        Returns:
            Tuple of (repaired_code, list_of_repairs)
        """
        repairs: list[str] = []
        repaired = code

        # Fix multiple consecutive backslashes
        if "\\\\\\\\" in repaired:
            repaired = re.sub(r"\\\\\\\\+", r"\\\\", repaired)
            repairs.append("Fixed multiple consecutive line breaks")

        # Fix unescaped underscores outside math
        # (simplified - full implementation would need proper parsing)

        # Fix missing documentclass
        if "\\documentclass" not in repaired and "\\begin{document}" in repaired:
            repaired = "\\documentclass{article}\n" + repaired
            repairs.append("Added missing documentclass")

        # Fix missing begin/end document
        if "\\begin{document}" not in repaired and "\\section" in repaired:
            # Wrap in document environment
            repaired = "\\begin{document}\n" + repaired + "\n\\end{document}"
            repairs.append("Added document environment")

        return repaired, repairs
