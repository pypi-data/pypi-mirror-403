"""
Glyph Markup Schema Converter
==============================

Converts markup AST to schema_runner format, enabling markup to use
the existing writers (ParagraphWriter, ListWriter, etc.).

This provides a unified document generation pipeline:
    Markup → AST → Schema → Schema Runner → Writers → DOCX
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from ..parser.ast import DocumentNode, BlockNode, ParagraphNode, RowContainerNode, CellNode
from .layout_resolver import resolve_classes, LayoutBundle


def ast_to_schema(
    ast: DocumentNode,
    template_path: Optional[str] = None,
    tag: str = "markup",
) -> Dict[str, Any]:
    """
    Convert markup AST to schema_runner format.

    Args:
        ast: Parsed DocumentNode from markup
        template_path: Optional path to template DOCX
        tag: Schema tag for identification

    Returns:
        Schema dict compatible with GlyphSchemaRunner

    Examples:
        >>> from glyph.core.markup.parser import parse_markup
        >>> ast = parse_markup("$glyph-bold\\nHello\\n$glyph")
        >>> schema = ast_to_schema(ast)
        >>> schema['selectors'][0]['style']['font']['bold']  # Using new 'selectors' key
        True
        >>> schema['pattern_descriptors'][0]['style']['font']['bold']  # Old key still works
        True
    """
    pattern_descriptors = []

    for block in ast.blocks:
        # Check if this is a row container
        if isinstance(block, RowContainerNode):
            # Handle row layout specially
            descriptor = convert_row_container(block)
            pattern_descriptors.append(descriptor)
            continue

        # Regular block handling
        # Resolve block-level utilities
        block_layout = resolve_classes(block.classes)

        # Process paragraphs within the block
        for para in block.paragraphs:
            # Resolve paragraph-specific utilities
            para_layout = resolve_classes(para.classes)

            # Merge block + paragraph layouts (paragraph overrides block)
            merged = block_layout.merge(para_layout)

            # Infer descriptor type from utilities
            type_str = infer_type(block.classes + para.classes, merged)

            # Build descriptor in schema_runner format
            descriptor = {
                "type": type_str,
                "features": {
                    "text": para.text,
                },
                "style": build_style_dict(merged),
            }

            # CRITICAL: Add section properties to THIS descriptor only
            # Do NOT add to global_defaults - that's for schema developers
            if block_layout.section_props:
                descriptor["style"]["section"] = convert_section_props(block_layout.section_props)

            pattern_descriptors.append(descriptor)

    # Build schema
    # NOTE: Both "selectors" and "pattern_descriptors" are output for backward compatibility
    # "selectors" is the new primary key, "pattern_descriptors" is deprecated
    # This dual output will be maintained during the transition period
    schema = {
        "tag": tag,
        "selectors": pattern_descriptors,  # NEW: Primary key
        "pattern_descriptors": pattern_descriptors,  # DEPRECATED: Backward compatibility
    }

    if template_path:
        schema["source_docx"] = str(template_path)

    # NOTE: Markup does NOT set global_defaults
    # Global defaults are for schema developers to set document-wide baseline
    # Markup only provides block-level overrides

    return schema


def build_style_dict(layout: LayoutBundle) -> Dict[str, Any]:
    """
    Build style dict from layout bundle.

    Args:
        layout: Resolved LayoutBundle

    Returns:
        Style dict with style_id, font, and paragraph properties
    """
    style = {}

    # Extract style_id if present
    style_id = extract_style_id(layout)
    if style_id:
        style["style_id"] = style_id

    # Convert run properties to font dict
    if layout.run_props:
        style["font"] = convert_run_props(layout.run_props)

    # Convert paragraph properties
    if layout.paragraph_props:
        style["paragraph"] = convert_para_props(layout.paragraph_props)

    return style


def infer_type(classes: List[str], layout: LayoutBundle) -> str:
    """
    Infer descriptor type from utility classes and layout.

    Tries to determine if this is a heading, list, table, or paragraph
    based on the utilities used.

    Args:
        classes: List of utility class names
        layout: Resolved LayoutBundle

    Returns:
        Type string (e.g., "H1", "P-NORMAL", "L-BULLET")

    Examples:
        >>> layout = resolve_classes(["bold", "font-size-24", "align-center"])
        >>> infer_type(["bold", "font-size-24", "align-center"], layout)
        'H1'
    """
    # Check for explicit style utilities
    for cls in classes:
        # Heading styles
        if cls.startswith("para-style-heading-"):
            level = cls.split("-")[-1]
            if level.isdigit():
                return f"H{level}"
            # Map named levels
            level_map = {"1": "1", "2": "2", "3": "3", "one": "1", "two": "2", "three": "3"}
            return f"H{level_map.get(level, '1')}"

        # List styles
        if cls == "list-bullet":
            return "L-BULLET"
        if cls == "list-number":
            return "L-DECIMAL"

        # Specific paragraph styles
        if cls.startswith("para-style-"):
            # Already set as style_id, use normal paragraph
            return "P-NORMAL"

    # Heuristic inference based on properties
    run_props = layout.run_props
    para_props = layout.paragraph_props

    # Large, bold, centered text → likely a heading
    size = run_props.get("size", 11)
    is_bold = run_props.get("bold", False)
    is_centered = para_props.get("alignment") == "center"

    if is_bold and size >= 18:
        return "H1"
    elif is_bold and size >= 14:
        return "H2"
    elif is_bold and size >= 12:
        return "H3"
    elif is_bold and is_centered:
        return "H2"

    # Default to normal paragraph
    return "P-NORMAL"


def extract_style_id(layout: LayoutBundle) -> Optional[str]:
    """
    Extract Word style name from layout.

    Checks for explicit style_id utility or infers from common patterns.

    Args:
        layout: Resolved LayoutBundle

    Returns:
        Style name or None
    """
    # Check if style_id was explicitly set via para-style-{slug}
    if "style_id" in layout.paragraph_props:
        slug = layout.paragraph_props["style_id"]
        return map_style_slug_to_name(slug)

    # Check for character style
    if "character_style" in layout.run_props:
        slug = layout.run_props["character_style"]
        return map_style_slug_to_name(slug)

    # Infer from properties (optional - could map bold+large to "Heading 1")
    # For now, return None to let schema_runner use defaults
    return None


def map_style_slug_to_name(slug: str) -> str:
    """
    Map style slug to actual Word style name.

    Args:
        slug: Style slug (e.g., "heading-1", "body")

    Returns:
        Word style name

    Examples:
        >>> map_style_slug_to_name("heading-1")
        'Heading 1'
    """
    style_map = {
        "heading-1": "Heading 1",
        "heading-2": "Heading 2",
        "heading-3": "Heading 3",
        "heading-4": "Heading 4",
        "heading-5": "Heading 5",
        "heading-6": "Heading 6",
        "body": "Body Text",
        "body-text": "Body Text",
        "normal": "Normal",
        "caption": "Caption",
        "quote": "Quote",
        "intense-quote": "Intense Quote",
        "list-paragraph": "List Paragraph",
        "title": "Title",
        "subtitle": "Subtitle",
    }

    # Try exact match
    if slug in style_map:
        return style_map[slug]

    # Try with spaces converted to title case
    # "my-custom-style" -> "My Custom Style"
    return slug.replace("-", " ").title()


def convert_run_props(props: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert markup run props to schema format.

    Args:
        props: Markup run properties

    Returns:
        Schema-compatible font dict
    """
    font = {}

    # Font name
    if "font_name" in props:
        font["name"] = props["font_name"]

    # Font size (in points)
    if "size" in props:
        font["size"] = props["size"]

    # Emphasis
    if "bold" in props:
        font["bold"] = props["bold"]

    if "italic" in props:
        font["italic"] = props["italic"]

    if "underline" in props:
        # Convert True/False to string for schema
        underline = props["underline"]
        if isinstance(underline, bool):
            font["underline"] = underline
        else:
            # Already a style string (single, double, etc.)
            font["underline"] = underline

    if "strike" in props:
        font["strike"] = props["strike"]

    if "double_strike" in props:
        font["double_strike"] = props["double_strike"]

    # Color
    if "color" in props:
        # Color is already in hex format (RRGGBB)
        font["color"] = props["color"]

    if "highlight" in props:
        font["highlight"] = props["highlight"]

    # Case and script
    if "all_caps" in props:
        font["all_caps"] = props["all_caps"]

    if "small_caps" in props:
        font["small_caps"] = props["small_caps"]

    if "superscript" in props:
        font["superscript"] = props["superscript"]

    if "subscript" in props:
        font["subscript"] = props["subscript"]

    # Advanced properties
    for prop_name in ["hidden", "outline", "shadow", "emboss", "imprint"]:
        if prop_name in props:
            font[prop_name] = props[prop_name]

    return font


