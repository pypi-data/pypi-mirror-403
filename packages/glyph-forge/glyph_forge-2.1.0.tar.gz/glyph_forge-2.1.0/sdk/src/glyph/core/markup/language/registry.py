"""
Glyph Markup Utility Registry
==============================

Source of truth for all allowed utilities and their mappings to DOCX properties.

Each utility is defined as a UtilityDef with:
- name: The utility class name (e.g., "bold", "font-size-12")
- scope: Where it applies ("run", "paragraph", "section", "document", "image")
- props: Normalized style properties that map to python-docx API

The registry supports:
- Parametric utilities (e.g., font-size-{N}, color-{RRGGBB})
- Boolean flags (e.g., bold, italic)
- Complex utilities (e.g., layout-col-2, section-margin-all-1in)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Any
import re

Scope = Literal["run", "paragraph", "section", "document", "image", "break", "row", "cell"]


@dataclass(frozen=True)
class UtilityDef:
    """
    Definition of a single utility class.

    Attributes:
        name: The utility pattern (may contain {N}, {RRGGBB}, etc. placeholders)
        scope: Where this utility applies
        props: Normalized property dict that maps to python-docx
        description: Human-readable description
        pattern: Optional regex pattern for parametric utilities
    """

    name: str
    scope: Scope
    props: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    pattern: Optional[str] = None

    def matches(self, utility_name: str) -> Optional[Dict[str, Any]]:
        r"""
        Check if a utility name matches this definition.

        Returns:
            Matched parameters as a dict, or None if no match

        Examples:
            >>> util = UtilityDef("font-size-{N}", "run", pattern=r"font-size-(\d+)")
            >>> util.matches("font-size-12")
            {'N': '12'}
        """
        if self.pattern:
            match = re.fullmatch(self.pattern, utility_name)
            if match:
                return match.groupdict() if match.lastindex else {}
            return None
        else:
            # Exact match
            return {} if utility_name == self.name else None


# ============================================================================
# UTILITY REGISTRY
# ============================================================================

# We'll build this incrementally using utility definition functions
_UTILITY_DEFS: List[UtilityDef] = []


def register_utility(util: UtilityDef):
    """Register a utility definition."""
    _UTILITY_DEFS.append(util)


def register_pattern_utility(
    pattern: str,
    scope: Scope,
    regex: str,
    prop_builder: callable,
    description: str = "",
):
    r"""
    Register a parametric utility with a pattern.

    Args:
        pattern: Display pattern (e.g., "font-size-{N}")
        scope: Utility scope
        regex: Regex pattern with named groups
        prop_builder: Function that takes match dict and returns props
        description: Human-readable description
    """
    # For now, store the prop_builder reference (we'll call it during resolution)
    # We'll handle this more elegantly in the layout_resolver
    util = UtilityDef(
        name=pattern,
        scope=scope,
        pattern=regex,
        description=description,
        props={"_builder": prop_builder},  # Special marker
    )
    register_utility(util)


# ----------------------------------------------------------------------------
# 1. RUN-LEVEL UTILITIES (Inline Text Formatting)
# ----------------------------------------------------------------------------

# 1.1 Font family & size
register_pattern_utility(
    pattern="font-name-{family}",
    scope="run",
    regex=r"font-name-(?P<family>[\w\-]+)",
    prop_builder=lambda m: {"font_name": m["family"].replace("-", " ").title()},
    description="Set font family",
)

register_pattern_utility(
    pattern="font-size-{pt}",
    scope="run",
    regex=r"font-size-(?P<pt>\d+)",
    prop_builder=lambda m: {"size": int(m["pt"])},
    description="Set font size in points",
)

# 1.2 Basic emphasis
for util_name, props in [
    ("bold", {"bold": True}),
    ("no-bold", {"bold": False}),
    ("italic", {"italic": True}),
    ("no-italic", {"italic": False}),
    ("underline", {"underline": True}),
    ("no-underline", {"underline": False}),
    ("strike", {"strike": True}),
    ("double-strike", {"double_strike": True}),
    ("no-strike", {"strike": False, "double_strike": False}),
]:
    register_utility(
        UtilityDef(
            name=util_name,
            scope="run",
            props=props,
            description=f"Text emphasis: {util_name}",
        )
    )

# Underline styles
for style in ["single", "double", "dotted", "wave", "thick"]:
    register_utility(
        UtilityDef(
            name=f"underline-{style}",
            scope="run",
            props={"underline": style},
            description=f"Underline with {style} style",
        )
    )

# 1.3 Case and script
for util_name, props in [
    ("all-caps", {"all_caps": True}),
    ("small-caps", {"small_caps": True}),
    ("no-caps-transform", {"all_caps": False, "small_caps": False}),
    ("superscript", {"superscript": True, "subscript": False}),
    ("subscript", {"subscript": True, "superscript": False}),
    ("no-script", {"superscript": False, "subscript": False}),
]:
    register_utility(
        UtilityDef(
            name=util_name,
            scope="run",
            props=props,
            description=f"Text transform: {util_name}",
        )
    )

# 1.4 Font color
register_pattern_utility(
    pattern="color-{RRGGBB}",
    scope="run",
    regex=r"color-(?P<hex>[0-9A-Fa-f]{6})",
    prop_builder=lambda m: {"color": m["hex"].upper()},
    description="Set text color (hex RGB)",
)

# Highlight colors
HIGHLIGHT_COLORS = [
    "yellow", "green", "cyan", "magenta", "blue", "red",
    "dark-blue", "dark-cyan", "dark-green", "dark-magenta",
    "dark-red", "dark-yellow", "dark-gray", "light-gray", "black", "none"
]
for color in HIGHLIGHT_COLORS:
    register_utility(
        UtilityDef(
            name=f"highlight-{color}",
            scope="run",
            props={"highlight": color},
            description=f"Highlight with {color}",
        )
    )

# 1.5 Advanced run properties
for util_name, props in [
    ("hidden", {"hidden": True}),
    ("no-hidden", {"hidden": False}),
    ("outline", {"outline": True}),
    ("no-outline", {"outline": False}),
    ("shadow", {"shadow": True}),
    ("no-shadow", {"shadow": False}),
    ("emboss", {"emboss": True}),
    ("no-emboss", {"emboss": False}),
    ("imprint", {"imprint": True}),
    ("no-imprint", {"imprint": False}),
]:
    register_utility(
        UtilityDef(
            name=util_name,
            scope="run",
            props=props,
            description=f"Advanced run property: {util_name}",
        )
    )

# ----------------------------------------------------------------------------
# 2. PARAGRAPH-LEVEL UTILITIES
# ----------------------------------------------------------------------------

# 2.1 Alignment
for align in ["left", "right", "center", "justify", "distribute"]:
    register_utility(
        UtilityDef(
            name=f"align-{align}",
            scope="paragraph",
            props={"alignment": align},
            description=f"Align paragraph {align}",
        )
    )

# 2.2 Indentation
register_pattern_utility(
    pattern="indent-left-{N}pt",
    scope="paragraph",
    regex=r"indent-left-(?P<pt>\d+)pt",
    prop_builder=lambda m: {"left_indent": int(m["pt"])},
    description="Left indentation in points",
)

register_pattern_utility(
    pattern="indent-right-{N}pt",
    scope="paragraph",
    regex=r"indent-right-(?P<pt>\d+)pt",
    prop_builder=lambda m: {"right_indent": int(m["pt"])},
    description="Right indentation in points",
)

register_pattern_utility(
    pattern="indent-first-line-{N}pt",
    scope="paragraph",
    regex=r"indent-first-line-(?P<pt>-?\d+)pt",
    prop_builder=lambda m: {"first_line_indent": int(m["pt"])},
    description="First line indentation in points (negative for hanging)",
)

register_pattern_utility(
    pattern="indent-hanging-{N}pt",
    scope="paragraph",
    regex=r"indent-hanging-(?P<pt>\d+)pt",
    prop_builder=lambda m: {
        "left_indent": int(m["pt"]),
        "first_line_indent": -int(m["pt"]),
    },
    description="Hanging indent (shorthand)",
)

# 2.3 Spacing
register_pattern_utility(
    pattern="space-before-{N}pt",
    scope="paragraph",
    regex=r"space-before-(?P<pt>\d+)pt",
    prop_builder=lambda m: {"space_before": int(m["pt"])},
    description="Space before paragraph in points",
)

register_pattern_utility(
    pattern="space-after-{N}pt",
    scope="paragraph",
    regex=r"space-after-(?P<pt>\d+)pt",
    prop_builder=lambda m: {"space_after": int(m["pt"])},
    description="Space after paragraph in points",
)

# Line spacing multiples
for mult_name, mult_val in [("1_0", 1.0), ("1_5", 1.5), ("2_0", 2.0)]:
    register_utility(
        UtilityDef(
            name=f"line-spacing-{mult_name}",
            scope="paragraph",
            props={"line_spacing": mult_val},
            description=f"Line spacing: {mult_val}x",
        )
    )

register_pattern_utility(
    pattern="line-spacing-pt-{N}",
    scope="paragraph",
    regex=r"line-spacing-pt-(?P<pt>\d+)",
    prop_builder=lambda m: {"line_spacing_pt": int(m["pt"])},
    description="Line spacing in exact points",
)

# 2.4 Pagination behavior
for util_name, props in [
    ("keep-together", {"keep_together": True}),
    ("no-keep-together", {"keep_together": False}),
    ("keep-with-next", {"keep_with_next": True}),
    ("no-keep-with-next", {"keep_with_next": False}),
    ("page-break-before", {"page_break_before": True}),
    ("no-page-break-before", {"page_break_before": False}),
    ("widow-control-on", {"widow_control": True}),
    ("widow-control-off", {"widow_control": False}),
]:
    register_utility(
        UtilityDef(
            name=util_name,
            scope="paragraph",
            props=props,
            description=f"Pagination: {util_name}",
        )
    )

# 2.5 Paragraph style
register_pattern_utility(
    pattern="para-style-{slug}",
    scope="paragraph",
    regex=r"para-style-(?P<slug>[\w\-]+)",
    prop_builder=lambda m: {"style_id": m["slug"]},
    description="Apply named paragraph style",
)

# ----------------------------------------------------------------------------
# 3. BREAK UTILITIES
# ----------------------------------------------------------------------------

for break_type in ["page-break", "line-break", "column-break"]:
    register_utility(
        UtilityDef(
            name=break_type,
            scope="break",
            props={"break_type": break_type.split("-")[0]},  # "page", "line", "column"
            description=f"Insert {break_type.replace('-', ' ')}",
        )
    )

# ----------------------------------------------------------------------------
# 4. SECTION & PAGE LAYOUT UTILITIES
# ----------------------------------------------------------------------------

# 4.1 Page orientation
for orient in ["portrait", "landscape"]:
    register_utility(
        UtilityDef(
            name=f"section-orientation-{orient}",
            scope="section",
            props={"orientation": orient},
            description=f"Set page orientation to {orient}",
        )
    )

# 4.2 Page size presets
PAGE_SIZES = {
    "letter": (8.5, 11),  # inches
    "legal": (8.5, 14),
    "a4": (8.27, 11.69),  # 210mm x 297mm
}
for size_name, (width, height) in PAGE_SIZES.items():
    register_utility(
        UtilityDef(
            name=f"section-size-{size_name}",
            scope="section",
            props={"page_width": width, "page_height": height},
            description=f"Set page size to {size_name}",
        )
    )

# 4.3 Margins
register_pattern_utility(
    pattern="section-margin-all-{N}in",
    scope="section",
    regex=r"section-margin-all-(?P<inches>\d+(?:_\d+)?)in",
    prop_builder=lambda m: {
        "margin_left": float(m["inches"].replace("_", ".")),
        "margin_right": float(m["inches"].replace("_", ".")),
        "margin_top": float(m["inches"].replace("_", ".")),
        "margin_bottom": float(m["inches"].replace("_", ".")),
    },
    description="Set all margins (in inches)",
)

for side in ["left", "right", "top", "bottom"]:
    register_pattern_utility(
        pattern=f"section-margin-{side}-{{N}}in",
        scope="section",
        regex=rf"section-margin-{side}-(?P<inches>\d+(?:_\d+)?)in",
        prop_builder=lambda m, s=side: {f"margin_{s}": float(m["inches"].replace("_", "."))},
        description=f"Set {side} margin (in inches)",
    )

# 4.4 Columns
for col_count in [1, 2, 3]:
    register_utility(
        UtilityDef(
            name=f"layout-col-{col_count}",
            scope="section",
            props={"columns": col_count},
            description=f"Set {col_count}-column layout",
        )
    )

# ----------------------------------------------------------------------------
# 5. LIST UTILITIES
# ----------------------------------------------------------------------------

# List types
for list_type in ["bullet", "number"]:
    register_utility(
        UtilityDef(
            name=f"list-{list_type}",
            scope="paragraph",
            props={"list_type": list_type},
            description=f"Apply {list_type} list style",
        )
    )

# List levels
for level in range(1, 10):
    register_utility(
        UtilityDef(
            name=f"list-level-{level}",
            scope="paragraph",
            props={"list_level": level},
            description=f"Set list level to {level}",
        )
    )

register_utility(
    UtilityDef(
        name="list-restart",
        scope="paragraph",
        props={"list_restart": True},
        description="Restart list numbering",
    )
)

# ----------------------------------------------------------------------------
# 6. STYLE UTILITIES
# ----------------------------------------------------------------------------

register_pattern_utility(
    pattern="char-style-{slug}",
    scope="run",
    regex=r"char-style-(?P<slug>[\w\-]+)",
    prop_builder=lambda m: {"character_style": m["slug"]},
    description="Apply named character style",
)

# ----------------------------------------------------------------------------
# 7. IMAGE UTILITIES
# ----------------------------------------------------------------------------

register_pattern_utility(
    pattern="image-id-{key}",
    scope="image",
    regex=r"image-id-(?P<key>[\w\-]+)",
    prop_builder=lambda m: {"image_id": m["key"]},
    description="Reference image by ID",
)

register_pattern_utility(
    pattern="image-width-{N}in",
    scope="image",
    regex=r"image-width-(?P<inches>\d+(?:_\d+)?)in",
    prop_builder=lambda m: {"image_width": float(m["inches"].replace("_", "."))},
    description="Set image width (in inches)",
)

register_pattern_utility(
    pattern="image-height-{N}in",
    scope="image",
    regex=r"image-height-(?P<inches>\d+(?:_\d+)?)in",
    prop_builder=lambda m: {"image_height": float(m["inches"].replace("_", "."))},
    description="Set image height (in inches)",
)

register_pattern_utility(
    pattern="image-align-{alignment}",
    scope="image",
    regex=r"image-align-(?P<alignment>left|center|right)",
    prop_builder=lambda m: {"image_alignment": m["alignment"]},
    description="Set image alignment (left, center, or right)",
)

register_utility(
    UtilityDef(
        name="image-caption-below",
        scope="image",
        props={"image_caption": True},
        description="Add caption below image",
    )
)

register_pattern_utility(
    pattern="image-path-{path}",
    scope="image",
    regex=r"image-path-(?P<path>[\w\-_/\\.]+)",
    prop_builder=lambda m: {"image_path": m["path"]},
    description="Reference image by file path",
)

register_pattern_utility(
    pattern="image-alt-{text}",
    scope="image",
    regex=r"image-alt-(?P<text>[\w\-_\s]+)",
    prop_builder=lambda m: {"alt_text": m["text"].replace("-", " ")},
    description="Set image alt text",
)

# ----------------------------------------------------------------------------
# 8. ROW LAYOUT UTILITIES
# ----------------------------------------------------------------------------

# Row structure
register_pattern_utility(
    pattern="row-cols-{N}",
    scope="row",
    regex=r"row-cols-(?P<cols>\d+)",
    prop_builder=lambda m: {"cols": int(m["cols"])},
    description="Set number of columns in row",
)

# Row widths (percentages or ratios)
register_pattern_utility(
    pattern="row-widths-{values}",
    scope="row",
    regex=r"row-widths-(?P<values>[\d\-]+)",
    prop_builder=lambda m: {
        "widths": [int(v) for v in m["values"].split("-")],
        "width_mode": "auto",  # Will be determined by schema_converter
    },
    description="Set column widths (percentages or ratios)",
)

# Row width (percent of available width)
register_pattern_utility(
    pattern="row-width-{N}",
    scope="row",
    regex=r"row-width-(?P<pct>\d+)",
    prop_builder=lambda m: {"total_width": int(m["pct"])},
    description="Set row width as percentage of available width",
)

# Row alignment
for align in ["left", "center", "right"]:
    register_utility(
        UtilityDef(
            name=f"row-align-{align}",
            scope="row",
            props={"alignment": align},
            description=f"Align row {align}",
        )
    )

# Row indent
register_pattern_utility(
    pattern="row-indent-{N}",
    scope="row",
    regex=r"row-indent-(?P<inches>\d+(?:_\d+)?)",
    prop_builder=lambda m: {"indent": float(m["inches"].replace("_", "."))},
    description="Set row indent from left margin (inches)",
)

# Row layout mode
for mode in ["fixed", "auto"]:
    register_utility(
        UtilityDef(
            name=f"row-layout-{mode}",
            scope="row",
            props={"width_mode": mode},
            description=f"Set row width mode to {mode}",
        )
    )

# Row spacing
register_pattern_utility(
    pattern="row-space-before-{N}",
    scope="row",
    regex=r"row-space-before-(?P<pt>\d+)",
    prop_builder=lambda m: {"space_before": int(m["pt"])},
    description="Set space before row (points)",
)

register_pattern_utility(
    pattern="row-space-after-{N}",
    scope="row",
    regex=r"row-space-after-(?P<pt>\d+)",
    prop_builder=lambda m: {"space_after": int(m["pt"])},
    description="Set space after row (points)",
)

# Row keep properties
register_utility(
    UtilityDef(
        name="row-keep-with-next",
        scope="row",
        props={"keep_with_next": True},
        description="Keep row with next block",
    )
)

register_utility(
    UtilityDef(
        name="row-keep-together",
        scope="row",
        props={"keep_together": True},
        description="Keep row content together",
    )
)

# Cell default padding
register_pattern_utility(
    pattern="cell-pad-{N}",
    scope="row",
    regex=r"cell-pad-(?P<inches>\d+(?:_\d+)?)",
    prop_builder=lambda m: {"default_cell_padding": float(m["inches"].replace("_", "."))},
    description="Set default cell padding (inches)",
)

# Visual gap between cells
register_pattern_utility(
    pattern="gap-{N}",
    scope="row",
    regex=r"gap-(?P<inches>\d+(?:_\d+)?)",
    prop_builder=lambda m: {"cell_gap": float(m["inches"].replace("_", "."))},
    description="Set visual gap between cells (inches)",
)

# Row borders
for border_mode in ["none", "debug"]:
    register_utility(
        UtilityDef(
            name=f"row-border-{border_mode}",
            scope="row",
            props={"borders": border_mode},
            description=f"Set row border mode to {border_mode}",
        )
    )

# ----------------------------------------------------------------------------
# 9. CELL UTILITIES
# ----------------------------------------------------------------------------

# Cell alignment (paragraph alignment within cell)
for align in ["left", "center", "right", "justify"]:
    register_utility(
        UtilityDef(
            name=f"cell-align-{align}",
            scope="cell",
            props={"align": align},
            description=f"Align cell content {align}",
        )
    )

# Cell vertical alignment
for valign in ["top", "middle", "bottom"]:
    register_utility(
        UtilityDef(
            name=f"cell-valign-{valign}",
            scope="cell",
            props={"valign": valign},
            description=f"Vertically align cell content to {valign}",
        )
    )

# Cell padding (all sides)
register_pattern_utility(
    pattern="cell-pad-{N}",
    scope="cell",
    regex=r"cell-pad-(?P<inches>\d+(?:_\d+)?)",
    prop_builder=lambda m: {
        "padding": {
            "top": float(m["inches"].replace("_", ".")),
            "bottom": float(m["inches"].replace("_", ".")),
            "left": float(m["inches"].replace("_", ".")),
            "right": float(m["inches"].replace("_", ".")),
        }
    },
    description="Set cell padding all sides (inches)",
)

# Cell padding (specific sides)
for side in ["top", "bottom", "left", "right"]:
    register_pattern_utility(
        pattern=f"cell-pad-{side}-{{N}}",
        scope="cell",
        regex=rf"cell-pad-{side}-(?P<inches>\d+(?:_\d+)?)",
        prop_builder=lambda m, s=side: {
            "padding": {s: float(m["inches"].replace("_", "."))}
        },
        description=f"Set cell padding on {side} (inches)",
    )

# Cell width override
register_pattern_utility(
    pattern="cell-width-{N}",
    scope="cell",
    regex=r"cell-width-(?P<pct>\d+)",
    prop_builder=lambda m: {"width_override": int(m["pct"])},
    description="Override cell width (percentage)",
)

# Cell text wrapping
register_utility(
    UtilityDef(
        name="cell-nowrap",
        scope="cell",
        props={"nowrap": True},
        description="Disable text wrapping in cell",
    )
)

# ============================================================================
# REGISTRY ACCESS FUNCTIONS
# ============================================================================

# Build a lookup dict for fast exact matches
_EXACT_MATCH_REGISTRY: Dict[str, UtilityDef] = {}
_PATTERN_MATCH_REGISTRY: List[UtilityDef] = []

for util in _UTILITY_DEFS:
    if util.pattern:
        _PATTERN_MATCH_REGISTRY.append(util)
    else:
        _EXACT_MATCH_REGISTRY[util.name] = util

# Export as UTILITY_REGISTRY for backward compatibility
UTILITY_REGISTRY = _EXACT_MATCH_REGISTRY


def get_utility(name: str) -> Optional[UtilityDef]:
    """
    Get utility definition by name.

    Supports both exact and pattern matching.

    Args:
        name: Utility name (e.g., "bold", "font-size-12")

    Returns:
        UtilityDef if found, None otherwise
    """
    # Try exact match first
    if name in _EXACT_MATCH_REGISTRY:
        return _EXACT_MATCH_REGISTRY[name]

    # Try pattern match
    for util in _PATTERN_MATCH_REGISTRY:
        if util.matches(name):
            return util

    return None


def get_utilities_by_scope(scope: Scope) -> List[UtilityDef]:
    """
    Get all utilities for a given scope.

    Args:
        scope: The scope to filter by

    Returns:
        List of UtilityDef objects
    """
    return [util for util in _UTILITY_DEFS if util.scope == scope]
