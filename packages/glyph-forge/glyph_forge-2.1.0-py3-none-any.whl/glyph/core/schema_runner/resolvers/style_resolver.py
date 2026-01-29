from typing import Any, Dict
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from glyph.settings import get_settings


def _verbose_print(*args, **kwargs):
    """Print only if SDK_VERBOSE_LOGGING is enabled."""
    settings = get_settings()
    if settings.SDK_VERBOSE_LOGGING:
        print(*args, **kwargs)


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dicts.
    Values in override take precedence over base.
    """
    merged = dict(base)  # copy
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


def _normalize_flat_style_properties(schema_style: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert flat style properties to nested format.

    Handles agent-generated schemas that have flat properties like:
      {'bold': True, 'size': 16, 'alignment': 'center'}

    And converts them to nested format:
      {'font': {'bold': True, 'size': 16}, 'paragraph': {'alignment': 'center'}}
    """
    normalized = dict(schema_style)  # Copy to avoid mutating original

    # Font properties that might be flat
    font_props_map = {
        'bold': 'bold',
        'italic': 'italic',
        'underline': 'underline',
        'size': 'size',  # Agent uses 'size', SDK expects 'size'
        'font_name': 'name',  # Agent uses 'font_name', SDK expects 'name'
        'color': 'color',
        'size': 'size',  # Also support direct 'size'
        'name': 'name',  # Also support direct 'name'
    }

    # Paragraph properties that might be flat
    paragraph_props = ['alignment', 'spacing', 'indent', 'line_spacing']

    # Extract flat font properties
    flat_font_props = {}
    for flat_key, nested_key in font_props_map.items():
        if flat_key in normalized and flat_key not in ['font', 'paragraph', 'style_id', 'list']:
            flat_font_props[nested_key] = normalized.pop(flat_key)

    # Extract flat paragraph properties
    flat_para_props = {}
    for prop in paragraph_props:
        if prop in normalized and prop not in ['font', 'paragraph', 'style_id', 'list']:
            flat_para_props[prop] = normalized.pop(prop)

    # Merge flat properties into nested structure
    if flat_font_props:
        if 'font' not in normalized:
            normalized['font'] = {}
        normalized['font'] = {**normalized['font'], **flat_font_props}

    if flat_para_props:
        if 'paragraph' not in normalized:
            normalized['paragraph'] = {}
        normalized['paragraph'] = {**normalized['paragraph'], **flat_para_props}

    return normalized


