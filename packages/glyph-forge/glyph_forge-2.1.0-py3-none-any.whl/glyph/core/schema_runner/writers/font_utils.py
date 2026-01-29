# src/glyph/core/schema_runner/writers/font_utils.py
"""
Shared font utility functions for converting schema values to python-docx enums.
"""

from docx.enum.text import WD_UNDERLINE


def convert_underline_value(underline_val):
    """
    Convert various underline value formats to WD_UNDERLINE enum.

    Handles:
    - String values: "single", "double", "dotted", etc.
    - Boolean values: True -> SINGLE, False -> NONE
    - Already correct WD_UNDERLINE enums: pass through
    - None: returns None

    :param underline_val: The underline value from schema (string, bool, enum, or None)
    :return: WD_UNDERLINE enum value or None
    """
    if underline_val is None:
        return None

    # Handle string values like "single", "double", etc.
    if isinstance(underline_val, str):
        underline_map = {
            "single": WD_UNDERLINE.SINGLE,
            "double": WD_UNDERLINE.DOUBLE,
            "thick": WD_UNDERLINE.THICK,
            "dotted": WD_UNDERLINE.DOTTED,
            "dottedheavy": WD_UNDERLINE.DOTTED_HEAVY,
            "dash": WD_UNDERLINE.DASH,
            "dashheavy": WD_UNDERLINE.DASH_HEAVY,
            "dashlong": WD_UNDERLINE.DASH_LONG,
            "dashlongheavy": WD_UNDERLINE.DASH_LONG_HEAVY,
            "dotdash": WD_UNDERLINE.DOT_DASH,
            "dotdashheavy": WD_UNDERLINE.DOT_DASH_HEAVY,
            "dotdotdash": WD_UNDERLINE.DOT_DOT_DASH,
            "dotdotdashheavy": WD_UNDERLINE.DOT_DOT_DASH_HEAVY,
            "none": WD_UNDERLINE.NONE,
            "wavy": WD_UNDERLINE.WAVY,
            "wavydouble": WD_UNDERLINE.WAVY_DOUBLE,
            "wavyheavy": WD_UNDERLINE.WAVY_HEAVY,
            "words": WD_UNDERLINE.WORDS,
        }
        return underline_map.get(underline_val.lower(), WD_UNDERLINE.SINGLE)

    # Handle boolean values (True = single underline, False/None = no underline)
    elif isinstance(underline_val, bool):
        return WD_UNDERLINE.SINGLE if underline_val else WD_UNDERLINE.NONE

    # Otherwise assume it's already a WD_UNDERLINE enum
    return underline_val
