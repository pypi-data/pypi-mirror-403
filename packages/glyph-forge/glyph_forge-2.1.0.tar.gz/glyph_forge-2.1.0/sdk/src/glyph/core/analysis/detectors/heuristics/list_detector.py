# src/glyph/core/analysis/detectors/heuristics/list_detector.py
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Sequence, Union, Dict, Any

from glyph.core.analysis.utils.plaintext_context import PlaintextContext
from glyph.core.analysis.detectors.utils import coerce_to_lines, normalize_line


@dataclass(frozen=True)
class ListDetection:
    line_idx: int
    label: str   # now subtype, not just "list"
    score: float = 0.0
    method: str = "heuristic"


# ---------- Regex patterns for heuristics ----------
BULLET_RE = re.compile(r"^\s*([\-–—•▪◦●·\*■])\s+")
ORDERED_RE = re.compile(r"^\s*((\d+|[a-zA-Z]|[ivxlcdmIVXLCDM]+)([\.\)]))\s+")
ORDERED_NESTED_RE = re.compile(r"^\s*\d+(\.\d+)+\s+")
DEFINITION_RE = re.compile(r"^\s*\w+(?:\s+\w+)*\s*[:—–-]\s+")
INDENTED_RE = re.compile(r"^\s{4,}")  # ≥4 spaces → continuation candidate


def score_list_line(text: str) -> tuple[str, float]:
    """
    Return (label, score) for whether a line is list-like.
    Uses simple regex heuristics with subtype detection for plaintext sources.
    """
    if not text:
        return ("L-UNKNOWN", 0.0)

    raw = text

    # Check bullet on RAW text BEFORE normalization (to preserve bullet type)
    # Pattern for bullet detection on raw text (including 'o')
    raw_bullet_re = re.compile(r"^\s*([\-–—•▪◦●·\*■o])\s+")
    raw_bullet_match = raw_bullet_re.match(raw)
    if raw_bullet_match:
        marker = raw_bullet_match.group(1)
        # Classify bullet type
        solid_bullets = {"•", "●", "·", "-", "–", "—", "*"}
        hollow_bullets = {"◦", "o"}
        square_bullets = {"▪", "■"}

        if marker in solid_bullets:
            return ("L-BULLET-SOLID", 0.9)
        elif marker in hollow_bullets:
            return ("L-BULLET-HOLLOW", 0.9)
        elif marker in square_bullets:
            return ("L-BULLET-SQUARE", 0.9)
        else:
            return ("L-BULLET", 0.9)

    # Normalize for other patterns
    s = normalize_line(text)

    # Ordered - with subtype detection
    ordered_match = ORDERED_RE.match(s)
    if ordered_match:
        full_marker = ordered_match.group(1)  # e.g., "1.", "a)", "I.", "iv)"
        num_part = ordered_match.group(2)     # e.g., "1", "a", "I", "iv"
        suffix = ordered_match.group(3)       # "." or ")"

        # Decimal numbers
        if num_part.isdigit():
            if suffix == ")":
                return ("L-ORDERED-PARA-NUM", 0.9)
            else:
                return ("L-ORDERED-DOTTED", 0.9)

        # Upper Roman (I, II, III, IV, V)
        if num_part.isupper() and all(c in "IVXLCDM" for c in num_part):
            return ("L-ORDERED-ROMAN-UPPER", 0.9)

        # Lower Roman (i, ii, iii, iv, v)
        if num_part.islower() and all(c in "ivxlcdm" for c in num_part):
            return ("L-ORDERED-ROMAN-LOWER", 0.9)

        # Upper letter (A, B, C)
        if len(num_part) == 1 and num_part.isupper() and num_part.isalpha():
            return ("L-ORDERED-ALPHA-UPPER", 0.9)

        # Lower letter (a, b, c) - split by suffix
        if len(num_part) == 1 and num_part.islower() and num_part.isalpha():
            if suffix == ")":
                return ("L-ORDERED-ALPHA-LOWER-PAREN", 0.9)  # a), b), c)
            else:
                return ("L-ORDERED-ALPHA-LOWER-DOT", 0.9)    # a., b., c.

        # Fallback for ordered
        return ("L-ORDERED", 0.9)

    # Nested (1.1, 1.2.3)
    if ORDERED_NESTED_RE.match(s):
        return ("L-ORDERED", 0.9)

    # Definition
    if DEFINITION_RE.match(s):
        return ("L-DEFINITION", 0.8)

    # Continuation (check raw, not normalized)
    if INDENTED_RE.match(raw):
        return ("L-CONTINUATION", 0.6)

    return ("L-UNKNOWN", 0.0)


