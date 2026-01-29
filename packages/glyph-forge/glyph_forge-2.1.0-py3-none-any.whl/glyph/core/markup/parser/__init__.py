"""
Glyph Markup Parser
===================

Converts plaintext with $glyph markup into an Abstract Syntax Tree (AST).

The parser is pure Python with no Word/DOCX dependencies.
"""

from .ast import (
    DocumentNode,
    BlockNode,
    ParagraphNode,
    RunNode,
)
from .tokenizer import (
    Token,
    TokenType,
    tokenize,
)
from .parser import (
    parse_markup,
    Parser,
)

__all__ = [
    # AST
    "DocumentNode",
    "BlockNode",
    "ParagraphNode",
    "RunNode",
    # Tokenizer
    "Token",
    "TokenType",
    "tokenize",
    # Parser
    "parse_markup",
    "Parser",
]
