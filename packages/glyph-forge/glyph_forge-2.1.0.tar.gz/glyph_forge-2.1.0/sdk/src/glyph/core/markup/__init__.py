"""
Glyph Markup Language
=====================

A plaintext markup language for LLM-driven document generation.

Syntax: $glyph-<utility-classes> ... $glyph

Example:
    $glyph-font-size-16-bold-color-000000
    This is bold 16pt black text.
    $glyph

Public API:
    - render_markup_to_docx: Render markup text to a DOCX file
    - render_markup_to_bytes: Render markup text to bytes
    - parse_markup: Parse markup text to AST
    - validate_markup: Validate markup text
"""

__all__ = [
    "render_markup_to_docx",
    "render_markup_to_bytes",
    "parse_markup",
    "validate_markup",
]
