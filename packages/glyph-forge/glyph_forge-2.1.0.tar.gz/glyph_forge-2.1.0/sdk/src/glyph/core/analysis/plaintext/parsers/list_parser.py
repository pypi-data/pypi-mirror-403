from __future__ import annotations
import re
from typing import Tuple, Dict, Any

BULLETS = {"•","·","‣","◦","–","-","*","—","▪","●","■","o"}
# Supports hierarchical numbering (1.1.1, 1.2, etc.), letters, and roman numerals
# Pattern requires whitespace after number to avoid matching decimals in sentences
ORDERED_RE = re.compile(r"^\s*(\d+(\.\d+)*[\.\)]?\s+|[a-zA-Z][\.\)]\s+|[ivxlcdmIVXLCDM]+[\.\)]\s+)")

def detect_bullet_type(marker: str) -> str:
    """Detect the specific bullet type from the marker character.

    Returns:
        L-BULLET-SOLID, L-BULLET-HOLLOW, or L-BULLET-SQUARE
    """
    solid_bullets = {"•", "●", "·", "-", "–", "—", "*"}
    hollow_bullets = {"◦", "o"}
    square_bullets = {"▪", "■"}

    if marker in solid_bullets:
        return "L-BULLET-SOLID"
    elif marker in hollow_bullets:
        return "L-BULLET-HOLLOW"
    elif marker in square_bullets:
        return "L-BULLET-SQUARE"
    else:
        return "L-BULLET"


def detect_ordered_type(marker: str) -> Tuple[str, str, str]:
    """Detect the specific ordered list type from the marker pattern.

    Args:
        marker: The full marker including suffix (e.g., "1.", "a)", "I.", "iv)")

    Returns:
        Tuple of (list_type, format, lvlText) where:
        - list_type: L-ORDERED-DOTTED, L-ORDERED-PARA-NUM, etc.
        - format: decimal, upperRoman, lowerRoman, upperLetter, lowerLetter
        - lvlText: pattern like "%1." or "%1)"
    """
    marker = marker.strip()

    # Check suffix
    has_paren = marker.endswith(")")
    has_dot = marker.endswith(".")
    suffix = ")" if has_paren else "."

    # Remove suffix to get the numbering part
    num_part = marker[:-1]

    # Decimal numbers (1, 2, 3) or hierarchical (1.1, 1.2.3)
    # Check if it's all digits OR hierarchical pattern (digits with dots)
    is_decimal = num_part.isdigit()
    is_hierarchical = all(c.isdigit() or c == '.' for c in num_part) and any(c.isdigit() for c in num_part)

    if is_decimal or is_hierarchical:
        list_type = "L-ORDERED-PARA-NUM" if has_paren else "L-ORDERED-DOTTED"
        return list_type, "decimal", f"%1{suffix}"

    # Upper Roman (I, II, III, IV, V)
    if num_part.isupper() and all(c in "IVXLCDM" for c in num_part):
        return "L-ORDERED-ROMAN-UPPER", "upperRoman", f"%1{suffix}"

    # Lower Roman (i, ii, iii, iv, v)
    if num_part.islower() and all(c in "ivxlcdm" for c in num_part):
        return "L-ORDERED-ROMAN-LOWER", "lowerRoman", f"%1{suffix}"

    # Upper letter (A, B, C)
    if len(num_part) == 1 and num_part.isupper() and num_part.isalpha():
        return "L-ORDERED-ALPHA-UPPER", "upperLetter", f"%1{suffix}"

    # Lower letter (a, b, c) - differentiate by suffix
    if len(num_part) == 1 and num_part.islower() and num_part.isalpha():
        if has_paren:
            return "L-ORDERED-ALPHA-LOWER-PAREN", "lowerLetter", f"%1)"
        else:
            return "L-ORDERED-ALPHA-LOWER-DOT", "lowerLetter", f"%1."

    # Default fallback
    list_type = "L-ORDERED-PARA-NUM" if has_paren else "L-ORDERED-DOTTED"
    return list_type, "decimal", f"%1{suffix}"


def is_bullet_line(line: str) -> bool:
    s = line.lstrip()
    return bool(s) and ((s[:1] in BULLETS) or bool(ORDERED_RE.match(s)))

def normalize_bullet_line(line: str, wrap_indent_spaces: int = 2) -> Tuple[int, str, str, Dict[str, Any]]:
    """Parse a list line and extract metadata.

    Args:
        line: The line to parse
        wrap_indent_spaces: Number of spaces per indent level

    Returns:
        Tuple of (ilvl, content, list_type, metadata) where:
        - ilvl: indent level
        - content: text content without marker
        - list_type: specific list type (L-BULLET-SOLID, L-ORDERED-DOTTED, etc.)
        - metadata: dict with format, lvlText, marker
    """
    indent = len(line) - len(line.lstrip(" "))
    s = line.lstrip()
    ilvl = max(0, indent // max(wrap_indent_spaces, 1))

    # Default metadata
    list_type = "L-UNKNOWN"
    metadata: Dict[str, Any] = {
        "format": None,
        "lvlText": None,
        "marker": None,
    }

    # Bullet lists
    if s[:1] in BULLETS:
        marker = s[:1]
        content = s[1:].lstrip()
        list_type = detect_bullet_type(marker)
        metadata = {
            "format": "bullet",
            "lvlText": marker,
            "marker": marker,
        }
        return ilvl, content, list_type, metadata

    # Ordered lists
    match = ORDERED_RE.match(s)
    if match:
        marker = match.group(1)
        content = ORDERED_RE.sub("", s, 1).lstrip()
        list_type, fmt, lvl_text = detect_ordered_type(marker)
        metadata = {
            "format": fmt,
            "lvlText": lvl_text,
            "marker": marker,
        }
        return ilvl, content, list_type, metadata

    # Fallback - not a list line
    content = s
    return ilvl, content, list_type, metadata