def convert_para_props(props: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert markup paragraph props to schema format.

    Args:
        props: Markup paragraph properties

    Returns:
        Schema-compatible paragraph dict
    """
    para = {}

    # Alignment
    if "alignment" in props:
        para["alignment"] = props["alignment"]

    # Indentation (convert from points to twips: 1pt = 20 twips)
    if "left_indent" in props:
        para["left_indent"] = props["left_indent"] * 20

    if "right_indent" in props:
        para["right_indent"] = props["right_indent"] * 20

    if "first_line_indent" in props:
        para["first_line_indent"] = props["first_line_indent"] * 20

    # Spacing (convert from points to twips)
    if "space_before" in props:
        para["spacing_before"] = props["space_before"] * 20

    if "space_after" in props:
        para["spacing_after"] = props["space_after"] * 20

    # Line spacing
    if "line_spacing" in props:
        para["line_spacing"] = props["line_spacing"]

    if "line_spacing_pt" in props:
        # Exact spacing in points
        para["line_spacing"] = props["line_spacing_pt"]

    # Pagination
    if "keep_together" in props:
        para["keep_together"] = props["keep_together"]

    if "keep_with_next" in props:
        para["keep_with_next"] = props["keep_with_next"]

    if "page_break_before" in props:
        para["page_break_before"] = props["page_break_before"]

    if "widow_control" in props:
        para["widow_control"] = props["widow_control"]

    return para


def convert_section_props(props: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert markup section props to schema format.

    Args:
        props: Markup section properties

    Returns:
        Schema-compatible section dict
    """
    section = {}

    # Orientation
    if "orientation" in props:
        section["orientation"] = props["orientation"]

    # Page size (in inches)
    if "page_width" in props:
        section["page_width"] = props["page_width"]

    if "page_height" in props:
        section["page_height"] = props["page_height"]

    # Margins (in inches)
    if "margin_left" in props:
        section["left_margin"] = props["margin_left"]

    if "margin_right" in props:
        section["right_margin"] = props["margin_right"]

    if "margin_top" in props:
        section["top_margin"] = props["margin_top"]

    if "margin_bottom" in props:
        section["bottom_margin"] = props["margin_bottom"]

    # Columns
    if "columns" in props:
        section["columns"] = props["columns"]

    return section


def convert_row_container(row_node: RowContainerNode) -> Dict[str, Any]:
    """
    Convert RowContainerNode to row descriptor for schema_runner.

    Args:
        row_node: RowContainerNode from AST

    Returns:
        Row descriptor in schema_runner format
    """
    # Resolve row-level utilities
    row_layout = resolve_classes(row_node.classes)

    # Build row configuration from row_props
    row_cfg = convert_row_props(row_layout.row_props)

    # Build cells configuration
    cells_cfg = []
    for cell in row_node.cells:
        cell_data = convert_cell(cell, row_layout)
        cells_cfg.append(cell_data)

    # Build descriptor
    descriptor = {
        "type": "R",
        "features": {
            "row": row_cfg,
            "cells": cells_cfg,
        },
        "style": build_row_style_dict(row_layout),
    }

    # Add section properties if present
    if row_layout.section_props:
        descriptor["style"]["section"] = convert_section_props(row_layout.section_props)

    return descriptor


def convert_row_props(props: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert markup row props to row configuration.

    Args:
        props: Markup row properties

    Returns:
        Row configuration dict
    """
    row = {}

    if "cols" in props:
        row["cols"] = props["cols"]

    if "widths" in props:
        widths = props["widths"]
        row["widths"] = widths

        # Determine width mode (percent vs ratio)
        width_mode = props.get("width_mode", "auto")
        if width_mode == "auto":
            # Auto-detect based on sum
            total = sum(widths)
            if abs(total - 100) < 1:
                width_mode = "percent"
            else:
                width_mode = "ratio"
        row["width_mode"] = width_mode

    if "total_width" in props:
        row["total_width"] = props["total_width"]

    if "alignment" in props:
        row["alignment"] = props["alignment"]

    if "indent" in props:
        row["indent"] = props["indent"]

    return row


def convert_cell(cell_node: CellNode, row_layout: LayoutBundle) -> Dict[str, Any]:
    """
    Convert CellNode to cell configuration.

    Args:
        cell_node: CellNode from AST
        row_layout: Parent row's layout bundle

    Returns:
        Cell configuration dict
    """
    # Resolve cell-level utilities
    cell_layout = resolve_classes(cell_node.classes)

    # Build cell configuration
    cell_cfg = {}

    # Cell alignment and valign from cell_props
    if "align" in cell_layout.cell_props:
        cell_cfg["align"] = cell_layout.cell_props["align"]

    if "valign" in cell_layout.cell_props:
        cell_cfg["valign"] = cell_layout.cell_props["valign"]

    if "padding" in cell_layout.cell_props:
        cell_cfg["padding"] = cell_layout.cell_props["padding"]

    if "width_override" in cell_layout.cell_props:
        cell_cfg["width_override"] = cell_layout.cell_props["width_override"]

    if "nowrap" in cell_layout.cell_props:
        cell_cfg["nowrap"] = cell_layout.cell_props["nowrap"]

    # Convert paragraphs to content
    content = []
    for para in cell_node.paragraphs:
        para_layout = resolve_classes(para.classes)
        merged = cell_layout.merge(para_layout)

        para_data = {
            "text": para.text,
            "style": build_style_dict(merged),
        }

        # Handle runs if present
        if para.runs:
            runs_data = []
            for run in para.runs:
                run_layout = resolve_classes(run.classes)
                run_merged = merged.merge(run_layout)

                run_data = {
                    "text": run.text,
                    "style": build_style_dict(run_merged),
                }
                runs_data.append(run_data)

            para_data["runs"] = runs_data

        content.append(para_data)

    cell_cfg["content"] = content

    return cell_cfg


def build_row_style_dict(layout: LayoutBundle) -> Dict[str, Any]:
    """
    Build style dict for row layout from layout bundle.

    Args:
        layout: Resolved LayoutBundle

    Returns:
        Style dict with row, cell, font, and paragraph properties
    """
    style = {}

    # Build row-level style (spacing, keep properties, etc.)
    row_style = {}

    if "space_before" in layout.row_props:
        row_style["space_before"] = layout.row_props["space_before"]

    if "space_after" in layout.row_props:
        row_style["space_after"] = layout.row_props["space_after"]

    if "keep_with_next" in layout.row_props:
        row_style["keep_with_next"] = layout.row_props["keep_with_next"]

    if "keep_together" in layout.row_props:
        row_style["keep_together"] = layout.row_props["keep_together"]

    if row_style:
        style["row"] = row_style

    # Build cell-level defaults
    cell_style = {}

    # Default cell padding
    if "default_cell_padding" in layout.row_props:
        padding = layout.row_props["default_cell_padding"]
        cell_style["padding"] = {
            "top": padding,
            "bottom": padding,
            "left": padding,
            "right": padding,
        }

    # Cell gap (visual separation)
    if "cell_gap" in layout.row_props:
        gap = layout.row_props["cell_gap"]
        # Implement gap as left/right padding adjustment
        if "padding" not in cell_style:
            cell_style["padding"] = {"top": 0.05, "bottom": 0.05, "left": gap / 2, "right": gap / 2}
        else:
            cell_style["padding"]["left"] = gap / 2
            cell_style["padding"]["right"] = gap / 2

    # Borders
    borders = layout.row_props.get("borders", "none")
    cell_style["borders"] = borders

    if cell_style:
        style["cell"] = cell_style

    # Convert run properties to font dict
    if layout.run_props:
        style["font"] = convert_run_props(layout.run_props)

    # Convert paragraph properties
    if layout.paragraph_props:
        style["paragraph"] = convert_para_props(layout.paragraph_props)

    return style


def render_markup_via_schema(
    markup_text: str,
    template_path: Optional[str] = None,
    output_path: Optional[str] = None,
    tag: str = "markup",
    validate: bool = True,
) -> Path:
    """
    Render markup text via schema_runner (uses existing writers).

    This is an alternative to render_markup_to_docx that routes through
    the schema_runner system, ensuring consistent styling and template
    handling across all input formats.

    Args:
        markup_text: Raw markup text
        template_path: Optional template DOCX path
        output_path: Output file path
        tag: Schema tag
        validate: Whether to validate markup first

    Returns:
        Path to saved DOCX file

    Examples:
        >>> markup = "$glyph-bold\\nHello World\\n$glyph"
        >>> output = render_markup_via_schema(markup, output_path="hello.docx")
    """
    from ..parser.parser import parse_markup
    from ..validator.validator import validate_ast
    from ...schema_runner.run_schema import GlyphSchemaRunner

    # Parse markup
    ast = parse_markup(markup_text)

    # Validate if requested
    if validate:
        diagnostics = validate_ast(ast)
        errors = [d for d in diagnostics if d.level == "error"]
        if errors:
            from ...language.errors import ValidationError

            error_msg = "\n".join(str(d) for d in errors)
            raise ValidationError(f"Markup validation failed:\n{error_msg}")

    # Convert to schema
    schema = ast_to_schema(ast, template_path=template_path, tag=tag)

    # Run through schema_runner
    runner = GlyphSchemaRunner(schema, source_docx=template_path)
    runner.run()

    # Save
    if output_path is None:
        output_path = "glyph_markup_output.docx"

    actual_path = runner.save(output_path, tag=tag)
    return Path(actual_path)
