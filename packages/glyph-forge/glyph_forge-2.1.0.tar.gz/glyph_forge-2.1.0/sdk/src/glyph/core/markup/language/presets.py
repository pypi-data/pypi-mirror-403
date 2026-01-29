"""
Glyph Markup Utility Presets
============================

Curated sets of utilities grouped by domain or use case.
"""

from typing import List
from .registry import get_utilities_by_scope

# Core utility sets by scope
CORE_RUN_UTILITIES: List[str] = [
    "bold", "italic", "underline", "strike",
    "font-size-{pt}", "font-name-{family}",
    "color-{RRGGBB}", "highlight-{color}",
    "all-caps", "small-caps",
    "superscript", "subscript",
]

CORE_PARAGRAPH_UTILITIES: List[str] = [
    "align-left", "align-center", "align-right", "align-justify",
    "indent-left-{N}pt", "indent-right-{N}pt", "indent-first-line-{N}pt",
    "space-before-{N}pt", "space-after-{N}pt",
    "line-spacing-1_0", "line-spacing-1_5", "line-spacing-2_0",
    "keep-together", "keep-with-next", "page-break-before",
]

CORE_SECTION_UTILITIES: List[str] = [
    "section-orientation-portrait", "section-orientation-landscape",
    "section-size-letter", "section-size-legal", "section-size-a4",
    "section-margin-all-{N}in",
    "layout-col-1", "layout-col-2", "layout-col-3",
]

CORE_BREAK_UTILITIES: List[str] = [
    "page-break", "line-break", "column-break",
]

# Domain-specific presets
ACADEMIC_UTILITIES: List[str] = [
    "font-name-times-new-roman",
    "font-size-12",
    "line-spacing-2_0",
    "align-justify",
    "indent-first-line-36pt",
    "section-margin-all-1in",
]

BUSINESS_UTILITIES: List[str] = [
    "font-name-calibri",
    "font-size-11",
    "line-spacing-1_0",
    "align-left",
    "section-margin-all-1in",
]

RESUME_UTILITIES: List[str] = [
    "font-name-calibri",
    "font-size-11",
    "font-size-14",  # For headings
    "bold",
    "align-left",
    "space-before-6pt",
    "space-after-6pt",
]

# Simple utility shortcuts
SHORTCUTS = {
    "h1": ["font-size-24", "bold", "space-before-12pt", "space-after-6pt"],
    "h2": ["font-size-18", "bold", "space-before-10pt", "space-after-4pt"],
    "h3": ["font-size-14", "bold", "space-before-8pt", "space-after-2pt"],
    "body": ["font-size-11", "line-spacing-1_5", "align-justify"],
    "code": ["font-name-courier-new", "font-size-10"],
    "quote": ["italic", "indent-left-36pt", "indent-right-36pt"],
}


def expand_shortcuts(utilities: List[str]) -> List[str]:
    """
    Expand utility shortcuts into full utility names.

    Args:
        utilities: List of utility names (may include shortcuts)

    Returns:
        Expanded list with shortcuts replaced

    Examples:
        >>> expand_shortcuts(["h1", "bold"])
        ["font-size-24", "bold", "space-before-12pt", "space-after-6pt", "bold"]
    """
    expanded = []
    for util in utilities:
        if util in SHORTCUTS:
            expanded.extend(SHORTCUTS[util])
        else:
            expanded.append(util)
    return expanded


def get_preset(preset_name: str) -> List[str]:
    """
    Get a named preset.

    Args:
        preset_name: Name of the preset (e.g., "academic", "business")

    Returns:
        List of utility names

    Raises:
        KeyError: If preset not found
    """
    presets = {
        "academic": ACADEMIC_UTILITIES,
        "business": BUSINESS_UTILITIES,
        "resume": RESUME_UTILITIES,
    }
    return presets[preset_name]
