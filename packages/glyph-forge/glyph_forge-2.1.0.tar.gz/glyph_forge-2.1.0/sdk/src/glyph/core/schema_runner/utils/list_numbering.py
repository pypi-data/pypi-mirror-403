"""
List Numbering Utilities
=========================

Standard numId mappings for consistent list formatting across documents.

These mappings ensure that list type descriptors (L-BULLET-SOLID, L-ORDERED-DOTTED, etc.)
consistently map to specific numId values in DOCX numbering.xml.

Usage:
    # Get numId for a list type
    numid = get_numid_for_type("L-BULLET-SOLID")  # Returns "1"

    # Get list type from numId
    list_type = get_type_for_numid("6")  # Returns "L-ORDERED-DOTTED"

    # Get format configuration for a list type
    config = get_format_config("L-ORDERED-ROMAN-UPPER")
    # Returns {"format": "upperRoman", "numId": "8", "lvlText": "I."}
"""

from typing import Dict, Optional


# Standard numId → List Type mapping
# Based on common DOCX numbering definitions
STANDARD_NUMID_MAP: Dict[str, str] = {
    "1": "L-BULLET-SOLID",         # Solid bullets (•, ●, -, *)
    "4": "L-BULLET-HOLLOW",        # Hollow bullets (◦, o)
    "5": "L-BULLET-SQUARE",        # Square bullets (▪, ■)
    "6": "L-ORDERED-DOTTED",       # Decimal dotted (1., 2., 3.)
    "7": "L-ORDERED-PARA-NUM",     # Decimal parenthesis (1), 2), 3))
    "8": "L-ORDERED-ROMAN-UPPER",  # Upper Roman (I., II., III.)
    "9": "L-ORDERED-ALPHA-UPPER",  # Upper Alpha (A., B., C.)
    "10": "L-ORDERED-ALPHA-LOWER-PAREN",  # Lower Alpha paren (a), b), c))
    "11": "L-ORDERED-ALPHA-LOWER-DOT",    # Lower Alpha dot (a., b., c.)
    "12": "L-ORDERED-ROMAN-LOWER", # Lower Roman (i., ii., iii.)
}

# Reverse mapping: List Type → numId
TYPE_TO_NUMID_MAP: Dict[str, str] = {v: k for k, v in STANDARD_NUMID_MAP.items()}

# Format configurations for each list type
# Maps list type to DOCX format properties
FORMAT_CONFIG_MAP: Dict[str, Dict[str, str]] = {
    "L-BULLET-SOLID": {
        "format": "bullet",
        "numId": "1",
        "lvlText": "•",  # Default bullet character
        "numFmt": "bullet",
    },
    "L-BULLET-HOLLOW": {
        "format": "bullet",
        "numId": "4",
        "lvlText": "◦",
        "numFmt": "bullet",
    },
    "L-BULLET-SQUARE": {
        "format": "bullet",
        "numId": "5",
        "lvlText": "▪",
        "numFmt": "bullet",
    },
    "L-ORDERED-DOTTED": {
        "format": "decimal",
        "numId": "6",
        "lvlText": "%1.",
        "numFmt": "decimal",
    },
    "L-ORDERED-PARA-NUM": {
        "format": "decimal",
        "numId": "7",
        "lvlText": "%1)",
        "numFmt": "decimal",
    },
    "L-ORDERED-ROMAN-UPPER": {
        "format": "upperRoman",
        "numId": "8",
        "lvlText": "%1.",
        "numFmt": "upperRoman",
    },
    "L-ORDERED-ALPHA-UPPER": {
        "format": "upperLetter",
        "numId": "9",
        "lvlText": "%1.",
        "numFmt": "upperLetter",
    },
    "L-ORDERED-ALPHA-LOWER-PAREN": {
        "format": "lowerLetter",
        "numId": "10",
        "lvlText": "%1)",
        "numFmt": "lowerLetter",
    },
    "L-ORDERED-ALPHA-LOWER-DOT": {
        "format": "lowerLetter",
        "numId": "11",
        "lvlText": "%1.",
        "numFmt": "lowerLetter",
    },
    "L-ORDERED-ROMAN-LOWER": {
        "format": "lowerRoman",
        "numId": "12",
        "lvlText": "%1.",
        "numFmt": "lowerRoman",
    },
}


def get_numid_for_type(list_type: str) -> Optional[str]:
    """
    Get the standard numId for a list type.

    Args:
        list_type: List type string (e.g., "L-BULLET-SOLID", "L-ORDERED-DOTTED")

    Returns:
        Standard numId string or None if not found

    Examples:
        >>> get_numid_for_type("L-BULLET-SOLID")
        "1"
        >>> get_numid_for_type("L-ORDERED-DOTTED")
        "6"
    """
    return TYPE_TO_NUMID_MAP.get(list_type)


def get_type_for_numid(numid: str) -> Optional[str]:
    """
    Get the list type for a numId.

    Args:
        numid: numId string (e.g., "1", "6", "12")

    Returns:
        List type string or None if not found

    Examples:
        >>> get_type_for_numid("1")
        "L-BULLET-SOLID"
        >>> get_type_for_numid("6")
        "L-ORDERED-DOTTED"
    """
    return STANDARD_NUMID_MAP.get(numid)


def get_format_config(list_type: str) -> Optional[Dict[str, str]]:
    """
    Get the complete format configuration for a list type.

    Args:
        list_type: List type string (e.g., "L-BULLET-SOLID")

    Returns:
        Dict with format, numId, lvlText, numFmt or None if not found

    Examples:
        >>> get_format_config("L-ORDERED-ROMAN-UPPER")
        {"format": "upperRoman", "numId": "8", "lvlText": "%1.", "numFmt": "upperRoman"}
    """
    return FORMAT_CONFIG_MAP.get(list_type)


def normalize_list_type(list_type: str) -> str:
    """
    Normalize a list type to its granular form if possible.

    Maps generic types (L-BULLET, L-ORDERED) to their most common specific type.

    Args:
        list_type: List type string (generic or specific)

    Returns:
        Normalized list type (preferring granular types)

    Examples:
        >>> normalize_list_type("L-BULLET")
        "L-BULLET-SOLID"
        >>> normalize_list_type("L-ORDERED")
        "L-ORDERED-DOTTED"
        >>> normalize_list_type("L-BULLET-HOLLOW")
        "L-BULLET-HOLLOW"
    """
    # Map generic types to their most common specific type
    generic_to_specific = {
        "L-BULLET": "L-BULLET-SOLID",
        "L-ORDERED": "L-ORDERED-DOTTED",
    }

    return generic_to_specific.get(list_type, list_type)


def is_bullet_type(list_type: str) -> bool:
    """Check if a list type is a bullet type."""
    return list_type.startswith("L-BULLET")


def is_ordered_type(list_type: str) -> bool:
    """Check if a list type is an ordered type."""
    return list_type.startswith("L-ORDERED")


def get_fallback_type(list_type: str) -> str:
    """
    Get the generic fallback type for a specific list type.

    Args:
        list_type: Specific list type (e.g., "L-BULLET-SOLID")

    Returns:
        Generic type (e.g., "L-BULLET")

    Examples:
        >>> get_fallback_type("L-BULLET-SOLID")
        "L-BULLET"
        >>> get_fallback_type("L-ORDERED-ROMAN-UPPER")
        "L-ORDERED"
    """
    if is_bullet_type(list_type):
        return "L-BULLET"
    elif is_ordered_type(list_type):
        return "L-ORDERED"
    else:
        return list_type
