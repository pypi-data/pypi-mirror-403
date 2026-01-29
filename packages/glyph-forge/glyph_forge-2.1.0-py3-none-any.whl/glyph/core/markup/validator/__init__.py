"""
Glyph Markup Validator
======================

Fast validation checks for markup AST.
"""

from .validator import (
    MarkupDiagnostic,
    validate_ast,
    validate_markup,
)

__all__ = [
    "MarkupDiagnostic",
    "validate_ast",
    "validate_markup",
]
