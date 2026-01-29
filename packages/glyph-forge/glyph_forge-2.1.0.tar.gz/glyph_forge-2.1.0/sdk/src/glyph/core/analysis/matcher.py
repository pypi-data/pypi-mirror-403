from .detectors import exact_matcher, regex_maker, semantic_classifier
from .detectors.heuristics import (
    heading_detector, list_detector, paragraph_detector, table_detector, callouts,
)
from .utils.pattern_descriptor import coerce_to_descriptor, PatternDescriptor

import logging
logger = logging.getLogger(__name__)

# Central registry of detectors
HEURISTIC_MATCHERS = {
    "heading": heading_detector.match,
    "list": list_detector.match,
    "paragraph": paragraph_detector.match,
    "table": table_detector.match,
    "callout": callouts.match,
}


# ------------------------------
# Helpers
# ------------------------------

def check_feature_shortcuts(text: str, features: dict | None) -> PatternDescriptor | None:
    """Route directly based on obvious feature clues (list, heading, etc.)."""
    if not features:
        return None

    # Explicit DOCX list feature
    if features.get("list"):
        m = list_detector.match(text, features=features)
        if m:
            return coerce_to_descriptor(m, signal="HEURISTIC-LIST", text=text, features=features)

    # Heading style id
    style_id = (features.get("style_id") or "").lower()
    if "heading" in style_id:
        m = heading_detector.match(text, features=features)
        if m:
            return coerce_to_descriptor(m, signal="HEURISTIC-HEADING", text=text, features=features)

    # Explicit DOCX table feature
    if features.get("table"):
        m = table_detector.match(text, features=features)
        if m:
            return coerce_to_descriptor(m, signal="HEURISTIC-TABLE", text=text, features=features)

    return None


def check_title_config(text: str, titles_config: list[str] | None) -> PatternDescriptor | None:
    """Check against exact title candidates."""
    if not titles_config:
        return None
    m = exact_matcher.match(text, candidates=titles_config)
    if m:
        return coerce_to_descriptor(m, signal="EXACT", text=text, features={"text": text})
    return None


def run_heuristics(text: str, features: dict | None) -> PatternDescriptor | None:
    """Run all heuristics, pick the highest scoring match."""
    results = []
    for key, detector in HEURISTIC_MATCHERS.items():
        m = detector(text, features=features)
        if m:
            results.append((m, key))
    if results:
        best, key = max(results, key=lambda tup: getattr(tup[0], "score", 1.0))
        return coerce_to_descriptor(best, signal=f"HEURISTIC-{key.upper()}", text=text, features=features)
    return None


def run_regex(text: str, features: dict | None) -> PatternDescriptor | None:
    """Regex matcher as fallback."""
    m = regex_maker.match(text)
    if m:
        return coerce_to_descriptor(m, signal="REGEX", text=text, features=features)
    return None


def run_semantic(text: str, features: dict | None) -> PatternDescriptor | None:
    """Semantic ML-based matcher as last resort."""
    m = semantic_classifier.match(text, features=features)
    if m:
        return coerce_to_descriptor(m, signal="SEMANTIC", text=text, features=features)
    return None


# ------------------------------
# Main router
# ------------------------------

def route_match(text: str, *, features: dict | None = None, titles_config: list[str] | None = None) -> PatternDescriptor:
    """
    Master router to detectors.
    Simplified API: only needs text + optional features + titles_config.
    """
    logger.debug(f"[ROUTE_MATCH] text='{text[:50]}...'")

    # 1. Feature shortcuts
    desc = check_feature_shortcuts(text, features)
    if desc:
        return desc

    # 2. Exact title config
    desc = check_title_config(text, titles_config)
    if desc:
        return desc

    # 3. Heuristic competition
    desc = run_heuristics(text, features)
    if desc:
        return desc

    # 4. Regex
    desc = run_regex(text, features)
    if desc:
        return desc

    # 5. Semantic
    desc = run_semantic(text, features)
    if desc:
        return desc

    # 6. Fallback
    return PatternDescriptor(
        type="UNKNOWN",
        signals=["FALLBACK"],
        score=0.0,
        features={"text": text},
    )
