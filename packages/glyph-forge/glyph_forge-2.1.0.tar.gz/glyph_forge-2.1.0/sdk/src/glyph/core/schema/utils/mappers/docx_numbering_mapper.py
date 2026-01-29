# src/glyph/core/schema/utils/mappers/docx_numbering_mapper.py
import xml.etree.ElementTree as ET

class DocxNumberingMapper:
    def __init__(self, numbering_xml_path: str):
        self.nsmap = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        self.tree = ET.parse(numbering_xml_path)
        self.root = self.tree.getroot()
        self.map = self._build_map()

    def _build_map(self):
        num_map = {}
        for num in self.root.findall(".//w:num", namespaces=self.nsmap):
            num_id = num.attrib.get(f"{{{self.nsmap['w']}}}numId")
            if not num_id:  # fallback: some schemas use child <w:numId>
                num_id_elem = num.find("w:numId", namespaces=self.nsmap)
                if num_id_elem is not None:
                    num_id = num_id_elem.attrib.get(f"{{{self.nsmap['w']}}}val")
            if not num_id:
                continue

            abs_id_elem = num.find("w:abstractNumId", namespaces=self.nsmap)
            if abs_id_elem is None:
                continue
            abs_id = abs_id_elem.attrib.get(f"{{{self.nsmap['w']}}}val")

            abs_def = self.root.find(
                f".//w:abstractNum[@w:abstractNumId='{abs_id}']",
                namespaces=self.nsmap
            )
            if abs_def is None:
                continue

            lvls = {}
            for lvl in abs_def.findall(".//w:lvl", namespaces=self.nsmap):
                ilvl = lvl.attrib.get(f"{{{self.nsmap['w']}}}ilvl")
                numFmt = lvl.find("w:numFmt", namespaces=self.nsmap)
                lvlText = lvl.find("w:lvlText", namespaces=self.nsmap)
                lvls[ilvl] = {
                    "format": numFmt.attrib.get(f"{{{self.nsmap['w']}}}val") if numFmt is not None else None,
                    "lvlText": lvlText.attrib.get(f"{{{self.nsmap['w']}}}val") if lvlText is not None else None,
                }

            num_map[num_id] = lvls

        return num_map

    def resolve(self, numId: str, ilvl: str = "0"):
        return self.map.get(numId, {}).get(ilvl, {})

    def collect_numbering(self):
        """Return the full numbering map (mainly for schema builder)."""
        return self.map
