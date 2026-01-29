"""
glyph SDK
============

A toolkit for analyzing, mapping, and generating schemas from DOCX and plaintext sources.
Provides a unified API around:
- Analysis (detectors, forms, matchers)
- Schema building (GlyphSchemaBuilder, SchemaGenerator)
- Markup (Tailwind-inspired plaintext markup language)
- Utilities (mappers, intake, workspace)
"""

from importlib.metadata import version, PackageNotFoundError

__all__ = [
    "__version__",
    "GlyphSchemaBuilder",
    "SchemaGenerator",
    "build_schema",
    # Markup API (direct)
    "render_markup_to_docx",
    "render_markup_to_bytes",
    # Markup API (schema integration)
    "render_markup_via_schema",
    "ast_to_schema",
    # Markup parsing
    "parse_markup",
    "validate_markup",
]

# ----------------------------------------------------------------------
# Package version
# ----------------------------------------------------------------------
try:
    __version__ = version("glyph")
except PackageNotFoundError:
    __version__ = "0.0.0"

# ----------------------------------------------------------------------
# Public imports
# ----------------------------------------------------------------------
from glyph.core.schema.build_schema import GlyphSchemaBuilder
from glyph.core.schema.schema_generator import SchemaGenerator
from glyph.runner import build_schema

# Markup Language API
from glyph.markup import (
    render_markup_to_docx,
    render_markup_to_bytes,
    render_markup_via_schema,
    ast_to_schema,
    parse_markup,
    validate_markup,
)
