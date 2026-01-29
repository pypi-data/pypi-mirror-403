# src/glyph/core/schema_runner/router.py
from .writers import (
    ParagraphWriter, ListWriter, TableWriter, RowWriter, HeaderFooterWriter, ImageWriter, ThemeWriter
)

class SchemaRouter:
    def __init__(self, document):
        self.doc = document
        self.writers = {
            "P": ParagraphWriter(document),
            "H": ParagraphWriter(document),
            "L": ListWriter(document),
            "T": TableWriter(document),
            "R": RowWriter(document),
            "IMG": ImageWriter(document),
        }

    # --- internal helper: call writer with plaintext kwarg if supported ---
    def _call_with_plaintext(self, fn, *args, plaintext=None, **kwargs):
        try:
            return fn(*args, plaintext=plaintext, **kwargs)
        except TypeError:
            # writer doesn't accept plaintext yet → fallback
            return fn(*args, **kwargs)

    def dispatch(self, descriptor, style, *, plaintext: str | None = None):
        """
        Route a single descriptor to the appropriate writer.
        Always passes through plaintext (line text) when available.

        Type field can be:
        - Standard: "H1", "H2", "P-NORMAL", "L-BULLET", etc.
        - Classification: "H-SHORT", "P-BODY", etc.
        - EXACT/REGEX: "EXACT:Title", "REGEX:^pattern$" (infers type from style_id)
        - Array: ["EXACT:Title1", "EXACT:Title2"] (infers type from style_id)
        """
        t = descriptor.get("type", "P")
        if style:
            descriptor = {**descriptor, "style": {**descriptor.get("style", {}), **style}}

        # Handle section properties before dispatching to writers
        # Section properties apply document-wide layout changes (orientation, margins, columns)
        section_props = descriptor.get("style", {}).get("section")
        if section_props:
            # Use any writer's _handle_section_change() method (all inherit from BaseWriter)
            # Pick ParagraphWriter as it's always available
            self.writers["P"]._handle_section_change(section_props)

        # Handle array types (e.g., ["EXACT:Title1", "EXACT:Title2"])
        if isinstance(t, list):
            # Use first element or infer from style_id
            if t and isinstance(t[0], str) and (t[0].startswith("EXACT:") or t[0].startswith("REGEX:")):
                # Infer output type from style_id
                style_id = descriptor.get("style", {}).get("style_id", "")
                if style_id:
                    if "Heading" in style_id or style_id.startswith("H"):
                        t = "H"
                    elif "List" in style_id or style_id.startswith("L"):
                        t = "L"
                    elif "Table" in style_id or style_id.startswith("T"):
                        t = "T"
                    else:
                        t = "P"  # Default to paragraph
                else:
                    t = "P"  # Default to paragraph if no style_id
            else:
                t = "P"  # Default to paragraph for unknown array types
        # Handle EXACT: and REGEX: types by inferring from style_id
        elif isinstance(t, str) and (t.startswith("EXACT:") or t.startswith("REGEX:")):
            # Infer output type from style_id
            style_id = descriptor.get("style", {}).get("style_id", "")
            if style_id:
                if "Heading" in style_id or style_id.startswith("H"):
                    t = "H"
                elif "List" in style_id or style_id.startswith("L"):
                    t = "L"
                elif "Table" in style_id or style_id.startswith("T"):
                    t = "T"
                else:
                    t = "P"  # Default to paragraph
            else:
                t = "P"  # Default to paragraph if no style_id

        if t.startswith("H"):
            return self._call_with_plaintext(self.writers["H"].write, descriptor, style, plaintext=plaintext)
        if t.startswith("P"):
            return self._call_with_plaintext(self.writers["P"].write, descriptor, style, plaintext=plaintext)
        if t.startswith("L"):
            return self._call_with_plaintext(self.writers["L"].write, descriptor, style, plaintext=plaintext)
        if t.startswith("T"):
            return self._call_with_plaintext(self.writers["T"].write, descriptor, style, plaintext=plaintext)
        if t.startswith("R"):
            return self._call_with_plaintext(self.writers["R"].write, descriptor, style, plaintext=plaintext)
        if t.startswith("IMG"):
            return self._call_with_plaintext(self.writers["IMG"].write, descriptor, style, plaintext=plaintext)

        # --- Fallback ---
        return self._call_with_plaintext(self.writers["P"].write, descriptor, style, plaintext=plaintext)

    def dispatch_block(self, block, style=None, *, plaintext: str | None = None):
        """
        Route a multi-line block (list/table). Writers should implement write_block(..., plaintext=...).
        Falls back to per-line emission if block APIs aren't present.
        """
        kind = block.get("kind")

        if kind == "list":
            writer = self.writers["L"]
            if hasattr(writer, "write_block"):
                return self._call_with_plaintext(writer.write_block, block, plaintext=plaintext)
            # fallback: emit items as individual list paragraphs
            for it in block["payload"]["items"]:
                desc = {
                    "type": "L-BULLET-SOLID",
                    "features": {"text": it["text"]},
                    "style": {"style_id": "ListParagraph"},
                }
                self.dispatch(desc, style=None, plaintext=it["text"])
            return

        if kind == "table":
            writer = self.writers["T"]
            if hasattr(writer, "write_block"):
                return self._call_with_plaintext(writer.write_block, block, plaintext=plaintext)
            # fallback: degrade to paragraphs (one row per paragraph)
            for row in block["payload"]["rows"]:
                row_text = " | ".join(row)
                desc = {
                    "type": "P-NORMAL",
                    "features": {"text": row_text},
                    "style": {"style_id": "Normal"},
                }
                self.dispatch(desc, style=None, plaintext=row_text)
            return

        if kind == "row":
            writer = self.writers["R"]
            if hasattr(writer, "write_block"):
                return self._call_with_plaintext(writer.write_block, block, plaintext=plaintext)
            # fallback: degrade to paragraphs (cells joined with " | ")
            cells = block.get("payload", {}).get("cells", [])
            if cells:
                cell_texts = [c.get("text", "") for c in cells]
                row_text = " | ".join(cell_texts)
                desc = {
                    "type": "P-NORMAL",
                    "features": {"text": row_text},
                    "style": {"style_id": "Normal"},
                }
                self.dispatch(desc, style=None, plaintext=row_text)
            return

        # unknown block → degrade gracefully
        for sid in block.get("source_ids", []):
            txt = f"[{kind} item {sid}]"
            self.dispatch({"type": "P-NORMAL", "features": {"text": txt}}, style=None, plaintext=txt)
