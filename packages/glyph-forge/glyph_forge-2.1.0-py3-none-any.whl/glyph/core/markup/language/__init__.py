"""
Glyph Markup Language Definition
=================================

Core language specification and utility registry.
"""

from .registry import (
    UtilityDef,
    Scope,
    UTILITY_REGISTRY,
    get_utility,
    get_utilities_by_scope,
)
from .errors import (
    MarkupError,
    MarkupSyntaxError,
    UnknownUtilityError,
    ValidationError,
)
from .tokens import (
    parse_utility_name,
    encode_utility_name,
)
from .presets import (
    CORE_RUN_UTILITIES,
    CORE_PARAGRAPH_UTILITIES,
    CORE_SECTION_UTILITIES,
    CORE_BREAK_UTILITIES,
)

__all__ = [
    # Registry
    "UtilityDef",
    "Scope",
    "UTILITY_REGISTRY",
    "get_utility",
    "get_utilities_by_scope",
    # Errors
    "MarkupError",
    "MarkupSyntaxError",
    "UnknownUtilityError",
    "ValidationError",
    # Tokens
    "parse_utility_name",
    "encode_utility_name",
    # Presets
    "CORE_RUN_UTILITIES",
    "CORE_PARAGRAPH_UTILITIES",
    "CORE_SECTION_UTILITIES",
    "CORE_BREAK_UTILITIES",
]
