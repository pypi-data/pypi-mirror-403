from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, Literal, Dict, List, TYPE_CHECKING
import unicodedata, hashlib, uuid, re

if TYPE_CHECKING:
    from .classifier import PlaintextLineClassification

_ZW_RE = re.compile(r"[\u200B-\u200D\uFEFF]")

LineEnding = Literal["LF", "CRLF", "CR", "MIXED", "UNKNOWN"]

@dataclass(frozen=True)
class PlaintextIntakeResult:
    text_raw: str
    text_norm: str
    lines: List[str]
    encoding: str
    original_line_ending: LineEnding
    normalized_line_ending: LineEnding
    checksum_sha256: str
    stats: Dict[str, int]
    stored_plaintext_path: Optional[Path] = None
    classifications: Optional[List["PlaintextLineClassification"]] = None

def _detect_line_ending(s: str) -> LineEnding:
    crlf = s.count("\r\n")
    cr = s.count("\r") - crlf
    lf = s.count("\n") - crlf
    kinds = sum(1 for n in (crlf, cr, lf) if n > 0)
    if kinds == 0: return "UNKNOWN"
    if kinds > 1:  return "MIXED"
    if crlf > 0:   return "CRLF"
    if cr > 0:     return "CR"
    return "LF"

def _decode_bytes(b: bytes) -> tuple[str, str]:
    try:    return b.decode("utf-8-sig"), "utf-8"
    except: pass
    try:    return b.decode("utf-8"), "utf-8"
    except: return b.decode("latin-1", errors="strict"), "latin-1"

def _normalize_text(s: str, *, unicode_form: Literal["NFC","NFKC"]="NFC",
                    strip_zero_width: bool=True, expand_tabs: int|None=None,
                    ensure_final_newline: bool=True) -> str:
    s = s.replace("\r\n","\n").replace("\r","\n")
    s = unicodedata.normalize(unicode_form, s)
    if strip_zero_width: s = _ZW_RE.sub("", s)
    if isinstance(expand_tabs,int) and expand_tabs>0: s = s.expandtabs(expand_tabs)
    if ensure_final_newline and not s.endswith("\n"): s += "\n"
    return s

def intake_plaintext(
    source: Union[str, Path, bytes],
    *,
    store_dir: Optional[Path] = None,
    filename: Optional[str] = None,
    unicode_form: Literal["NFC","NFKC"]="NFC",
    strip_zero_width: bool=True,
    expand_tabs: Optional[int]=None,
    ensure_final_newline: bool=True,
    max_bytes: int = 8*1024*1024,
    classify: bool = False,
) -> PlaintextIntakeResult:
    if isinstance(source, Path):
        b = source.read_bytes()
    elif isinstance(source, bytes):
        b = source
    elif isinstance(source, str):
        b = source.encode("utf-8")
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")

    if len(b) > max_bytes:
        raise ValueError(f"Plaintext exceeds max_bytes ({max_bytes}).")

    text_decoded, encoding = _decode_bytes(b)
    original_le = _detect_line_ending(text_decoded)
    text_norm = _normalize_text(
        text_decoded,
        unicode_form=unicode_form,
        strip_zero_width=strip_zero_width,
        expand_tabs=expand_tabs,
        ensure_final_newline=ensure_final_newline,
    )
    normalized_le = "LF" if "\n" in text_norm else "UNKNOWN"
    lines = text_norm.splitlines()
    stats = {
        "num_chars_raw": len(text_decoded),
        "num_chars_norm": len(text_norm),
        "num_lines": len(lines),
        "num_blank_lines": sum(1 for ln in lines if ln.strip() == ""),
    }
    checksum = hashlib.sha256(text_norm.encode("utf-8")).hexdigest()

    stored_path = None
    if store_dir:
        store_dir.mkdir(parents=True, exist_ok=True)
        stored_path = (store_dir / (filename or f"plaintext_{uuid.uuid4().hex}.txt"))
        stored_path.write_text(text_norm, encoding="utf-8")

    # Optionally classify lines
    line_classifications = None
    if classify:
        from .classifier import classify_lines
        line_classifications = classify_lines(lines, use_context=True)

    return PlaintextIntakeResult(
        text_raw=text_decoded,
        text_norm=text_norm,
        lines=lines,
        encoding=encoding,
        original_line_ending=original_le,
        normalized_line_ending=normalized_le,
        checksum_sha256=checksum,
        stats=stats,
        stored_plaintext_path=stored_path,
        classifications=line_classifications,
    )
