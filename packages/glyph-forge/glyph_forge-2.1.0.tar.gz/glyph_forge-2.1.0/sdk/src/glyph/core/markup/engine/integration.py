"""
Glyph Markup Integration Layer
===============================

Public API for markup rendering.

This is the orchestration layer that combines parsing, validation, and rendering.
"""

from typing import Optional, Union, Dict
from pathlib import Path
from dataclasses import dataclass, field
from io import BytesIO

from ..parser.parser import parse_markup as _parse_markup
from ..validator.validator import validate_ast
from .docx_renderer import render_ast_to_docx


@dataclass
class ImageRegistry:
    """
    Registry that maps image IDs to file paths for markup rendering.

    Used with the $glyph-image-id-{key} syntax to reference images.

    Examples:
        >>> registry = ImageRegistry()
        >>> registry.register("profile", "/path/to/profile.jpg")
        >>> registry.register("logo", "/path/to/logo.png")
        >>>
        >>> # Use in markup
        >>> markup = "$glyph-image-id-profile-image-width-2in\\n$glyph"
        >>> render_markup_to_docx(markup, image_registry=registry)
    """
    images: Dict[str, str] = field(default_factory=dict)

    def register(self, image_id: str, path: str) -> None:
        """
        Register an image with the given ID.

        Args:
            image_id: Unique identifier for the image (used in markup as image-id-{id})
            path: File path to the image
        """
        self.images[image_id] = str(path)

    def get_path(self, image_id: str) -> Optional[str]:
        """
        Get the file path for an image ID.

        Args:
            image_id: The image identifier

        Returns:
            File path if found, None otherwise
        """
        return self.images.get(image_id)

    def __contains__(self, image_id: str) -> bool:
        """Check if an image ID is registered."""
        return image_id in self.images

    def __getitem__(self, image_id: str) -> str:
        """Get image path by ID (raises KeyError if not found)."""
        return self.images[image_id]


def render_markup_to_docx(
    markup_text: str,
    template_path: Optional[Union[str, Path]] = None,
    output_path: Optional[Union[str, Path]] = None,
    validate: bool = True,
    image_registry: Optional[ImageRegistry] = None,
) -> Path:
    """
    Render markup text to a DOCX file.

    Args:
        markup_text: Raw markup text with $glyph-... syntax
        template_path: Optional template DOCX file path
        output_path: Output file path (default: "glyph_output.docx")
        validate: Whether to validate markup before rendering (default: True)
        image_registry: Optional ImageRegistry mapping image IDs to file paths

    Returns:
        Path to the saved DOCX file

    Raises:
        MarkupSyntaxError: If markup syntax is invalid
        UnbalancedBlockError: If blocks are unbalanced
        ValidationError: If validation fails and validate=True

    Examples:
        >>> markup = '''
        ... $glyph-font-size-14-bold-align-center
        ... Hello World
        ... $glyph
        ...
        ... This is body text.
        ... '''
        >>> output = render_markup_to_docx(markup, output_path="hello.docx")
        >>> print(output)
        hello.docx

        # With images:
        >>> registry = ImageRegistry()
        >>> registry.register("logo", "/path/to/logo.png")
        >>> markup = "$glyph-image-id-logo-image-width-2in\\n$glyph"
        >>> render_markup_to_docx(markup, image_registry=registry)
    """
    # Parse markup to AST
    ast = _parse_markup(markup_text)

    # Validate if requested
    if validate:
        diagnostics = validate_ast(ast)
        errors = [d for d in diagnostics if d.level == "error"]
        if errors:
            from ..language.errors import ValidationError

            error_msg = "\n".join(str(d) for d in errors)
            raise ValidationError(f"Markup validation failed:\n{error_msg}")

    # Render to DOCX
    doc = render_ast_to_docx(ast, template_path, image_registry=image_registry)

    # Save to file
    if output_path is None:
        output_path = Path("glyph_output.docx")
    else:
        output_path = Path(output_path)

    doc.save(str(output_path))
    return output_path


def render_markup_to_bytes(
    markup_text: str,
    template_path: Optional[Union[str, Path]] = None,
    validate: bool = True,
    image_registry: Optional[ImageRegistry] = None,
) -> bytes:
    """
    Render markup text to DOCX bytes (in-memory).

    Args:
        markup_text: Raw markup text with $glyph-... syntax
        template_path: Optional template DOCX file path
        validate: Whether to validate markup before rendering (default: True)
        image_registry: Optional ImageRegistry mapping image IDs to file paths

    Returns:
        DOCX file as bytes

    Raises:
        MarkupSyntaxError: If markup syntax is invalid
        UnbalancedBlockError: If blocks are unbalanced
        ValidationError: If validation fails and validate=True

    Examples:
        >>> markup = "$glyph-bold\\nHello\\n$glyph"
        >>> docx_bytes = render_markup_to_bytes(markup)
        >>> len(docx_bytes) > 0
        True
    """
    # Parse markup to AST
    ast = _parse_markup(markup_text)

    # Validate if requested
    if validate:
        diagnostics = validate_ast(ast)
        errors = [d for d in diagnostics if d.level == "error"]
        if errors:
            from ..language.errors import ValidationError

            error_msg = "\n".join(str(d) for d in errors)
            raise ValidationError(f"Markup validation failed:\n{error_msg}")

    # Render to DOCX
    doc = render_ast_to_docx(ast, template_path, image_registry=image_registry)

    # Save to BytesIO
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def parse_markup(markup_text: str):
    """
    Parse markup text to AST.

    This is a convenience re-export for users who want to inspect the AST.

    Args:
        markup_text: Raw markup text

    Returns:
        DocumentNode AST

    Examples:
        >>> ast = parse_markup("$glyph-bold\\nHello\\n$glyph")
        >>> ast.blocks[0].classes
        ['bold']
    """
    return _parse_markup(markup_text)


def validate_markup(markup_text: str, strict: bool = False):
    """
    Validate markup text.

    Args:
        markup_text: Raw markup text
        strict: If True, return only errors; if False, include warnings

    Returns:
        List of diagnostic messages

    Examples:
        >>> diagnostics = validate_markup("$glyph-bold\\nHello\\n$glyph")
        >>> len(diagnostics)
        0
    """
    ast = _parse_markup(markup_text)
    diagnostics = validate_ast(ast, strict=strict)
    return diagnostics
