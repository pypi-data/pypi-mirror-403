from __future__ import annotations
import re
from enum import Enum
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from glyph.core.analysis.context.context_enricher import ContextWindow


# ----------------- Canonical heading classes -----------------

class HeadingForm(str, Enum):
    """Axis 1 — Subtypes of headings & titles."""
    H_SHORT = "H-SHORT"          # Short headings (≤6 words, title/ALLCAPS)
    H_LONG = "H-LONG"            # Longer headings (≥7 words)
    H_SECTION_N = "H-SECTION-N"  # Numbered/roman section (1., 1.1, II., §)
    H_CONTENTS = "H-CONTENTS"    # Table of contents entry (leaders + page #)
    H_SUBTITLE = "H-SUBTITLE"    # Subtitle / overline (follows a title)


# ----------------- Regex helpers -----------------

_NUMERIC_SECTION_RE = re.compile(r"^\d+(\.\d+)*[.)]?\s+")
_ROMAN_SECTION_RE   = re.compile(r"^[IVXLCDM]+[.)]\s+", re.IGNORECASE)
_TOC_LEADER_RE      = re.compile(r"\.{2,}\s*\d+$")


# ----------------- Heuristic thresholds -----------------

MAX_SHORT_WORDS = 6
MIN_LONG_WORDS  = 7


# ----------------- Rule metadata -----------------

HEADING_RULES: Dict[HeadingForm, Dict[str, Any]] = {
    HeadingForm.H_SHORT: {
        "max_words": MAX_SHORT_WORDS,
        "casing": "title_or_allcaps",
    },
    HeadingForm.H_LONG: {
        "min_words": MIN_LONG_WORDS,
    },
    HeadingForm.H_SECTION_N: {
        "regex": [_NUMERIC_SECTION_RE, _ROMAN_SECTION_RE],
    },
    HeadingForm.H_CONTENTS: {
        "regex": [_TOC_LEADER_RE],
    },
    HeadingForm.H_SUBTITLE: {
        "position": "after_title",  # handled at aggregation stage
    },
}


# ----------------- Public helper -----------------

def guess_heading_form(text: str) -> Optional[HeadingForm]:
    """
    Roughly assign a heading form subtype (Axis 1) based on simple rules.
    Detectors (heuristic/regex/semantic) should call this to propose a form.
    """
    if not text:
        return None

    # Normalize whitespace
    s = " ".join(text.split())

    # 1. TOC entries
    if _TOC_LEADER_RE.search(s):
        return HeadingForm.H_CONTENTS

    # 2. Numbered / roman section headings
    if _NUMERIC_SECTION_RE.match(s) or _ROMAN_SECTION_RE.match(s):
        return HeadingForm.H_SECTION_N

    # 3. Word count split for short vs long
    word_count = len(s.split())
    if word_count <= MAX_SHORT_WORDS:
        return HeadingForm.H_SHORT
    if word_count >= MIN_LONG_WORDS:
        return HeadingForm.H_LONG

    return None


