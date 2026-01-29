from __future__ import annotations

from .intake import intake_plaintext, PlaintextIntakeResult
from .builder import build_emittables_from_plaintext
from .handlers import make_handlers_from_settings
from .classifier import classify_lines, PlaintextLineClassification

__all__ = [
    "intake_plaintext",
    "PlaintextIntakeResult",
    "build_emittables_from_plaintext",
    "make_handlers_from_settings",
    "classify_lines",
    "PlaintextLineClassification",
]
