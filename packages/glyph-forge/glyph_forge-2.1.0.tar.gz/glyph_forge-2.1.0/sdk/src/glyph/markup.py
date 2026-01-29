"""
Glyph Markup Language - Public API
===================================

A plaintext markup language for LLM-driven document generation.

Quick Start
-----------

Generate a DOCX from markup text:

    >>> from glyph.markup import render_markup_to_docx
    >>>
    >>> markup = '''
    ... $glyph-font-size-14-bold-align-center
    ... Hello World
    ... $glyph
    ...
    ... This is normal body text.
    ... '''
    >>>
    >>> render_markup_to_docx(markup, output_path="hello.docx")

Syntax
------

The markup language uses `$glyph-<utilities>` blocks:

    $glyph-<utility-1>-<utility-2>-...
    Content goes here
    $glyph

Available utility classes:
- Run level: bold, italic, font-size-{N}, color-{RRGGBB}
- Paragraph level: align-{left|center|right}, indent-left-{N}pt
- Section level: layout-col-{N}, section-margin-all-{N}in

See documentation for complete utility reference.

API Functions
-------------

Direct Rendering (python-docx):
- render_markup_to_docx: Render markup to DOCX file
- render_markup_to_bytes: Render markup to bytes (in-memory)

Schema Runner Integration (uses existing writers):
- render_markup_via_schema: Render via schema_runner for better template support
- ast_to_schema: Convert markup AST to schema format

Parsing & Validation:
- parse_markup: Parse markup to AST
- validate_markup: Validate markup for errors
"""

from .core.markup.engine.integration import (
    render_markup_to_docx,
    render_markup_to_bytes,
    parse_markup,
    validate_markup,
)
from .core.markup.engine.schema_converter import (
    render_markup_via_schema,
    ast_to_schema,
)

__all__ = [
    # Direct rendering
    "render_markup_to_docx",
    "render_markup_to_bytes",
    # Schema runner integration
    "render_markup_via_schema",
    "ast_to_schema",
    # Parsing & validation
    "parse_markup",
    "validate_markup",
]
