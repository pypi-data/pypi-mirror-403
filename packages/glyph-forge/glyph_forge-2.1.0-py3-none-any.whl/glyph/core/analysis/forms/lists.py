# src/glyph/core/analysis/forms/lists.py
from __future__ import annotations
from enum import Enum
from typing import Dict, Any, Optional

from glyph.core.analysis.detectors.heuristics.list_detector import (
    BULLET_RE, ORDERED_RE, ORDERED_NESTED_RE,
    DEFINITION_RE, INDENTED_RE,
)


class ListForm(str, Enum):
    """
    Axis 1 — List subtypes.

    Canonical forms of lists detected in text or DOCX.
    Supports granular bullet and ordered list type detection.

    Standard numId mappings (for DOCX compatibility):
      - numId 1:  L-BULLET-SOLID
      - numId 4:  L-BULLET-HOLLOW
      - numId 5:  L-BULLET-SQUARE
      - numId 6:  L-ORDERED-DOTTED
      - numId 7:  L-ORDERED-PARA-NUM
      - numId 8:  L-ORDERED-ROMAN-UPPER
      - numId 9:  L-ORDERED-ALPHA-UPPER
      - numId 10: L-ORDERED-ALPHA-LOWER-PAREN
      - numId 11: L-ORDERED-ALPHA-LOWER-DOT
      - numId 12: L-ORDERED-ROMAN-LOWER
    """

    # Generic types (backward compatibility)
    L_BULLET       = "L-BULLET"        # Generic bulleted list
    L_ORDERED      = "L-ORDERED"       # Generic ordered list
    L_DEFINITION   = "L-DEFINITION"    # Definition-style lists
    L_CONTINUATION = "L-CONTINUATION"  # Continuation / wrapped lines
    L_UNKNOWN      = "L-UNKNOWN"       # Fallback

    # Granular bullet types
    L_BULLET_SOLID  = "L-BULLET-SOLID"   # Solid bullets (•, ●, -, *) - numId: 1
    L_BULLET_HOLLOW = "L-BULLET-HOLLOW"  # Hollow bullets (◦, o) - numId: 4
    L_BULLET_SQUARE = "L-BULLET-SQUARE"  # Square bullets (▪, ■) - numId: 5

    # Granular ordered types
    L_ORDERED_DOTTED           = "L-ORDERED-DOTTED"            # Decimal dotted (1., 2., 3.) - numId: 6
    L_ORDERED_PARA_NUM         = "L-ORDERED-PARA-NUM"          # Decimal parenthesis (1), 2), 3)) - numId: 7
    L_ORDERED_ROMAN_UPPER      = "L-ORDERED-ROMAN-UPPER"       # Upper Roman (I., II., III.) - numId: 8
    L_ORDERED_ALPHA_UPPER      = "L-ORDERED-ALPHA-UPPER"       # Upper Alpha (A., B., C.) - numId: 9
    L_ORDERED_ALPHA_LOWER_PAREN = "L-ORDERED-ALPHA-LOWER-PAREN"  # Lower Alpha paren (a), b), c)) - numId: 10
    L_ORDERED_ALPHA_LOWER_DOT   = "L-ORDERED-ALPHA-LOWER-DOT"    # Lower Alpha dot (a., b., c.) - numId: 11
    L_ORDERED_ROMAN_LOWER      = "L-ORDERED-ROMAN-LOWER"       # Lower Roman (i., ii., iii.) - numId: 12


def classify_list_line(text: str, features: Optional[Dict[str, Any]] = None) -> ListForm:
    """
    Map a line (already detected as 'list') into a specific ListForm subtype.

    Sources of evidence (in order of priority):
      1. Regex match on plaintext (quick heuristic)
      2. Features derived from DOCX schema extraction (style.list, style_id, etc.)
      3. Indentation or fallback rules
    """
    s = (text or "").strip()
    if not s:
        return ListForm.L_UNKNOWN

    # ---------- Regex-based classification ----------
    if BULLET_RE.match(s):
        return ListForm.L_BULLET
    if ORDERED_RE.match(s) or ORDERED_NESTED_RE.match(s):
        return ListForm.L_ORDERED
    if DEFINITION_RE.match(s):
        return ListForm.L_DEFINITION
    if INDENTED_RE.match(s):
        return ListForm.L_CONTINUATION

    # ---------- Feature-based classification ----------
    if features:
        # DOCX-extracted numbering info
        list_info = features.get("list")
        if list_info:
            num_id = list_info.get("numId")
            ilvl = int(list_info.get("ilvl", 0))

            # At this layer we don’t know the exact symbol/format yet,
            # but writers will resolve numId → bullet/decimal/roman/etc.
            # So we just normalize into BULLET vs ORDERED.
            # (Convention: odd numIds = bullets, even numIds = ordered → refined later by writer)
            if features.get("style_id", "").lower().startswith("listbullet"):
                return ListForm.L_BULLET
            if features.get("style_id", "").lower().startswith("listnumber"):
                return ListForm.L_ORDERED

            # fallback: treat numId presence as ordered list
            if num_id is not None:
                return ListForm.L_ORDERED

            # indentation
            if ilvl > 0:
                return ListForm.L_CONTINUATION

        # Plain style flags
        if features.get("is_bullet"):
            return ListForm.L_BULLET
        if features.get("is_numbered"):
            return ListForm.L_ORDERED
        if features.get("indent_level", 0) > 0:
            return ListForm.L_CONTINUATION
        if features.get("style_name", "").lower().startswith("definition"):
            return ListForm.L_DEFINITION

    # ---------- Fallback ----------
    return ListForm.L_UNKNOWN
