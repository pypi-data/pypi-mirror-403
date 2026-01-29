# src/glyph/core/analysis/context/heading_enricher.py

"""Heading-specific context enricher plugin."""

from typing import Dict, Any, List
from glyph.core.analysis.context.context_enricher import ContextWindow


def heading_context_enricher(
    context: ContextWindow,
    current_descriptor: Dict[str, Any],
    all_descriptors: List[Dict[str, Any]]
) -> None:
    """
    Enrich context with heading-specific signals.

    Adds DOCX-specific style comparison signals to the context window
    for use in subtitle detection and heading hierarchy analysis.

    Args:
        context: ContextWindow to enrich (modified in place)
        current_descriptor: Current element descriptor
        all_descriptors: Full list of descriptors

    Adds to context.custom_data:
        - size_smaller_than_prev: Current font size < previous
        - size_larger_than_prev: Current font size > previous
        - style_id_differs_from_prev: Different style_id from previous
        - bold_same_as_prev: Bold status matches previous
        - alignment_differs_from_prev: Alignment differs from previous
        - font_family_break: Font family changes from previous
        - prev_style_id: Previous element's style_id
        - next_style_id: Next element's style_id
        - is_heading_style: Current style_id contains "heading"
        - prev_pattern_type: Previous element's pattern type
        - next_pattern_type: Next element's pattern type
    """
    current_style = current_descriptor.get("style") or {}

    # Initialize heading-specific data
    heading_data = {
        "size_smaller_than_prev": False,
        "size_larger_than_prev": False,
        "style_id_differs_from_prev": False,
        "bold_same_as_prev": False,
        "alignment_differs_from_prev": False,
        "font_family_break": False,
        "prev_style_id": None,
        "next_style_id": None,
        "is_heading_style": False,
        "prev_pattern_type": None,
        "next_pattern_type": None,
    }

    # Check if current style is a heading style
    curr_style_id = current_style.get("style_id", "")
    if curr_style_id and "heading" in curr_style_id.lower():
        heading_data["is_heading_style"] = True

    # Compare with previous descriptor
    if context.prev_descriptors:
        prev = context.prev_descriptors[-1]  # Most recent previous
        prev_style = prev.get("style") or {}

        # Font size comparison
        prev_size = prev_style.get("font", {}).get("size", 12)
        curr_size = current_style.get("font", {}).get("size", 12)

        heading_data["size_smaller_than_prev"] = curr_size < prev_size
        heading_data["size_larger_than_prev"] = curr_size > prev_size

        # Style ID comparison
        prev_style_id = prev_style.get("style_id", "")
        heading_data["prev_style_id"] = prev_style_id
        heading_data["style_id_differs_from_prev"] = (
            prev_style_id != curr_style_id if prev_style_id and curr_style_id else False
        )

        # Bold comparison
        prev_bold = prev_style.get("font", {}).get("bold", False)
        curr_bold = current_style.get("font", {}).get("bold", False)
        heading_data["bold_same_as_prev"] = prev_bold == curr_bold

        # Alignment comparison
        prev_alignment = prev_style.get("alignment", "")
        curr_alignment = current_style.get("alignment", "")
        if prev_alignment and curr_alignment:
            heading_data["alignment_differs_from_prev"] = prev_alignment != curr_alignment

        # Font family comparison
        prev_font_family = prev_style.get("font", {}).get("name", "")
        curr_font_family = current_style.get("font", {}).get("name", "")
        if prev_font_family and curr_font_family:
            heading_data["font_family_break"] = prev_font_family != curr_font_family

        # Pattern type
        heading_data["prev_pattern_type"] = prev.get("type")

    # Compare with next descriptor
    if context.next_descriptors:
        next_elem = context.next_descriptors[0]  # Most immediate next
        next_style = next_elem.get("style") or {}

        heading_data["next_style_id"] = next_style.get("style_id", "")
        heading_data["next_pattern_type"] = next_elem.get("type")

    # Add to context custom data
    context.custom_data.update(heading_data)


def plaintext_heading_enricher(
    context: ContextWindow,
    current_descriptor: Dict[str, Any],
    all_descriptors: List[Dict[str, Any]]
) -> None:
    """
    Enrich context with plaintext-specific heading signals.

    For plaintext, we don't have style metadata, so we rely on
    pattern types and text-based heuristics.

    Args:
        context: ContextWindow to enrich (modified in place)
        current_descriptor: Current element descriptor
        all_descriptors: Full list of descriptors

    Adds to context.custom_data:
        - prev_line_length: Length of previous line text
        - current_is_shorter: Current line is shorter than previous
        - has_blank_line_before: Blank line immediately before
        - has_blank_line_after: Blank line immediately after
        - prev_was_all_caps: Previous line was all uppercase
        - current_is_title_case: Current line is title case
        - casing_differs_from_prev: Casing pattern differs from previous
        - indent_level: Indentation level (if available)
    """
    plaintext_data = {
        "prev_line_length": 0,
        "current_is_shorter": False,
        "has_blank_line_before": False,
        "has_blank_line_after": False,
        "prev_was_all_caps": False,
        "current_is_title_case": False,
        "casing_differs_from_prev": False,
        "indent_level": 0,
    }

    # Support both direct text field and features.text field
    current_text = current_descriptor.get("text", "")
    if not current_text and "features" in current_descriptor:
        current_text = current_descriptor["features"].get("text", "")

    # Check if current is title case
    if current_text:
        words = current_text.split()
        if words and words[0] and words[0][0].isupper():
            plaintext_data["current_is_title_case"] = True

    # Extract indent level if available
    if current_text:
        stripped = current_text.lstrip()
        indent = len(current_text) - len(stripped)
        plaintext_data["indent_level"] = indent

    # Compare with previous descriptor
    if context.prev_descriptors:
        prev = context.prev_descriptors[-1]
        prev_text = prev.get("text", "")
        if not prev_text and "features" in prev:
            prev_text = prev["features"].get("text", "")

        plaintext_data["prev_line_length"] = len(prev_text)

        # Check if current is shorter
        if prev_text:
            plaintext_data["current_is_shorter"] = len(current_text) < len(prev_text)

        # Check if previous was all caps
        plaintext_data["prev_was_all_caps"] = prev_text.isupper() if prev_text else False

        # Check casing differences
        prev_is_all_caps = prev_text.isupper() if prev_text else False
        curr_is_all_caps = current_text.isupper() if current_text else False
        plaintext_data["casing_differs_from_prev"] = prev_is_all_caps != curr_is_all_caps

    # Check for blank lines in original descriptors (not skipped)
    if context.index > 0:
        actual_prev = all_descriptors[context.index - 1]
        prev_text = actual_prev.get("text", "")
        if not prev_text and "features" in actual_prev:
            prev_text = actual_prev["features"].get("text", "")
        plaintext_data["has_blank_line_before"] = not prev_text.strip()

    if context.index < len(all_descriptors) - 1:
        actual_next = all_descriptors[context.index + 1]
        next_text = actual_next.get("text", "")
        if not next_text and "features" in actual_next:
            next_text = actual_next["features"].get("text", "")
        plaintext_data["has_blank_line_after"] = not next_text.strip()

    # Add to context custom data
    context.custom_data.update(plaintext_data)
