from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from glyph.core.analysis.detectors.semantic_classifier import SemanticPrediction
from glyph.core.analysis.forms.headings import HeadingForm
from glyph.core.analysis.forms.paragraphs import ParagraphForm
from glyph.core.analysis.detectors.heuristics.paragraph_detector import ParagraphDetection
from glyph.core.analysis.detectors.heuristics.heading_detector import HeadingDetection
from glyph.core.analysis.detectors.heuristics.list_detector import ListDetection
from glyph.core.analysis.detectors.heuristics.table_detector import TableDetection
from glyph.core.analysis.detectors.heuristics.callouts import CalloutDetection
from glyph.core.analysis.detectors.regex_maker import RegexDetection


@dataclass
class PatternDescriptor:
    """Unified representation of detection results (Axis-1 classification)."""
    type: str = "UNKNOWN"                 # Axis-1 code (H-SHORT, L-BULLET, etc.)
    text: str = ""                        # Raw line text
    signals: List[str] = None             # How it was detected
    score: float = 0.0                    # Confidence/score
    features: Dict[str, Any] = None       # Extra properties (line_idx, regex, etc.)
    style: Dict[str, Any] = None          # DOCX style overrides
    method: str = "heuristic"             # Detection method
    paragraph_id: Optional[str] = None    # Link back to schema paragraph
    id: str = ""                          # Unique id

    def __post_init__(self):
        if self.signals is None:
            self.signals = []
        if self.features is None:
            self.features = {}
        if self.style is None:
            self.style = {}
        if not self.id:
            self.id = f"pat_{id(self)}"

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "paragraph_id": self.paragraph_id,
            "type": self.type,
            "features": self.features,
            "score": self.score,
            "method": self.method,
            "style": self.style,
            "signals": self.signals,
        }
        # Include regex if present (for plaintext pattern matching)
        if hasattr(self, 'regex') and self.regex:
            result["regex"] = self.regex
        # Include table_id if present
        if hasattr(self, 'table_id') and self.table_id:
            result["table_id"] = self.table_id
        return result

def coerce_to_descriptor(raw: Any, signal: str = "GENERIC", text: str = "", features: dict | None = None) -> PatternDescriptor:
    """Normalize detector outputs into a PatternDescriptor."""
    # Already normalized
    if isinstance(raw, PatternDescriptor):
        return raw

    # String labels (regex/exact)
    if isinstance(raw, str):
        return PatternDescriptor(type=raw, text=text, signals=[signal], score=1.0, features=features or {})

    # Dict
    if isinstance(raw, dict):
        return PatternDescriptor(
            type=raw.get("type") or raw.get("class") or raw.get("label", "UNKNOWN"),
            text=text,
            signals=[signal],
            score=raw.get("score", raw.get("confidence", 0.0)),
            features=raw.get("features", features or {}),
            style=raw.get("style", {}),
            method=raw.get("method", "heuristic"),
        )

    # List of strings
    if isinstance(raw, list) and raw and all(isinstance(r, str) for r in raw):
        return coerce_to_descriptor(raw[0], signal=signal, text=text, features=features)

    # Heuristic dataclasses
    if isinstance(raw, (ParagraphDetection, HeadingDetection, ListDetection, TableDetection, CalloutDetection)):
        return PatternDescriptor(
            type=raw.label,
            text=text,
            signals=[signal],
            score=getattr(raw, "score", 0.0),
            features={**(features or {}), "line_idx": getattr(raw, "line_idx", None)},
            method=getattr(raw, "method", "heuristic"),
        )

    # Semantic prediction
    if isinstance(raw, SemanticPrediction):
        return PatternDescriptor(
            type=getattr(raw, "label", "P-BODY"),
            text=text,
            signals=["SEMANTIC"],
            score=raw.score,
            features={"title": getattr(raw, "title", None)},
            style={"pStyle": "Normal"},
            method="semantic",
        )

    # Regex detection
    if isinstance(raw, RegexDetection):
        return PatternDescriptor(
            type=raw.label,
            text=text,
            signals=[signal],
            score=raw.score,
            features={"pattern": raw.pattern},
            method=raw.method,
        )

    # List of semantic or heuristic dataclasses → take best
    if isinstance(raw, list) and raw:
        best = max(raw, key=lambda p: getattr(p, "score", 0.0))
        return coerce_to_descriptor(best, signal=signal, text=text, features=features)

    # Enums (heading/paragraph forms)
    if isinstance(raw, HeadingForm):
        return PatternDescriptor(type=raw.value, text=text, signals=[signal], score=0.9, style={"pStyle": "Heading1"})
    if isinstance(raw, ParagraphForm):
        return PatternDescriptor(type=raw.value, text=text, signals=[signal], score=0.8, style={"pStyle": "Normal"})

    # Fallback
    return PatternDescriptor(type="UNKNOWN", text=text or str(raw), signals=[signal], score=0.0, features=features or {})

