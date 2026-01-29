"""
Glyph Markup Error Types
========================

Exception hierarchy for markup parsing and validation.
"""

from typing import Optional


class MarkupError(Exception):
    """Base exception for all markup errors."""

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        col: Optional[int] = None,
        code: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col
        self.code = code

    def __str__(self):
        parts = [self.message]
        if self.line is not None:
            parts.append(f"(line {self.line}")
            if self.col is not None:
                parts[-1] += f", col {self.col}"
            parts[-1] += ")"
        if self.code:
            parts.append(f"[{self.code}]")
        return " ".join(parts)


class MarkupSyntaxError(MarkupError):
    """Raised when markup syntax is invalid."""

    def __init__(self, message: str, line: Optional[int] = None, col: Optional[int] = None):
        super().__init__(message, line, col, "SYNTAX_ERROR")


class UnknownUtilityError(MarkupError):
    """Raised when an unknown utility class is encountered."""

    def __init__(self, utility_name: str, line: Optional[int] = None, col: Optional[int] = None):
        message = f"Unknown utility: '{utility_name}'"
        super().__init__(message, line, col, "UNKNOWN_UTILITY")
        self.utility_name = utility_name


class ValidationError(MarkupError):
    """Raised when markup validation fails."""

    def __init__(self, message: str, line: Optional[int] = None, col: Optional[int] = None):
        super().__init__(message, line, col, "VALIDATION_ERROR")


class UnbalancedBlockError(MarkupSyntaxError):
    """Raised when $glyph blocks are not properly balanced."""

    def __init__(self, message: str = "Unbalanced $glyph blocks", line: Optional[int] = None):
        super().__init__(message, line)
