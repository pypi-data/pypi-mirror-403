"""
Glyph Markup Abstract Syntax Tree (AST)
========================================

Node types for representing parsed markup.

Hierarchy:
    DocumentNode
    └── BlockNode[] | RowContainerNode[]
        ├── BlockNode
        │   └── ParagraphNode[]
        │       └── RunNode[]
        └── RowContainerNode
            └── CellNode[]
                └── ParagraphNode[]
                    └── RunNode[]
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union


@dataclass
class RunNode:
    """
    A text run with inline formatting.

    Represents a span of text with uniform styling (run-level utilities).

    Attributes:
        text: The text content
        classes: List of utility class names (e.g., ["bold", "font-size-12"])
        line: Source line number (for error reporting)
        col: Source column number (for error reporting)
    """

    text: str
    classes: List[str] = field(default_factory=list)
    line: Optional[int] = None
    col: Optional[int] = None

    def __repr__(self):
        classes_str = f" classes={self.classes}" if self.classes else ""
        text_preview = self.text[:30] + "..." if len(self.text) > 30 else self.text
        return f"RunNode({text_preview!r}{classes_str})"


@dataclass
class ParagraphNode:
    """
    A paragraph with optional formatting.

    Represents a block of text that forms a paragraph (paragraph-level utilities).

    Attributes:
        runs: List of text runs within this paragraph
        classes: List of utility class names (e.g., ["align-center", "space-after-12pt"])
        line: Source line number
        col: Source column number
    """

    runs: List[RunNode] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    line: Optional[int] = None
    col: Optional[int] = None

    @property
    def text(self) -> str:
        """Get combined text from all runs."""
        return "".join(run.text for run in self.runs)

    def __repr__(self):
        classes_str = f" classes={self.classes}" if self.classes else ""
        text_preview = self.text[:30] + "..." if len(self.text) > 30 else self.text
        return f"ParagraphNode({text_preview!r}, {len(self.runs)} runs{classes_str})"


@dataclass
class CellNode:
    """
    A cell within a row layout container.

    Represents a $glyph-cell block with cell-level utilities.

    Attributes:
        classes: List of utility class names (e.g., ["cell-align-right", "cell-valign-top"])
        paragraphs: List of paragraphs within this cell
        line: Source line number where cell starts
        col: Source column number
    """

    classes: List[str] = field(default_factory=list)
    paragraphs: List[ParagraphNode] = field(default_factory=list)
    line: Optional[int] = None
    col: Optional[int] = None

    @property
    def text(self) -> str:
        """Get combined text from all paragraphs."""
        return "\n".join(p.text for p in self.paragraphs)

    def __repr__(self):
        classes_str = f" classes={self.classes}" if self.classes else ""
        text_preview = self.text[:30] + "..." if len(self.text) > 30 else self.text
        return f"CellNode({text_preview!r}, {len(self.paragraphs)} paragraphs{classes_str})"


@dataclass
class RowContainerNode:
    """
    A row layout container with N cells.

    Represents a $glyph-row-... $glyph block with row-level utilities.
    This is a layout primitive for aligned content (e.g., two-column resume lines).

    Attributes:
        classes: List of utility class names (e.g., ["row-cols-2", "row-widths-70-30"])
        cells: List of cells within this row
        line: Source line number where row starts
        col: Source column number
    """

    classes: List[str] = field(default_factory=list)
    cells: List[CellNode] = field(default_factory=list)
    line: Optional[int] = None
    col: Optional[int] = None

    @property
    def text(self) -> str:
        """Get combined text from all cells."""
        return " | ".join(c.text for c in self.cells)

    def __repr__(self):
        classes_str = f" classes={self.classes}" if self.classes else ""
        return f"RowContainerNode({len(self.cells)} cells{classes_str})"


@dataclass
class BlockNode:
    """
    A block of content with section/layout styling.

    Represents a $glyph-... $glyph block with section-level utilities.

    Attributes:
        classes: List of utility class names (e.g., ["layout-col-2", "section-margin-all-1in"])
        paragraphs: List of paragraphs within this block
        line: Source line number where block starts
        col: Source column number
    """

    classes: List[str] = field(default_factory=list)
    paragraphs: List[ParagraphNode] = field(default_factory=list)
    line: Optional[int] = None
    col: Optional[int] = None

    @property
    def text(self) -> str:
        """Get combined text from all paragraphs."""
        return "\n".join(p.text for p in self.paragraphs)

    def __repr__(self):
        classes_str = f" classes={self.classes}" if self.classes else ""
        return f"BlockNode({len(self.paragraphs)} paragraphs{classes_str})"


@dataclass
class DocumentNode:
    """
    The root document node.

    Represents the entire document as a sequence of blocks (regular blocks or row containers).

    Attributes:
        blocks: List of blocks in the document (BlockNode or RowContainerNode)
    """

    blocks: List[Union[BlockNode, RowContainerNode]] = field(default_factory=list)

    @property
    def text(self) -> str:
        """Get combined text from all blocks."""
        return "\n\n".join(b.text for b in self.blocks)

    def __repr__(self):
        return f"DocumentNode({len(self.blocks)} blocks)"
