# src/glyph/core/analysis/detectors/heuristics/table_detector.py
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Sequence, Union, Dict, Any

from glyph.core.analysis.utils.plaintext_context import PlaintextContext
from glyph.core.analysis.detectors.utils import coerce_to_lines, normalize_line
from glyph.core.analysis.forms.tables import TableForm, guess_table_form


@dataclass(frozen=True)
class TableDetection:
    line_idx: int
    label: str
    score: float
    method: str = "heuristic"
    form: TableForm | None = None
    clean_text: str | None = None


# ---------- Regex helpers ----------
PIPE_RE = re.compile(r"\|")
DELIM_RE = re.compile(r"[;,\t]")
GRID_BORDER_RE = re.compile(r"^[\+\-\|\=]+$")  # ASCII table lines


def score_table_line(text: str, *, debug: bool = False) -> float:
    """
    Score how table/grid-like a line is. Returns 0..1.
    """
    s = normalize_line(text or "")
    if not s:
        return 0.0

    score = 0.0
    logs = []

    tokens = s.split()
    num_tokens = len(tokens)

    # Positive: many tokens (columns)
    if num_tokens >= 4:
        score += 0.8; logs.append(("multi_column", +0.8))

    # Positive: delimiters (pipes, commas, tabs, semicolons)
    if PIPE_RE.search(s) or DELIM_RE.search(s):
        score += 0.3; logs.append(("delimiter", +0.3))

    # Positive: mostly digits
    digit_ratio = sum(c.isdigit() for c in s) / max(1, len(s))
    if digit_ratio > 0.3:
        score += 0.3; logs.append(("digit_ratio", +0.3))

    # Positive: ASCII borders
    if GRID_BORDER_RE.match(s):
        score += 0.9; logs.append(("grid_border", +0.9))

    # Negative: stopwords (likely prose, not table)
    if any(stop in s.lower().split() for stop in {"the", "is", "and", "of", "in"}):
        score -= 0.3; logs.append(("stopwords", -0.3))

    final = max(0.0, min(1.0, score))

    if debug:
        print(f"[Table scoring] {text!r} → {final:.3f}")
        for name, delta in logs:
            print(f"  - {name}: {delta:+.2f}")

    return final


def detect_tables(
    source: Union[Sequence[str], PlaintextContext],
    threshold: float = 0.55,
) -> List[TableDetection]:
    """
    Run heuristics to detect table-like lines and classify their form.
    (Used for plaintext-based detection only.)
    """
    lines = coerce_to_lines(source)
    preds: List[TableDetection] = []

    for i, s in enumerate(lines):
        sc = score_table_line(s)
        if sc >= threshold:
            form = guess_table_form(s)
            label = form.value if form else TableForm.T_ROW.value
            preds.append(
                TableDetection(
                    line_idx=i,
                    label=label,
                    score=sc,
                    form=form,
                    clean_text=s.strip(),
                )
            )

    return preds


def match(
    lines: Union[str, Sequence[str]],
    features: Dict[str, Any] | None = None,
    domain=None,
    threshold: float = 0.55,
    **kwargs,
):
    """
    Standardized entrypoint for the router.
    For DOCX tables → short-circuit to TableForm.TABLE.
    For plaintext → fall back to heuristic detection.
    """
    # --- DOCX feature-based detection ---
    if features and features.get("table"):
        return TableDetection(
            line_idx=0,
            label=TableForm.TABLE.value,
            score=1.0,
            method="docx-feature",
            form=TableForm.TABLE,
            clean_text="[TABLE]",
        )

    # --- Plaintext heuristic detection ---
    return detect_tables(lines, threshold=threshold)