def detect_subtitle_context(
    text: str,
    current_type: str,
    context: "ContextWindow",
    style: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Determine if element is a subtitle based on context.

    This function uses contextual signals to detect if a heading-like element
    is actually a subtitle (subordinate heading that follows a main title).

    Args:
        text: The text content of the element
        current_type: Current pattern type (e.g., "H-SHORT", "H-LONG", "H-SECTION-N")
        context: ContextWindow with neighbor and hierarchical information
        style: Optional style metadata (DOCX-specific)

    Returns:
        True if element should be classified as H-SUBTITLE

    Signals used:
    - Follows H-SHORT/H-SECTION-N/H-LONG within context window
    - Smaller font size than previous heading (DOCX) OR different style
    - Still has heading-like properties (bold, short, title case)
    - Precedes body content (paragraph/list)
    """
    # Must start as heading candidate
    if current_type not in ["H-SHORT", "H-LONG", "H-SECTION-N"]:
        return False

    # NEVER mark TOC entries as subtitles
    if current_type == "H-CONTENTS":
        return False

    # Must follow another heading
    if not context.follows_title:
        return False

    # If we have style metadata (DOCX), use style-based detection
    if style:
        return _is_subtitle_docx(text, current_type, context, style)

    # Otherwise use plaintext pattern-based detection
    return _is_subtitle_plaintext(text, current_type, context)


def _is_subtitle_docx(
    text: str,
    current_type: str,
    context: "ContextWindow",
    style: Dict[str, Any]
) -> bool:
    """
    Subtitle detection for DOCX using style signals.

    DOCX has rich style metadata available for comparison.
    """
    if not context.prev_descriptors:
        return False

    prev = context.prev_descriptors[-1]  # Most recent previous

    # Get font sizes for comparison
    prev_size = prev.get("style", {}).get("font", {}).get("size", 12)
    curr_size = style.get("font", {}).get("size", 12)

    # Strong signal: Smaller font than previous heading
    if curr_size < prev_size:
        return True

    # Subtitle shouldn't be larger than the title it follows
    if curr_size > prev_size:
        return False

    # Check for same-level headings (should NOT be subtitle)
    prev_style_id = prev.get("style", {}).get("style_id", "")
    curr_style_id = style.get("style_id", "")

    # If font size exactly matches AND style_id matches, likely same level
    if curr_size == prev_size and prev_style_id and curr_style_id:
        if prev_style_id == curr_style_id:
            # Same style = same level (NOT subtitle)
            return False

    # Alternative signal: Different style_id but still bold
    if prev_style_id and curr_style_id and prev_style_id != curr_style_id:
        # Check if both are bold (style consistency)
        prev_bold = prev.get("style", {}).get("font", {}).get("bold", False)
        curr_bold = style.get("font", {}).get("bold", False)

        if prev_bold and curr_bold:
            return True

    # Weak signal: Next element is body content and sizes are equal
    if context.precedes_content and curr_size <= prev_size:
        return True

    return False


def _is_subtitle_plaintext(
    text: str,
    current_type: str,
    context: "ContextWindow"
) -> bool:
    """
    Subtitle detection for plaintext - more conservative.

    Without style metadata, we rely on:
    1. Pattern sequence (H-SHORT follows H-SHORT/H-SECTION-N)
    2. Text length heuristics
    3. Casing patterns
    """
    if not context.prev_descriptors:
        return False

    prev = context.prev_descriptors[-1]  # Most recent previous
    # Support both direct text field and features.text field
    prev_text = prev.get("text", "")
    if not prev_text and "features" in prev:
        prev_text = prev["features"].get("text", "")

    # STRONG SIGNAL: Previous was ALL CAPS, current is Title Case
    # Example:
    #   PROFESSIONAL EXPERIENCE    <- H-SHORT (ALL CAPS)
    #   Senior Engineer            <- H-SUBTITLE (Title Case)
    if prev_text.isupper() and not text.isupper():
        if _is_title_case(text):
            return True

    # MEDIUM SIGNAL: Current line is notably shorter + precedes body
    if context.precedes_content:
        curr_len = len(text)
        prev_len = len(prev_text)
        if prev_len > 0 and curr_len < prev_len * 0.7:  # 30% shorter
            return True

    # WEAK SIGNAL: Numbered section followed by H-SHORT
    # Example:
    #   1. Introduction     <- H-SECTION-N
    #   Background Info     <- Could be H-SUBTITLE
    prev_type = prev.get("type", "")
    if prev_type == "H-SECTION-N" and current_type == "H-SHORT":
        return True

    return False


def _is_title_case(text: str) -> bool:
    """Check if text is in Title Case."""
    words = text.split()
    if not words:
        return False
    # First word capitalized, others may be lowercase/capitalized
    return words[0][0].isupper() if words[0] else False
