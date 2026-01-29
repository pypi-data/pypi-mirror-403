"""
glyph.core.config
--------------------
Configuration utilities for DOCX parsing and reconstruction.

Exports:
    - SchemaGenerator : assemble JSON configs from parsed DOCX content
    - SchemaSaver  : write configs to disk
    - DocxStylesMapper: collect style definitions from unzipped DOCX
    - GlyphSchemaBuilder: parse DOCX XML into structured configs
    - compress_schema: compress schemas by deduplicating pattern descriptors
    - get_compression_stats: get statistics about schema compression
    - PlaintextGenerator: generate Glyph markup from schemas
    - generate_plaintext_from_schema: convenience function for plaintext generation
"""

from .schema_generator import SchemaGenerator
from .utils.schema_saver import SchemaSaver
from .utils.mappers.docx_styles_mapper import DocxStylesMapper
from .build_schema import GlyphSchemaBuilder
from .compress_schema import compress_schema, get_compression_stats
from .plaintext_generator import PlaintextGenerator, generate_plaintext_from_schema

__all__ = [
    "SchemaGenerator",
    "SchemaSaver",
    "DocxStylesMapper",
    "GlyphSchemaBuilder",
    "compress_schema",
    "get_compression_stats",
    "PlaintextGenerator",
    "generate_plaintext_from_schema",
]
