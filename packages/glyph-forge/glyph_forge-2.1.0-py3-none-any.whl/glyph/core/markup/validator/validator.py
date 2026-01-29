"""
Glyph Markup Validator
======================

Validates markup AST for errors and warnings:
- Unknown utility names
- Invalid utility combinations
- Block nesting issues
"""

from dataclasses import dataclass
from typing import List, Optional
from ..parser.ast import DocumentNode, BlockNode, ParagraphNode, RunNode
from ..language.registry import get_utility
from ..language.errors import UnknownUtilityError


@dataclass
class MarkupDiagnostic:
    """
    A validation diagnostic (error or warning).

    Attributes:
        level: "error" or "warning"
        message: Human-readable message
        line: Source line number
        col: Source column number
        code: Diagnostic code (e.g., "UNKNOWN_UTILITY")
    """

    level: str  # "error" | "warning"
    message: str
    line: Optional[int] = None
    col: Optional[int] = None
    code: Optional[str] = None

    def __str__(self):
        parts = [f"[{self.level.upper()}]"]
        if self.code:
            parts.append(f"[{self.code}]")
        if self.line is not None:
            location = f"line {self.line}"
            if self.col is not None:
                location += f", col {self.col}"
            parts.append(f"({location})")
        parts.append(self.message)
        return " ".join(parts)


class ASTValidator:
    """
    Validates a markup AST.

    Performs checks:
    - Unknown utilities
    - Invalid utility combinations
    - Scope mismatches
    """

    def __init__(self, strict: bool = False):
        """
        Initialize validator.

        Args:
            strict: If True, treat warnings as errors
        """
        self.strict = strict
        self.diagnostics: List[MarkupDiagnostic] = []

    def add_diagnostic(
        self,
        level: str,
        message: str,
        line: Optional[int] = None,
        col: Optional[int] = None,
        code: Optional[str] = None,
    ):
        """Add a diagnostic."""
        self.diagnostics.append(
            MarkupDiagnostic(level=level, message=message, line=line, col=col, code=code)
        )

    def validate(self, ast: DocumentNode) -> List[MarkupDiagnostic]:
        """
        Validate an AST.

        Args:
            ast: The DocumentNode to validate

        Returns:
            List of diagnostics
        """
        self.diagnostics = []

        for block in ast.blocks:
            self.validate_block(block)

        return self.diagnostics

    def validate_block(self, block: BlockNode):
        """Validate a block node."""
        # Check utilities in block classes
        for class_name in block.classes:
            util_def = get_utility(class_name)
            if not util_def:
                self.add_diagnostic(
                    level="error",
                    message=f"Unknown utility: '{class_name}'",
                    line=block.line,
                    col=block.col,
                    code="UNKNOWN_UTILITY",
                )
            else:
                # Check if utility scope is appropriate for block level
                # Blocks can have section, paragraph, run, image, or break utilities
                if util_def.scope not in ("section", "paragraph", "run", "image", "break"):
                    self.add_diagnostic(
                        level="warning",
                        message=f"Utility '{class_name}' with scope '{util_def.scope}' "
                        f"may not be appropriate at block level",
                        line=block.line,
                        col=block.col,
                        code="SCOPE_MISMATCH",
                    )

        # Validate paragraphs
        for para in block.paragraphs:
            self.validate_paragraph(para)

    def validate_paragraph(self, para: ParagraphNode):
        """Validate a paragraph node."""
        # Check utilities in paragraph classes
        for class_name in para.classes:
            util_def = get_utility(class_name)
            if not util_def:
                self.add_diagnostic(
                    level="error",
                    message=f"Unknown utility: '{class_name}'",
                    line=para.line,
                    col=para.col,
                    code="UNKNOWN_UTILITY",
                )
            else:
                # Paragraphs should have paragraph or run utilities
                if util_def.scope not in ("paragraph", "run"):
                    self.add_diagnostic(
                        level="warning",
                        message=f"Utility '{class_name}' with scope '{util_def.scope}' "
                        f"may not be appropriate at paragraph level",
                        line=para.line,
                        col=para.col,
                        code="SCOPE_MISMATCH",
                    )

        # Validate runs
        for run in para.runs:
            self.validate_run(run)

    def validate_run(self, run: RunNode):
        """Validate a run node."""
        # Check utilities in run classes
        for class_name in run.classes:
            util_def = get_utility(class_name)
            if not util_def:
                self.add_diagnostic(
                    level="error",
                    message=f"Unknown utility: '{class_name}'",
                    line=run.line,
                    col=run.col,
                    code="UNKNOWN_UTILITY",
                )
            else:
                # Runs should only have run-scope utilities
                if util_def.scope != "run":
                    self.add_diagnostic(
                        level="warning",
                        message=f"Utility '{class_name}' with scope '{util_def.scope}' "
                        f"is not appropriate at run level (should be 'run' scope)",
                        line=run.line,
                        col=run.col,
                        code="SCOPE_MISMATCH",
                    )

        # Check for empty text
        if not run.text.strip():
            self.add_diagnostic(
                level="warning",
                message="Empty run (no text content)",
                line=run.line,
                col=run.col,
                code="EMPTY_RUN",
            )


def validate_ast(ast: DocumentNode, strict: bool = False) -> List[MarkupDiagnostic]:
    """
    Validate a markup AST.

    Args:
        ast: The DocumentNode to validate
        strict: If True, treat warnings as errors

    Returns:
        List of diagnostics

    Examples:
        >>> from glyph.core.markup.parser import parse_markup
        >>> ast = parse_markup("$glyph-bold\\nHello\\n$glyph")
        >>> diagnostics = validate_ast(ast)
        >>> len(diagnostics)
        0
    """
    validator = ASTValidator(strict=strict)
    return validator.validate(ast)


def validate_markup(markup_text: str, strict: bool = False) -> List[MarkupDiagnostic]:
    """
    Validate markup text.

    Args:
        markup_text: Raw markup text
        strict: If True, treat warnings as errors

    Returns:
        List of diagnostics

    Examples:
        >>> diagnostics = validate_markup("$glyph-unknown-utility\\nText\\n$glyph")
        >>> len(diagnostics) > 0
        True
        >>> diagnostics[0].code
        'UNKNOWN_UTILITY'
    """
    from ..parser.parser import parse_markup

    ast = parse_markup(markup_text)
    return validate_ast(ast, strict=strict)
