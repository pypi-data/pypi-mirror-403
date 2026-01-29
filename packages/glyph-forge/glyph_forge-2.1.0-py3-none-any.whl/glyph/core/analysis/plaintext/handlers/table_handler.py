from __future__ import annotations
from typing import List, Tuple, TypedDict
from ..parsers.table_parser import is_table_like, parse_table_block

class RangeBlock(TypedDict):
    kind: str
    start_idx: int
    end_idx: int
    source_ids: List[str]
    payload: dict

class TableBlockHandler:
    def __init__(self, *, max_gap: int = 0):
        self.max_gap = max_gap

    def can_start(self, lines: List[str], i: int) -> bool:
        return is_table_like(lines[i])

    def consume(self, lines: List[str], i: int) -> Tuple[RangeBlock, int]:
        start, j, gaps = i, i, 0
        while j < len(lines):
            ln = lines[j]
            if ln.strip() == "":
                if gaps < self.max_gap: gaps += 1; j += 1; continue
                break
            if is_table_like(ln):
                j += 1; continue
            break

        rows = parse_table_block(lines[start:j])
        block: RangeBlock = {
            "kind": "table",
            "start_idx": start,
            "end_idx": j - 1,
            "source_ids": [f"pt_{k}" for k in range(start, j)],
            "payload": {"rows": rows},
        }
        return block, j - 1
