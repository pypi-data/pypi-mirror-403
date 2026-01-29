# src/glyph/core/analysis/plaintext/classifier.py

"""Plaintext line-level classifier with context awareness."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any

from glyph.core.analysis.matcher import route_match
from glyph.core.analysis.context.context_enricher import ContextEnricher
from glyph.core.analysis.context.heading_enricher import plaintext_heading_enricher
from glyph.core.analysis.forms.headings import detect_subtitle_context, HeadingForm


@dataclass
class PlaintextLineClassification:
    """Classification result for a single plaintext line."""

    line_index: int
    text: str
    pattern_type: str
    signals: List[str]
    score: float
    method: str = "heuristic"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "line_index": self.line_index,
            "text": self.text,
            "type": self.pattern_type,
            "signals": self.signals,
            "score": self.score,
            "method": self.method,
        }


def classify_lines(
    lines: List[str],
    *,
    use_context: bool = True,
    window_size: int = 2
) -> List[PlaintextLineClassification]:
    """
    Classify plaintext lines with optional context awareness.

    This function performs line-level classification similar to DOCX schema building,
    but for plaintext where we don't have style metadata.

    Args:
        lines: List of text lines to classify
        use_context: If True, apply context-aware refinements (e.g., subtitle detection)
        window_size: Context window size for enrichment

    Returns:
        List of PlaintextLineClassification objects

    Example:
        >>> lines = ["PROFESSIONAL EXPERIENCE", "Senior Engineer", "Led team..."]
        >>> classifications = classify_lines(lines)
        >>> classifications[0].pattern_type
        'H-SHORT'
        >>> classifications[1].pattern_type  # Detected as subtitle via context
        'H-SUBTITLE'
    """
    if not lines:
        return []

    # Phase 1: Base classification using route_match
    base_classifications = []

    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            base_classifications.append(
                PlaintextLineClassification(
                    line_index=i,
                    text=line,
                    pattern_type="BLANK",
                    signals=["EMPTY"],
                    score=1.0,
                    method="fallback"
                )
            )
            continue

        # Route through matcher (no style features for plaintext)
        desc = route_match(text=line, features=None)

        base_classifications.append(
            PlaintextLineClassification(
                line_index=i,
                text=line,
                pattern_type=desc.type,
                signals=desc.signals,
                score=desc.score,
                method=desc.method
            )
        )

    # Phase 2: Context-aware refinement
    if use_context:
        base_classifications = _refine_with_context(
            base_classifications,
            window_size=window_size
        )

    return base_classifications


def _refine_with_context(
    classifications: List[PlaintextLineClassification],
    window_size: int = 2
) -> List[PlaintextLineClassification]:
    """
    Apply context-aware refinements to classifications.

    Currently focuses on subtitle detection for headings.
    Can be extended for other context-aware classifications.

    Args:
        classifications: List of base classifications
        window_size: Context window size

    Returns:
        Refined list of classifications
    """
    if not classifications:
        return classifications

    # Convert to dict format for context enricher
    descriptors = [c.to_dict() for c in classifications]

    # Initialize context enricher with plaintext heading enricher
    enricher = ContextEnricher(window_size=window_size, skip_blank_lines=True)
    enricher.register_enricher(plaintext_heading_enricher)

    # Apply context refinement to each classification
    for i, classification in enumerate(classifications):
        # Build context window for current element
        context = enricher.build_window(i, descriptors, descriptors[i])

        # Check if this is a heading that should be reclassified as subtitle
        current_type = classification.pattern_type
        text = classification.text

        # Apply subtitle detection for heading types (plaintext mode)
        if current_type in ["H-SHORT", "H-LONG", "H-SECTION-N"]:
            is_subtitle = detect_subtitle_context(
                text=text,
                current_type=current_type,
                context=context,
                style=None  # No style = plaintext mode
            )

            if is_subtitle:
                # Reclassify as subtitle
                classification.pattern_type = HeadingForm.H_SUBTITLE.value
                classification.signals.append("CONTEXT-SUBTITLE")

    return classifications
