import xml.etree.ElementTree as ET
from typing import Any, Dict, List


class DocxTablesMapper:
    def __init__(self, document_xml_path: str):
        self.tree = ET.parse(document_xml_path)
        self.ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    def collect_tables(self) -> List[Dict[str, Any]]:
        tables = []
        for t_idx, tbl in enumerate(self.tree.findall(".//w:tbl", self.ns)):
            # --- Extract row/cell content (plaintext only for now) ---
            rows = []
            for tr in tbl.findall("w:tr", self.ns):
                cells = []
                for tc in tr.findall("w:tc", self.ns):
                    texts = [
                        "".join(t.itertext()) for t in tc.findall(".//w:t", self.ns)
                    ]
                    cells.append(" ".join(texts).strip())
                rows.append(cells)

            # --- Table properties ---
            tblPr = tbl.find("w:tblPr", self.ns)

            # style id
            style_id = None
            if tblPr is not None:
                style_elem = tblPr.find("w:tblStyle", self.ns)
                if style_elem is not None:
                    style_id = style_elem.get(f"{{{self.ns['w']}}}val")

            # alignment
            alignment = None
            if tblPr is not None:
                jc_elem = tblPr.find("w:jc", self.ns)
                if jc_elem is not None:
                    alignment = jc_elem.get(f"{{{self.ns['w']}}}val")

            # borders (just a flag for now)
            borders = "all" if tblPr is not None and tblPr.find("w:tblBorders", self.ns) is not None else None

            # shading (fill color on tblPr if present)
            shading = None
            if tblPr is not None:
                shd_elem = tblPr.find("w:shd", self.ns)
                if shd_elem is not None:
                    shading = shd_elem.get(f"{{{self.ns['w']}}}fill")

            # --- Header row detection (naive: first row) ---
            header_rows = 1 if rows else 0

            # --- Build schema-friendly object ---
            tables.append({
                "id": f"tbl_{t_idx+1}",
                "type": "T",
                "features": {
                    "style": {
                        "table_style": style_id or "TableGrid",
                        "alignment": alignment or "left",
                        "borders": borders or "all",
                        "shading": shading or "none"
                    },
                    "table": {
                        "columns": len(rows[0]) if rows and rows[0] else 0,
                        "header_rows": header_rows
                    }
                }
            })

        return tables
