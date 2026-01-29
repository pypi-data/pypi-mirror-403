from __future__ import annotations
from typing import List, Tuple, TypedDict
from ..parsers.list_parser import is_bullet_line, normalize_bullet_line

class RangeBlock(TypedDict):
    kind: str
    start_idx: int
    end_idx: int
    source_ids: List[str]
    payload: dict

class ListBlockHandler:
    def __init__(self, *, blank_line_tolerance=0, allow_mixed_markers=True, wrap_indent_spaces=2):
        self.blank_tol = blank_line_tolerance
        self.allow_mixed = allow_mixed_markers
        self.wrap_indent = wrap_indent_spaces

    def can_start(self, lines: List[str], i: int) -> bool:
        return is_bullet_line(lines[i])

    def consume(self, lines: List[str], i: int) -> Tuple[RangeBlock, int]:
        start, j = i, i
        items = []
        blanks_left = self.blank_tol
        last_ilvl = None
        list_types = []  # Track all list types in block

        while j < len(lines):
            ln = lines[j]
            if ln.strip() == "":
                if blanks_left > 0:
                    blanks_left -= 1; j += 1; continue
                break

            if is_bullet_line(ln):
                ilvl, text, list_type, metadata = normalize_bullet_line(ln, self.wrap_indent)
                last_ilvl = ilvl if last_ilvl is None else last_ilvl

                # Capture detailed list metadata
                items.append({
                    "text": text,
                    "ilvl": ilvl,
                    "type": list_type,
                    "format": metadata.get("format"),
                    "lvlText": metadata.get("lvlText"),
                    "marker": metadata.get("marker"),
                })

                # Track unique list types
                if list_type not in list_types:
                    list_types.append(list_type)

                j += 1; continue

            # wrapped line continuation based on indent
            leading = len(ln) - len(ln.lstrip(" "))
            if last_ilvl is not None and leading >= (last_ilvl + 1) * self.wrap_indent and items:
                items[-1]["text"] = (items[-1]["text"] + " " + ln.strip()).strip()
                j += 1; continue
            break

        # Determine primary format from first item
        primary_format = items[0].get("format") if items else None
        primary_lvl_text = items[0].get("lvlText") if items else None

        block: RangeBlock = {
            "kind": "list",
            "start_idx": start,
            "end_idx": j - 1,
            "source_ids": [f"pt_{k}" for k in range(start, j)],
            "payload": {
                "numId": None,
                "ilvl": 0,
                "items": items,
                "list_types": list_types,  # All detected types
                "format": primary_format,  # Primary format for the block
                "lvlText": primary_lvl_text,  # Primary lvlText pattern
            },
        }
        return block, j - 1