def detect_lists(
    source: Union[Sequence[str], PlaintextContext],
    features: List[Dict[str, Any]] | None = None,
    threshold: float = 0.55,
) -> List[ListDetection]:
    """
    Detect list-like lines. Returns ListDetection objects
    with Axis-1 subtype labels (L-BULLET, L-ORDERED, etc.).
    """
    lines = coerce_to_lines(source)
    preds: List[ListDetection] = []

    for i, s in enumerate(lines):
        label, sc = score_list_line(s)

        # Feature-based override from DOCX schema
        feats = features[i] if features and i < len(features) else {}
        list_info = feats.get("list") if feats else None
        style_id = feats.get("style_id", "").lower() if feats else ""

        if list_info:
            fmt = list_info.get("format", "").lower()
            lvl_text = list_info.get("lvlText", "")

            # --- classify bullets ---
            if fmt == "bullet":
                if lvl_text in {"\uf0b7", "•"}:
                    label, sc = "L-BULLET-SOLID", 0.95
                elif lvl_text in {"o", "◦"}:
                    label, sc = "L-BULLET-HOLLOW", 0.95
                elif lvl_text in {"\uf0a7", "▪"}:
                    label, sc = "L-BULLET-SQUARE", 0.95
                else:
                    label, sc = "L-BULLET", 0.9

            # --- classify ordered ---
            elif fmt == "decimal":
                if lvl_text.endswith(")"):
                    label, sc = "L-ORDERED-PARA-NUM", 0.95   # 1)
                elif lvl_text.endswith("."):
                    label, sc = "L-ORDERED-DOTTED", 0.95  # 1.
                else:
                    label, sc = "L-ORDERED", 0.9
            elif fmt == "upperroman":
                label, sc = "L-ORDERED-ROMAN-UPPER", 0.95
            elif fmt == "lowerroman":
                label, sc = "L-ORDERED-ROMAN-LOWER", 0.95
            elif fmt == "upperletter":
                label, sc = "L-ORDERED-ALPHA-UPPER", 0.95
            elif fmt == "lowerletter":
                # Differentiate by suffix in lvlText
                if lvl_text.endswith(")"):
                    label, sc = "L-ORDERED-ALPHA-LOWER-PAREN", 0.95  # a), b), c)
                else:
                    label, sc = "L-ORDERED-ALPHA-LOWER-DOT", 0.95    # a., b., c.

            # --- fallback ---
            else:
                label, sc = "L-ORDERED", 0.9

            # Nested levels
            if int(list_info.get("ilvl", 0)) > 0:
                label = f"{label}-NESTED"

        if sc >= threshold:
            preds.append(ListDetection(i, label, sc))
    return preds


def match(lines, features=None, domain=None, threshold: float = 0.55, **kwargs):
    """
    Standardized entrypoint for the router.
    Delegates to the heuristic list detector.
    Accepts either:
      - a single string + dict of features
      - a list of strings + list of feature dicts
    """
    # Normalize single-paragraph input
    if isinstance(lines, str):
        lines = [lines]
        if isinstance(features, dict):
            features = [features]

    return detect_lists(lines, features=features, threshold=threshold)

