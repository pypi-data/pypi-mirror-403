from __future__ import annotations
import re
from typing import List

PIPE_SPLIT_RE = re.compile(r"\s*\|\s*")
CSV_SPLIT_RE  = re.compile(r"\s*,\s*")
ASCII_RULE_RE = re.compile(r"^\s*[:\-|+=]+\s*$")

def _split_pipe(line: str) -> List[str]:
    parts = PIPE_SPLIT_RE.split(line.strip().strip("|"))
    return [p.strip() for p in parts]

def _split_csv(line: str) -> List[str]:
    return [p.strip() for p in CSV_SPLIT_RE.split(line.strip())]

def is_table_like(line: str) -> bool:
    """
    Determine if a line looks like a table row.

    Conservative heuristics to avoid false positives:
    - Pipe delimiters: >=2 cells (pipes are strong indicators of intentional table formatting)
    - CSV: DISABLED for single-line detection to prevent prose false positives

    Rationale:
    - Natural language prose can have many commas in long sentences
    - A single line with commas is more likely prose than a CSV table
    - Real CSV tables should use pipe delimiters (|) for reliable detection
    - The table handler's consume() method would create tables from single prose sentences
    """
    s = line.strip()
    if not s:
        return False

    # Pipe tables: Keep original logic (strong signal of intentional table)
    if "|" in s and len(_split_pipe(s)) >= 2:
        return True

    # CSV detection disabled: Too prone to false positives with prose
    # Users should use pipe delimiters for tables
    return False

def parse_table_block(lines: List[str]) -> List[List[str]]:
    delim = None
    for ln in lines:
        if ASCII_RULE_RE.match(ln):
            continue

        if "|" in ln:
            delim = "pipe"
            break

        if ln.count(",") >= 2:
            delim = "csv"
            break

    if delim is None:
        delim = "pipe" if (lines and "|" in lines[0]) else "csv"

    rows: List[List[str]] = []
    for ln in lines:
        if ASCII_RULE_RE.match(ln): continue
        parts = _split_pipe(ln) if delim == "pipe" else _split_csv(ln)
        rows.append(parts)
    maxw = max((len(r) for r in rows), default=0)
    for r in rows:
        if len(r) < maxw: r += [""] * (maxw - len(r))
    return rows