def resolve_style(
    descriptor: Dict[str, Any],
    schema: Dict[str, Any],
    global_defaults: Dict[str, Any],
    docx_styles: dict | None,
) -> Dict[str, Any]:
    _verbose_print(f"[SDK]     🔄 [STYLE_RESOLVER] Starting style resolution...")

    # CRITICAL: Check if descriptor has top-level font/paragraph (new format)
    # vs nested in "style" dict (old format)
    descriptor_has_top_level_props = "font" in descriptor or "paragraph" in descriptor
    schema_style_raw = descriptor.get("style", {}) or {}

    # Normalize flat properties to nested format (handles agent-generated schemas)
    schema_style = _normalize_flat_style_properties(schema_style_raw)

    _verbose_print(f"[SDK]     📥 INPUT:")
    _verbose_print(f"[SDK]       - descriptor.font: {descriptor.get('font', 'NOT PRESENT')}")
    _verbose_print(f"[SDK]       - descriptor.paragraph: {descriptor.get('paragraph', 'NOT PRESENT')}")
    _verbose_print(f"[SDK]       - descriptor.style (raw): {schema_style_raw}")
    if schema_style_raw != schema_style:
        _verbose_print(f"[SDK]       - descriptor.style (normalized): {schema_style}")
    _verbose_print(f"[SDK]       - global_defaults.font: {global_defaults.get('font', {})}")
    _verbose_print(f"[SDK]       - global_defaults.paragraph: {global_defaults.get('paragraph', {})}")

    merged: Dict[str, Any] = {}

    # --- Step 1: style_id
    if "style_id" in schema_style:
        style_id = schema_style["style_id"]
        merged["style_id"] = style_id
        _verbose_print(f"[SDK]       📌 Found style_id: {style_id}")

        if docx_styles and style_id in docx_styles:
            word_style = docx_styles[style_id]
            merged["font"] = {}

            # Extract ALL font properties from the DOCX style, not just name and size
            if getattr(word_style.font, "name", None):
                merged["font"]["name"] = word_style.font.name

            if getattr(word_style.font, "size", None):
                merged["font"]["size"] = word_style.font.size.pt

            # Bold, italic, underline can be True, False, or None (inherit)
            bold = getattr(word_style.font, "bold", None)
            if bold is not None:
                merged["font"]["bold"] = bold

            italic = getattr(word_style.font, "italic", None)
            if italic is not None:
                merged["font"]["italic"] = italic

            underline = getattr(word_style.font, "underline", None)
            if underline is not None:
                merged["font"]["underline"] = underline

            # Color is accessed via .color.rgb which returns RGBColor or None
            try:
                if word_style.font.color and word_style.font.color.rgb:
                    # Convert RGBColor to hex string (e.g., "FF0000")
                    rgb = word_style.font.color.rgb
                    merged["font"]["color"] = str(rgb)
            except (AttributeError, ValueError):
                # Color not set or invalid
                pass

            _verbose_print(f"[SDK]       📖 Extracted from DOCX style '{style_id}': {merged['font']}")

    # --- Step 2: Font resolution priority
    # Priority: global_defaults.font < docx_style.font < descriptor.font (if top-level) < schema_style.font

    _verbose_print(f"[SDK]       🔀 Font resolution (priority: global < docx_style < descriptor < schema_style):")

    # Start with global defaults as BASE
    base_font = global_defaults.get("font", {}).copy() if global_defaults else {}
    _verbose_print(f"[SDK]         Layer 1 (global_defaults): {base_font}")

    # Layer 2: Merge DOCX style font (if extracted from style_id lookup above)
    if "font" in merged and merged["font"]:
        base_font = deep_merge(base_font, merged["font"])
        _verbose_print(f"[SDK]         Layer 2 (docx_style): {base_font}")

    # Layer 3: Top-level descriptor.font (NEW - agent might put font here!)
    if "font" in descriptor:
        _verbose_print(f"[SDK]         ⚠️ Found TOP-LEVEL descriptor.font: {descriptor['font']}")
        base_font = deep_merge(base_font, descriptor["font"])
        _verbose_print(f"[SDK]         Layer 3 (descriptor.font): {base_font}")

    # Layer 4: Schema style overrides (highest priority)
    if "font" in schema_style:
        _verbose_print(f"[SDK]         Found schema_style.font: {schema_style['font']}")
        base_font = deep_merge(base_font, schema_style["font"])
        _verbose_print(f"[SDK]         Layer 4 (schema_style.font): {base_font}")

    merged["font"] = base_font
    _verbose_print(f"[SDK]       ✅ FINAL FONT: {merged['font']}")

    # --- Step 3: paragraph merging
    _verbose_print(f"[SDK]       🔀 Paragraph resolution:")

    # Start with global defaults
    base_para = global_defaults.get("paragraph", {}).copy() if global_defaults else {}
    _verbose_print(f"[SDK]         Layer 1 (global_defaults): {base_para}")

    # Layer 2: Top-level descriptor.paragraph
    if "paragraph" in descriptor:
        _verbose_print(f"[SDK]         ⚠️ Found TOP-LEVEL descriptor.paragraph: {descriptor['paragraph']}")
        base_para = deep_merge(base_para, descriptor["paragraph"])
        _verbose_print(f"[SDK]         Layer 2 (descriptor.paragraph): {base_para}")

    # Layer 3: Schema style overrides (highest priority)
    if "paragraph" in schema_style:
        _verbose_print(f"[SDK]         Found schema_style.paragraph: {schema_style['paragraph']}")
        base_para = deep_merge(base_para, schema_style["paragraph"])
        _verbose_print(f"[SDK]         Layer 3 (schema_style.paragraph): {base_para}")

    merged["paragraph"] = base_para
    _verbose_print(f"[SDK]       ✅ FINAL PARAGRAPH: {merged['paragraph']}")

    # --- Step 4: preserve list metadata if present
    if "list" in schema_style:
        merged["list"] = schema_style["list"]

    _verbose_print(f"[SDK]       📤 OUTPUT: {merged}")

    return merged


def apply_style_to_paragraph(paragraph, style: Dict[str, Any]):
    """
    Given a python-docx paragraph and merged style dict,
    apply styles safely.
    """
    # Style ID (if valid)
    if "style_id" in style and style["style_id"] in [s.name for s in paragraph.part.styles]:
        paragraph.style = style["style_id"]

    # Font properties
    if "font" in style:
        run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
        font = style["font"]
        if "name" in font:
            run.font.name = font["name"]
        if "size" in font:
            run.font.size = Pt(font["size"])
        if "bold" in font:
            run.font.bold = font["bold"]

    # Paragraph properties
    if "paragraph" in style:
        para = style["paragraph"]
        if "alignment" in para:
            align = para["alignment"].lower()
            if align == "left":
                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            elif align == "center":
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif align == "right":
                paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            elif align == "justify":
                paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
