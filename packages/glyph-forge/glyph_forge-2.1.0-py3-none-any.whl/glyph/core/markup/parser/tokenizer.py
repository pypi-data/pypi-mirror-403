"""
Glyph Markup Tokenizer
======================

Scans raw text for $glyph control sequences and text segments.

Token types:
- BLOCK_START: $glyph-{classes}
- BLOCK_END: $glyph
- TEXT: Plain text between tokens
- PARAGRAPH_BREAK: Empty line (double newline)
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional
import re


class TokenType(Enum):
    """Token types for markup scanning."""

    BLOCK_START = auto()  # $glyph-...
    BLOCK_END = auto()    # $glyph
    TEXT = auto()         # Plain text
    PARAGRAPH_BREAK = auto()  # Empty line
    EOF = auto()          # End of file


@dataclass
class Token:
    """
    A single token from the markup stream.

    Attributes:
        type: The token type
        value: Token value (e.g., class names for BLOCK_START, text for TEXT)
        line: Source line number
        col: Source column number
    """

    type: TokenType
    value: str = ""
    line: int = 0
    col: int = 0

    def __repr__(self):
        value_str = f" {self.value!r}" if self.value else ""
        return f"Token({self.type.name}{value_str} @{self.line}:{self.col})"


class Tokenizer:
    """
    Stateful tokenizer for Glyph markup.

    Scans text character by character, identifying:
    - $glyph-... (block start with classes)
    - $glyph (block end)
    - Text segments
    - Paragraph breaks (blank lines)
    """

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    def current_char(self) -> Optional[str]:
        """Get current character without advancing."""
        if self.pos < len(self.text):
            return self.text[self.pos]
        return None

    def peek_char(self, offset: int = 1) -> Optional[str]:
        """Peek ahead at a character."""
        pos = self.pos + offset
        if pos < len(self.text):
            return self.text[pos]
        return None

    def advance(self) -> Optional[str]:
        """Advance to next character and update line/col."""
        if self.pos < len(self.text):
            char = self.text[self.pos]
            self.pos += 1

            if char == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1

            return char
        return None

    def peek_string(self, s: str) -> bool:
        """Check if the next characters match a string."""
        end_pos = self.pos + len(s)
        if end_pos <= len(self.text):
            return self.text[self.pos:end_pos] == s
        return False

    def consume_string(self, s: str) -> bool:
        """Consume a string if it matches, otherwise return False."""
        if self.peek_string(s):
            for _ in s:
                self.advance()
            return True
        return False

    def scan_glyph_token(self) -> Optional[Token]:
        """
        Scan a $glyph token (either block start or block end).

        Returns:
            Token if $glyph found, None otherwise
        """
        if not self.peek_string("$glyph"):
            return None

        start_line = self.line
        start_col = self.col

        # Consume "$glyph"
        self.consume_string("$glyph")

        # Check if it's a block start (has a dash after)
        if self.current_char() == "-":
            self.advance()  # consume the dash

            # Scan class string until newline or end of text
            class_string = ""

            while True:
                char = self.current_char()

                if char is None or char == "\n":
                    # End of token
                    break

                # Accumulate all characters (including dashes)
                class_string += char
                self.advance()

            return Token(
                type=TokenType.BLOCK_START,
                value=class_string.strip(),
                line=start_line,
                col=start_col,
            )
        else:
            # Block end (just "$glyph")
            return Token(
                type=TokenType.BLOCK_END,
                line=start_line,
                col=start_col,
            )

    def scan_paragraph_break(self) -> Optional[Token]:
        """
        Scan for paragraph break (blank line).

        Returns:
            Token if blank line found, None otherwise
        """
        # Look for \n\n or \r\n\r\n
        if self.peek_string("\n\n") or self.peek_string("\r\n\r\n"):
            start_line = self.line
            start_col = self.col

            # Consume all consecutive newlines
            while self.current_char() in ("\n", "\r"):
                self.advance()

            return Token(
                type=TokenType.PARAGRAPH_BREAK,
                line=start_line,
                col=start_col,
            )
        return None

    def scan_text(self) -> Optional[Token]:
        """
        Scan plain text until we hit a $glyph token or paragraph break.

        Returns:
            Token containing text
        """
        start_line = self.line
        start_col = self.col
        text = ""

        while True:
            # Check for $glyph token
            if self.peek_string("$glyph"):
                break

            # Check for paragraph break
            if self.peek_string("\n\n"):
                break

            char = self.current_char()
            if char is None:
                break

            text += char
            self.advance()

        if text:
            return Token(
                type=TokenType.TEXT,
                value=text.strip(),  # Strip both leading and trailing whitespace
                line=start_line,
                col=start_col,
            )
        return None

    def tokenize(self) -> List[Token]:
        """
        Tokenize the entire text.

        Returns:
            List of tokens
        """
        tokens = []

        while self.pos < len(self.text):
            # Try to scan $glyph token
            token = self.scan_glyph_token()
            if token:
                tokens.append(token)
                continue

            # Try to scan paragraph break
            token = self.scan_paragraph_break()
            if token:
                tokens.append(token)
                continue

            # Scan text
            token = self.scan_text()
            if token:
                tokens.append(token)
                continue

            # If nothing matched, advance to avoid infinite loop
            # This shouldn't happen, but it's a safety net
            self.advance()

        # Add EOF token
        tokens.append(Token(type=TokenType.EOF, line=self.line, col=self.col))
        return tokens


def tokenize(text: str) -> List[Token]:
    """
    Tokenize markup text.

    Args:
        text: Raw markup text

    Returns:
        List of tokens

    Examples:
        >>> tokens = tokenize("$glyph-bold\\nHello\\n$glyph")
        >>> [t.type for t in tokens]
        [TokenType.BLOCK_START, TokenType.TEXT, TokenType.BLOCK_END, TokenType.EOF]
    """
    tokenizer = Tokenizer(text)
    return tokenizer.tokenize()
