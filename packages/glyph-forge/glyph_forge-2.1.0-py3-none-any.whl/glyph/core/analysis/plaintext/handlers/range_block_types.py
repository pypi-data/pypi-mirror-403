from __future__ import annotations
from typing import TypedDict, List, Literal, NotRequired

# Base
class BaseRangeBlock(TypedDict):
    kind: Literal["list", "table"]
    start_idx: int          # inclusive
    end_idx: int            # inclusive
    source_ids: List[str]   # e.g., ["pt_10","pt_11","pt_12"]

# List
class ListItem(TypedDict, total=False):
    text: str
    ilvl: int               # nesting level
    style: dict             # optional per-item overrides

class ListPayload(TypedDict, total=False):
    numId: NotRequired[str | None]   # None for plaintext
    ilvl: NotRequired[int]           # top-level default
    items: List[ListItem]

class ListRangeBlock(BaseRangeBlock):
    kind: Literal["list"]
    payload: ListPayload

# Table
class TablePayload(TypedDict, total=False):
    rows: List[List[str]]
    header_rows: NotRequired[int]
    col_widths: NotRequired[List[float]]   # inches
    cell_alignment: NotRequired[Literal["left","right","center","justify"]]

class TableRangeBlock(BaseRangeBlock):
    kind: Literal["table"]
    payload: TablePayload

# Union you can use in signatures:
RangeBlock = ListRangeBlock | TableRangeBlock
