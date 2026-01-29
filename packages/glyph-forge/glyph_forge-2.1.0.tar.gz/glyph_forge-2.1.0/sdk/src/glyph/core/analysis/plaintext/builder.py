from __future__ import annotations
from typing import List, Dict, Any
from glyph.settings import get_settings
from .handlers import make_handlers_from_settings

def build_emittables_from_plaintext(lines: List[str], settings=None) -> List[Dict[str, Any]]:
    S = settings or get_settings()
    handlers = make_handlers_from_settings(S)

    out: List[Dict[str, Any]] = []
    i = 0
    while i < len(lines):
        consumed = False
        for h in handlers:
            if h.can_start(lines, i):
                block, j = h.consume(lines, i)
                out.append({"kind": "block", "block": block})
                i = j + 1
                consumed = True
                break
        if consumed: 
            continue
        ln = lines[i]
        if ln.strip():
            out.append({"kind": "single", "text": ln})
        i += 1
    return out
