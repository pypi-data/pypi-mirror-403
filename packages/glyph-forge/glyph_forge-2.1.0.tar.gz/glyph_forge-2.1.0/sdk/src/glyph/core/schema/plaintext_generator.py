# glyph/core/schema/plaintext_generator.py
"""
Plaintext Generator
===================

Generates Glyph markup plaintext from a schema.

This module converts pattern descriptors back into Glyph markup format,
including inline image references using $glyph-image-id-{id} syntax.
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional
from pathlib import Path
import os


class PlaintextGenerator:
    """
    Generate Glyph markup from a schema.

    Takes pattern descriptors and image metadata from a schema and produces
    a plaintext file with Glyph markup syntax for later DOCX rendering.
    """

    def __init__(self, schema: Dict[str, Any]):
        """
        Initialize the generator with a schema.

        Args:
            schema: The Glyph schema containing pattern_descriptors and images
        """
        self.schema = schema
        self.pattern_descriptors = schema.get("pattern_descriptors", [])
        self.images = schema.get("images", [])
        self.global_defaults = schema.get("global_defaults", {})

        # Build lookup of images by paragraph index for insertion
        self._images_by_para: Dict[int, List[Dict[str, Any]]] = {}
        for img in self.images:
            para_idx = img.get("paragraph_index", -1)
            if para_idx >= 0:
                if para_idx not in self._images_by_para:
                    self._images_by_para[para_idx] = []
                self._images_by_para[para_idx].append(img)

    def generate(self) -> str:
        """
        Generate Glyph markup from the schema.

        Returns:
            String containing the complete Glyph markup
        """
        lines: List[str] = []
        para_idx = 0

        for descriptor in self.pattern_descriptors:
            # Check for images before this paragraph
            if para_idx in self._images_by_para:
                for img in self._images_by_para[para_idx]:
                    lines.append(self._generate_image_block(img))
                    lines.append("")  # blank line after image

            # Generate paragraph block
            para_markup = self._generate_paragraph_block(descriptor)
            if para_markup:
                lines.append(para_markup)
                lines.append("")  # blank line between paragraphs

            para_idx += 1

        # Check for any trailing images (after all paragraphs)
        for idx in sorted(self._images_by_para.keys()):
            if idx >= para_idx:
                for img in self._images_by_para[idx]:
                    lines.append(self._generate_image_block(img))
                    lines.append("")

        return "\n".join(lines)

    def _generate_paragraph_block(self, descriptor: Dict[str, Any]) -> str:
        """
        Generate a Glyph block for a paragraph descriptor.

        Args:
            descriptor: The pattern descriptor dict

        Returns:
            Glyph markup string for this paragraph
        """
        text = descriptor.get("features", {}).get("text", "")
        if not text:
            return ""

        # Build utility classes from descriptor
        classes = self._build_utility_classes(descriptor)

        # Format as $glyph-classes\ntext\n$glyph
        if classes:
            class_str = "-".join(classes)
            return f"$glyph-{class_str}\n{text}\n$glyph"
        else:
            # Plain text without formatting
            return text

    def _build_utility_classes(self, descriptor: Dict[str, Any]) -> List[str]:
        """
        Build Glyph utility classes from a pattern descriptor.

        Converts pattern type and style info into Glyph utility class names.

        Args:
            descriptor: The pattern descriptor

        Returns:
            List of utility class names
        """
        classes: List[str] = []
        dtype = descriptor.get("type", "")
        style = descriptor.get("style", {})

        # Map pattern type to heading utilities
        heading_map = {
            "H-SHORT": "h-short",
            "H-LONG": "h-long",
            "H-SECTION-N": "h-section",
            "H-CONTENTS": "h-contents",
            "H-SUBTITLE": "h-subtitle",
        }

        if dtype in heading_map:
            classes.append(heading_map[dtype])

        # Extract run-level formatting from style
        run_props = style.get("run_props", {})
        if run_props.get("bold"):
            classes.append("bold")
        if run_props.get("italic"):
            classes.append("italic")
        if run_props.get("underline"):
            classes.append("underline")

        # Extract paragraph alignment
        para_props = style.get("paragraph_props", {})
        alignment = para_props.get("alignment", "").lower()
        if alignment in ("center", "right", "justify"):
            classes.append(f"align-{alignment}")

        # Font size
        font_size = run_props.get("font_size")
        if font_size:
            classes.append(f"font-size-{font_size}")

        # Font color
        color = run_props.get("color")
        if color:
            classes.append(f"color-{color}")

        return classes

    def _generate_image_block(self, image: Dict[str, Any]) -> str:
        """
        Generate a Glyph image block.

        Args:
            image: Image metadata dict

        Returns:
            Glyph markup for the image block
        """
        classes = [f"image-id-{image['id']}"]

        # Add dimensions if available
        if image.get("width_inches"):
            classes.append(f"image-width-{image['width_inches']}in")
        if image.get("height_inches"):
            classes.append(f"image-height-{image['height_inches']}in")

        # Add alt text if present
        alt_text = image.get("alt_text", "")
        if alt_text:
            # For now, put alt text as content; could add image-alt utility later
            class_str = "-".join(classes)
            return f"$glyph-{class_str}\n{alt_text}\n$glyph"
        else:
            class_str = "-".join(classes)
            return f"$glyph-{class_str}\n$glyph"

    def save(
        self,
        output_path: Optional[str] = None,
        workspace: Optional[Any] = None,
        filename: str = "output.glyph.txt",
    ) -> str:
        """
        Generate and save Glyph markup to a file.

        Args:
            output_path: Direct path to save to (takes precedence)
            workspace: Workspace instance to use for output_plaintext directory
            filename: Filename to use when saving to workspace

        Returns:
            Path to the saved file
        """
        markup = self.generate()

        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(markup, encoding="utf-8")
            return str(path)

        if workspace:
            # Use workspace's output_plaintext directory
            output_dir = workspace.directory("output_plaintext")
            path = Path(output_dir) / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(markup, encoding="utf-8")
            return str(path)

        raise ValueError("Either output_path or workspace must be provided")


def generate_plaintext_from_schema(
    schema: Dict[str, Any],
    output_path: Optional[str] = None,
    workspace: Optional[Any] = None,
    filename: str = "output.glyph.txt",
) -> str:
    """
    Convenience function to generate Glyph markup from a schema.

    Args:
        schema: The Glyph schema
        output_path: Direct path to save to
        workspace: Workspace instance for output_plaintext directory
        filename: Filename when saving to workspace

    Returns:
        Path to the saved file
    """
    generator = PlaintextGenerator(schema)
    return generator.save(output_path=output_path, workspace=workspace, filename=filename)
