from __future__ import annotations
from typing import List
from glyph.settings import get_settings
from .list_handler import ListBlockHandler
from .table_handler import TableBlockHandler

def make_handlers_from_settings(settings=None) -> List[object]:
    S = settings or get_settings()
    enabled = set(S.RANGE_HANDLERS_ENABLED or [])
    handlers: List[object] = []
    if "table" in enabled:
        handlers.append(TableBlockHandler())
    if "list" in enabled:
        handlers.append(ListBlockHandler(
            blank_line_tolerance=S.LIST_BLANK_LINE_TOLERANCE,
            allow_mixed_markers=S.LIST_ALLOW_MIXED_MARKERS,
            wrap_indent_spaces=S.LIST_WRAP_INDENT_SPACES,
        ))
    return handlers
