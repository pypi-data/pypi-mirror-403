"""
Glyph Markup Token Utilities
============================

Helpers for encoding/decoding utility names.

Examples:
    - "font-size-12" -> {"type": "font-size", "value": 12}
    - "color-FF0000" -> {"type": "color", "value": "FF0000"}
    - "bold" -> {"type": "bold", "value": True}
"""

import re
from typing import Dict, Any, Optional


def parse_utility_name(name: str) -> Dict[str, Any]:
    """
    Parse a utility name into its components.

    Args:
        name: Utility name (e.g., "font-size-12", "color-FF0000", "bold")

    Returns:
        Dictionary with 'type' and 'value' keys

    Examples:
        >>> parse_utility_name("font-size-12")
        {'type': 'font-size', 'value': 12}

        >>> parse_utility_name("color-FF0000")
        {'type': 'color', 'value': 'FF0000'}

        >>> parse_utility_name("bold")
        {'type': 'bold', 'value': True}
    """
    # Pattern: {prefix}-{value}
    # Special cases: boolean flags (bold, italic, etc.) and negative flags (no-bold)

    # Check for negative flag first (e.g., "no-bold")
    if name.startswith("no-"):
        return {"type": name[3:], "value": False}

    # Try to split on last dash
    parts = name.rsplit("-", 1)

    if len(parts) == 1:
        # No value, just a flag (e.g., "bold")
        return {"type": name, "value": True}

    prefix, value_str = parts

    # Try to convert value to appropriate type
    # Check for integer
    if value_str.isdigit():
        return {"type": prefix, "value": int(value_str)}

    # Check for float with underscore (e.g., "1_5" -> 1.5)
    if "_" in value_str and all(p.isdigit() for p in value_str.split("_")):
        return {"type": prefix, "value": float(value_str.replace("_", "."))}

    # Otherwise, keep as string
    return {"type": prefix, "value": value_str}


def encode_utility_name(util_type: str, value: Any = True) -> str:
    """
    Encode a utility type and value into a utility name.

    Args:
        util_type: The utility type (e.g., "font-size", "color")
        value: The utility value

    Returns:
        Encoded utility name

    Examples:
        >>> encode_utility_name("font-size", 12)
        'font-size-12'

        >>> encode_utility_name("bold", False)
        'no-bold'

        >>> encode_utility_name("line-spacing", 1.5)
        'line-spacing-1_5'
    """
    if value is True:
        return util_type
    elif value is False:
        return f"no-{util_type}"
    elif isinstance(value, float):
        # Replace . with _ for float values
        return f"{util_type}-{str(value).replace('.', '_')}"
    else:
        return f"{util_type}-{value}"


def extract_color_from_name(name: str) -> Optional[str]:
    """
    Extract hex color value from utility name.

    Args:
        name: Utility name (e.g., "color-FF0000")

    Returns:
        Hex color string (without #) or None

    Examples:
        >>> extract_color_from_name("color-FF0000")
        'FF0000'

        >>> extract_color_from_name("highlight-yellow")
        None
    """
    parsed = parse_utility_name(name)
    if parsed["type"] == "color" and isinstance(parsed["value"], str):
        # Validate hex color
        if re.match(r'^[0-9A-Fa-f]{6}$', parsed["value"]):
            return parsed["value"].upper()
    return None


def extract_size_from_name(name: str) -> Optional[int]:
    """
    Extract size value from utility name.

    Args:
        name: Utility name (e.g., "font-size-12", "indent-left-20pt")

    Returns:
        Size value (in points) or None

    Examples:
        >>> extract_size_from_name("font-size-12")
        12

        >>> extract_size_from_name("indent-left-20pt")
        20
    """
    parsed = parse_utility_name(name)

    # Only extract from non-boolean values
    # If value is True/False, it's a flag, not a size
    if isinstance(parsed["value"], bool):
        return None

    # Handle numeric values directly
    if isinstance(parsed["value"], int):
        return parsed["value"]

    # Handle values with unit suffix (e.g., "20pt")
    if isinstance(parsed["value"], str):
        match = re.match(r'^(\d+)(pt|in|cm|mm)?$', parsed["value"])
        if match:
            return int(match.group(1))

    return None
