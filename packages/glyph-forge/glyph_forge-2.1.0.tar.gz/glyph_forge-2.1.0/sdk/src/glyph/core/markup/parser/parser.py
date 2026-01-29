"""
Glyph Markup Parser
===================

Converts token stream into Abstract Syntax Tree (AST).

Parser Strategy:
- Maintains a block stack for nested $glyph blocks
- Splits text into paragraphs based on PARAGRAPH_BREAK tokens
- Creates runs within paragraphs (for v1, one run per paragraph)
"""

from typing import List, Optional, Union
from .ast import DocumentNode, BlockNode, ParagraphNode, RunNode, RowContainerNode, CellNode
from .tokenizer import Token, TokenType, tokenize
from ..language.errors import MarkupSyntaxError, UnbalancedBlockError


class Parser:
    """
    Stateful parser for Glyph markup.

    Consumes tokens and builds an AST with proper block nesting.
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.block_stack: List[Union[BlockNode, RowContainerNode, CellNode]] = []
        self.in_row_container = False  # Track if we're inside a row container

    def current_token(self) -> Optional[Token]:
        """Get current token without advancing."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def peek_token(self, offset: int = 1) -> Optional[Token]:
        """Peek ahead at a token."""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None

    def advance(self) -> Optional[Token]:
        """Advance to next token."""
        token = self.current_token()
        if token:
            self.pos += 1
        return token

    def expect_token(self, token_type: TokenType) -> Token:
        """
        Expect a specific token type and consume it.

        Raises:
            MarkupSyntaxError: If token type doesn't match
        """
        token = self.current_token()
        if not token or token.type != token_type:
            raise MarkupSyntaxError(
                f"Expected {token_type.name}, got {token.type.name if token else 'EOF'}",
                line=token.line if token else None,
                col=token.col if token else None,
            )
        return self.advance()

    def parse_classes(self, class_string: str) -> List[str]:
        """
        Parse a class string into individual utility classes.

        The tricky part: intelligently split "font-size-12-bold-color-FF0000"
        into ["font-size-12", "bold", "color-FF0000"]

        Strategy:
        - Split on dashes
        - Reassemble based on known patterns (parametric utilities)
        - Simple heuristic: if a segment is all uppercase or digits, it belongs to previous

        Args:
            class_string: The class string from $glyph-...

        Returns:
            List of individual utility class names
        """
        if not class_string:
            return []

        # Split on dashes
        parts = class_string.split("-")

        classes = []
        current_class = []

        for i, part in enumerate(parts):
            if not part:
                continue

            current_class.append(part)

            # Heuristics to determine if we should continue building or finalize:
            # 1. If next part is all digits/hex, it's likely a parameter value
            # 2. If next part is a known prefix (font, color, etc.), finalize current
            # 3. If current is a known standalone (bold, italic), finalize

            peek_next = parts[i + 1] if i + 1 < len(parts) else None

            # Known standalone flags
            STANDALONE_FLAGS = {
                "bold", "italic", "underline", "strike",
                "left", "right", "center", "justify",
                "portrait", "landscape",
            }

            # Known prefixes that start new utilities
            KNOWN_PREFIXES = {
                "font", "color", "highlight", "align", "indent",
                "section", "layout", "image", "list", "para", "char",
                "space", "line", "page", "no",
                "row", "cell", "gap",  # Row layout utilities
            }

            # Words that can be in the middle of a utility (don't trigger split)
            CONTINUATION_WORDS = {
                "first", "left", "right", "top", "bottom",
                "before", "after", "all", "name", "size",
                "cols", "widths", "width", "align", "valign", "pad",  # Row/cell parts
                "indent", "space", "keep", "border", "layout",
            }

            # Compound prefix patterns (two-word prefixes like "line-spacing")
            COMPOUND_PREFIXES = {
                ("line", "spacing"),
                ("page", "break"),
                ("column", "break"),
                ("first", "line"),
                # Image utilities
                ("image", "id"),
                ("image", "width"),
                ("image", "height"),
                ("image", "align"),
                ("image", "caption"),
                ("image", "path"),
                ("image", "alt"),
            }

            current_str = "-".join(current_class)

            # Check if current is a complete utility
            should_finalize = False

            # Check if we're building a compound prefix
            is_compound_prefix = False
            if current_class and peek_next:
                # Simple check: if current ends with word from compound and next is the second word
                last_word = current_class[-1] if current_class else ""
                for first_word, second_word in COMPOUND_PREFIXES:
                    if last_word == first_word and peek_next == second_word:
                        is_compound_prefix = True
                        break

            if peek_next is None:
                # Last part, finalize
                should_finalize = True
            elif current_str in STANDALONE_FLAGS:
                # Known standalone flag
                should_finalize = True
            elif is_compound_prefix:
                # Building a compound prefix like "line-spacing", don't finalize yet
                should_finalize = False
            elif peek_next in KNOWN_PREFIXES and peek_next not in CONTINUATION_WORDS:
                # Check if peek_next is the first word of a compound prefix
                # If so, finalize current before starting the compound
                is_starting_compound = any(peek_next == first for first, _ in COMPOUND_PREFIXES)
                if not is_starting_compound:
                    # Next part starts a new utility (and isn't a continuation word)
                    should_finalize = True
                else:
                    # Starting a compound, finalize current
                    should_finalize = True
            elif len(current_class) >= 3:
                # Have prefix + value + maybe unit (e.g., "indent-left-36")
                # Check if peek_next is a unit (pt, in, etc.) or another value
                if peek_next and (
                    peek_next in {"pt", "in", "cm", "mm"} or
                    peek_next.isdigit() or
                    peek_next in CONTINUATION_WORDS
                ):
                    # Continue building (it's a unit or continuation)
                    should_finalize = False
                elif peek_next in KNOWN_PREFIXES or peek_next in STANDALONE_FLAGS:
                    # Next part starts a new utility
                    should_finalize = True
            elif len(current_class) >= 2:
                # Have a prefix and at least one part
                # Check if peek_next looks like a new prefix
                if peek_next in KNOWN_PREFIXES and peek_next not in CONTINUATION_WORDS:
                    should_finalize = True
                elif peek_next in STANDALONE_FLAGS:
                    # Special case: don't finalize if we're building image-align-{direction}
                    # These directions (left, center, right) are in STANDALONE_FLAGS but
                    # should stay with image-align
                    if current_class[-1] == "align" and peek_next in {"left", "center", "right"}:
                        should_finalize = False
                    else:
                        should_finalize = True

            if should_finalize:
                classes.append(current_str)
                current_class = []

        # Don't forget remaining class
        if current_class:
            classes.append("-".join(current_class))

        return classes

    def is_row_container(self, classes: List[str]) -> bool:
        """
        Check if classes indicate this is a row container.

        A row container is identified by having 'row-cols-N' or starting with 'row-'
        utilities like 'row-widths-*', etc.

        Args:
            classes: List of utility class names

        Returns:
            True if this should be a row container
        """
        for cls in classes:
            # Check for row-cols-N (definitive indicator)
            if cls.startswith("row-cols-"):
                return True
            # Check for row-widths (also a strong indicator)
            if cls.startswith("row-widths-"):
                return True
            # Check for other row utilities
            if cls.startswith("row-align-") or cls.startswith("row-indent-"):
                return True
            if cls.startswith("row-width-") or cls.startswith("row-layout-"):
                return True
            if cls.startswith("row-space-") or cls.startswith("row-keep-"):
                return True
            if cls.startswith("row-border-"):
                return True
        return False

    def is_cell_block(self, classes: List[str]) -> bool:
        """
        Check if classes indicate this is a cell block.

        A cell block is identified by having utilities starting with 'cell-'
        or being an explicit 'cell' marker.

        Args:
            classes: List of utility class names

        Returns:
            True if this should be a cell
        """
        # Empty class list inside row container = implicit cell
        if not classes and self.in_row_container:
            return True

        for cls in classes:
            # Check for cell utilities
            if cls.startswith("cell-align-") or cls.startswith("cell-valign-"):
                return True
            if cls.startswith("cell-pad-") or cls.startswith("cell-width-"):
                return True
            if cls == "cell-nowrap":
                return True
            # Explicit cell marker
            if cls == "cell":
                return True
        return False

    def parse(self) -> DocumentNode:
        """
        Parse tokens into a DocumentNode.

        Returns:
            The root DocumentNode

        Raises:
            UnbalancedBlockError: If $glyph blocks are unbalanced
        """
        doc = DocumentNode()

        # Start with an implicit root block (for content outside $glyph blocks)
        current_block = BlockNode(line=0, col=0)
        current_paragraph_text = []

        while self.current_token() and self.current_token().type != TokenType.EOF:
            token = self.current_token()

            if token.type == TokenType.BLOCK_START:
                # Start a new block
                self.advance()

                # Finalize current paragraph if any
                if current_paragraph_text:
                    para_text = "".join(current_paragraph_text).strip()
                    if para_text:
                        para = ParagraphNode(
                            runs=[RunNode(text=para_text)],
                            line=token.line,
                            col=token.col,
                        )
                        # Add to current context (cell, block, or implicit block)
                        if self.block_stack:
                            last_block = self.block_stack[-1]
                            if isinstance(last_block, CellNode):
                                last_block.paragraphs.append(para)
                            elif isinstance(last_block, BlockNode):
                                last_block.paragraphs.append(para)
                        else:
                            current_block.paragraphs.append(para)
                    current_paragraph_text = []

                # ORDERING FIX: If starting a top-level glyph block, flush implicit content first
                if not self.block_stack and current_block.paragraphs:
                    doc.blocks.append(current_block)
                    current_block = BlockNode(line=token.line, col=token.col)

                # Parse class names from token value
                classes = self.parse_classes(token.value)

                # Determine what type of block this is
                if self.is_row_container(classes):
                    # This is a row container
                    new_block = RowContainerNode(
                        classes=classes,
                        line=token.line,
                        col=token.col,
                    )
                    self.block_stack.append(new_block)
                    self.in_row_container = True

                elif self.is_cell_block(classes) and self.in_row_container:
                    # This is a cell inside a row container
                    new_cell = CellNode(
                        classes=classes,
                        line=token.line,
                        col=token.col,
                    )
                    self.block_stack.append(new_cell)

                else:
                    # Regular block
                    new_block = BlockNode(
                        classes=classes,
                        line=token.line,
                        col=token.col,
                    )
                    self.block_stack.append(new_block)

            elif token.type == TokenType.BLOCK_END:
                # End current block
                self.advance()

                # Finalize current paragraph if any
                if current_paragraph_text:
                    para_text = "".join(current_paragraph_text).strip()
                    if para_text:
                        para = ParagraphNode(
                            runs=[RunNode(text=para_text)],
                        )
                        if self.block_stack:
                            last_block = self.block_stack[-1]
                            if isinstance(last_block, (CellNode, BlockNode)):
                                last_block.paragraphs.append(para)
                        else:
                            current_block.paragraphs.append(para)
                    current_paragraph_text = []

                # Pop block from stack
                if not self.block_stack:
                    raise UnbalancedBlockError(
                        "Found $glyph closing tag without matching opening tag",
                        line=token.line,
                    )

                closed_block = self.block_stack.pop()

                # Handle different block types
                if isinstance(closed_block, CellNode):
                    # Closing a cell - add it to parent row container
                    if self.block_stack and isinstance(self.block_stack[-1], RowContainerNode):
                        self.block_stack[-1].cells.append(closed_block)
                    else:
                        # Cell outside of row container - this is an error, but we'll be lenient
                        # Convert to regular block and add to document
                        # (This shouldn't happen with proper markup, but handle gracefully)
                        pass

                elif isinstance(closed_block, RowContainerNode):
                    # Closing a row container - add it to document
                    doc.blocks.append(closed_block)
                    # Reset row container flag
                    self.in_row_container = False
                    # Start a fresh implicit block for following plaintext
                    current_block = BlockNode(line=token.line, col=token.col)

                elif isinstance(closed_block, BlockNode):
                    # Regular block handling
                    if self.block_stack:
                        # Still inside a parent block - this would be nested blocks
                        # For v1, we'll treat nested blocks as sequential siblings
                        # (flatten them to avoid complexity)
                        pass  # We'll add to doc at the end
                    else:
                        # Block is complete, add to document
                        doc.blocks.append(closed_block)
                        # ORDERING FIX: Start a fresh implicit block for following plaintext
                        current_block = BlockNode(line=token.line, col=token.col)

            elif token.type == TokenType.PARAGRAPH_BREAK:
                # Paragraph boundary
                self.advance()

                # Finalize current paragraph
                if current_paragraph_text:
                    para_text = "".join(current_paragraph_text).strip()
                    if para_text:
                        para = ParagraphNode(
                            runs=[RunNode(text=para_text)],
                        )
                        if self.block_stack:
                            last_block = self.block_stack[-1]
                            # Add to cell or block (not row container)
                            if isinstance(last_block, (CellNode, BlockNode)):
                                last_block.paragraphs.append(para)
                            # If last block is a row container, we shouldn't have loose text
                            # (text should be inside cells), but handle gracefully by ignoring
                        else:
                            current_block.paragraphs.append(para)
                    current_paragraph_text = []

            elif token.type == TokenType.TEXT:
                # Accumulate text for current paragraph
                self.advance()
                current_paragraph_text.append(token.value)

            else:
                # Unknown token type, skip
                self.advance()

        # Finalize any remaining paragraph
        if current_paragraph_text:
            para_text = "".join(current_paragraph_text).strip()
            if para_text:
                para = ParagraphNode(
                    runs=[RunNode(text=para_text)],
                )
                if self.block_stack:
                    last_block = self.block_stack[-1]
                    if isinstance(last_block, (CellNode, BlockNode)):
                        last_block.paragraphs.append(para)
                else:
                    current_block.paragraphs.append(para)

        # Check for unbalanced blocks
        if self.block_stack:
            raise UnbalancedBlockError(
                f"Unclosed $glyph block(s): {len(self.block_stack)} block(s) not closed",
                line=self.block_stack[-1].line,
            )

        # Add implicit root block if it has content
        if current_block.paragraphs:
            doc.blocks.append(current_block)

        return doc


def parse_markup(text: str) -> DocumentNode:
    """
    Parse markup text into an AST.

    Args:
        text: Raw markup text with $glyph-... syntax

    Returns:
        DocumentNode representing the parsed structure

    Raises:
        MarkupSyntaxError: If syntax is invalid
        UnbalancedBlockError: If blocks are unbalanced

    Examples:
        >>> doc = parse_markup("$glyph-bold\\nHello world\\n$glyph")
        >>> doc.blocks[0].classes
        ['bold']
        >>> doc.blocks[0].paragraphs[0].text
        'Hello world'
    """
    tokens = tokenize(text)
    parser = Parser(tokens)
    return parser.parse()
