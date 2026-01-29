"""
Glyph Markup Rendering Engine
==============================

Converts AST to DOCX documents via python-docx or schema_runner.
"""

from .layout_resolver import (
    LayoutBundle,
    resolve_classes,
)
from .docx_renderer import (
    render_ast_to_docx,
    DocxRenderer,
)
from .integration import (
    render_markup_to_docx,
    render_markup_to_bytes,
)
from .schema_converter import (
    ast_to_schema,
    render_markup_via_schema,
    infer_type,
    convert_run_props,
    convert_para_props,
    convert_section_props,
)

__all__ = [
    # Layout resolution
    "LayoutBundle",
    "resolve_classes",
    # Direct rendering (python-docx)
    "render_ast_to_docx",
    "DocxRenderer",
    # Integration API (standalone)
    "render_markup_to_docx",
    "render_markup_to_bytes",
    # Schema runner integration
    "ast_to_schema",
    "render_markup_via_schema",
    "infer_type",
    "convert_run_props",
    "convert_para_props",
    "convert_section_props",
]
