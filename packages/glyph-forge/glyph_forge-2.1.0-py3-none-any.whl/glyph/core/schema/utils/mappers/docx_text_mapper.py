import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
import os


class DocxTextMapper:
    def __init__(
        self,
        nsmap: Dict[str, str],
        styles: Dict[str, Any],
        defaults: Dict[str, Any],
        numbering: Optional[Dict[str, Any]] = None,
        docx_extract_dir: Optional[str] = None,
    ):
        self.nsmap = nsmap
        self.styles = styles
        self.defaults = defaults
        self.numbering = numbering or {}
        self.docx_extract_dir = docx_extract_dir
        self.relationships = self._load_relationships() if docx_extract_dir else {}

    def extract_paragraphs(self, body: ET.Element) -> List[Dict[str, Any]]:
        """Return list of dicts (text + style + para_id) for each paragraph in <w:body>."""
        paragraphs = []
        for p in body.findall("w:p", namespaces=self.nsmap):
            text = self._get_text(p)
            style = self._resolve_style(p)
            para_id = p.attrib.get("{http://schemas.microsoft.com/office/word/2010/wordml}paraId")
            hyperlinks = self._extract_hyperlinks(p)

            para_dict = {
                "text": text,
                "style": style,
                "paragraph_id": para_id,
                "p_elem": p,  # keep original element if needed downstream
            }

            # Add hyperlinks if found
            if hyperlinks:
                para_dict["hyperlinks"] = hyperlinks
                # For simple case: if entire paragraph is a hyperlink, add to style
                if len(hyperlinks) == 1 and hyperlinks[0]["text"].strip() == text.strip():
                    style.setdefault("font", {})["hyperlink"] = hyperlinks[0]["url"]

            paragraphs.append(para_dict)
        return paragraphs

    def _get_text(self, p: ET.Element) -> str:
        return " ".join(t.text for t in p.findall(".//w:t", namespaces=self.nsmap) if t.text)

    def _resolve_style(self, p: ET.Element) -> Dict[str, Any]:
        """
        Resolve paragraph-level and run-level style info into a dict.
        Includes font, alignment, style_id, and list info (numId/ilvl + resolved format).
        """
        style: Dict[str, Any] = {}

        # paragraph props
        pPr = p.find("w:pPr", namespaces=self.nsmap)
        if pPr is not None:
            # explicit paragraph style
            style_elem = pPr.find("w:pStyle", namespaces=self.nsmap)
            if style_elem is not None:
                style_id = style_elem.attrib.get(f"{{{self.nsmap['w']}}}val")
                style["style_id"] = style_id
                if style_id and style_id in self.styles.get("paragraphs", {}):
                    style.update(self.styles["paragraphs"][style_id])

            # alignment
            jc = pPr.find("w:jc", namespaces=self.nsmap)
            if jc is not None:
                style.setdefault("paragraph", {})["alignment"] = jc.attrib.get(f"{{{self.nsmap['w']}}}val")

            # paragraph shading
            shd = pPr.find("w:shd", namespaces=self.nsmap)
            if shd is not None:
                fill = shd.attrib.get(f"{{{self.nsmap['w']}}}fill")
                if fill and fill != "auto":  # Ignore "auto" which means no shading
                    style.setdefault("paragraph", {})["shading"] = fill

            # list / numbering
            numPr = pPr.find("w:numPr", namespaces=self.nsmap)
            if numPr is not None:
                list_info: Dict[str, Any] = {}
                num_id_elem = numPr.find("w:numId", namespaces=self.nsmap)
                ilvl_elem = numPr.find("w:ilvl", namespaces=self.nsmap)

                if num_id_elem is not None:
                    list_info["numId"] = num_id_elem.attrib.get(f"{{{self.nsmap['w']}}}val")
                if ilvl_elem is not None:
                    list_info["ilvl"] = ilvl_elem.attrib.get(f"{{{self.nsmap['w']}}}val")

                # 🔑 integrate numbering map (format, lvlText, etc.)
                if list_info and "numId" in list_info and self.numbering:
                    num_id = list_info["numId"]
                    ilvl = list_info.get("ilvl", "0")
                    resolved = self.numbering.get(num_id, {}).get(ilvl, {})
                    if resolved:
                        list_info.update(resolved)

                if list_info:
                    style["list"] = list_info

        # run props (font-level)
        for r in p.findall(".//w:r", namespaces=self.nsmap):
            rPr = r.find("w:rPr", namespaces=self.nsmap)
            if rPr is not None:
                self._merge_run_properties(style, rPr)

        return style

    def _merge_run_properties(self, style: Dict[str, Any], rPr: ET.Element):
        font = style.setdefault("font", {})
        if rPr.find("w:b", namespaces=self.nsmap) is not None:
            font["bold"] = True
        if rPr.find("w:i", namespaces=self.nsmap) is not None:
            font["italic"] = True
        if rPr.find("w:u", namespaces=self.nsmap) is not None:
            font["underline"] = True
        if rPr.find("w:strike", namespaces=self.nsmap) is not None:
            font["strike"] = True
        if rPr.find("w:caps", namespaces=self.nsmap) is not None:
            font["all_caps"] = True
        if rPr.find("w:smallCaps", namespaces=self.nsmap) is not None:
            font["small_caps"] = True

        rFonts = rPr.find("w:rFonts", namespaces=self.nsmap)
        if rFonts is not None:
            ascii_font = rFonts.attrib.get(f"{{{self.nsmap['w']}}}ascii")
            if ascii_font:
                font["name"] = ascii_font

        sz = rPr.find("w:sz", namespaces=self.nsmap)
        if sz is not None:
            font["size"] = int(sz.attrib.get(f"{{{self.nsmap['w']}}}val")) // 2

        color = rPr.find("w:color", namespaces=self.nsmap)
        if color is not None:
            font["color"] = color.attrib.get(f"{{{self.nsmap['w']}}}val")

        highlight = rPr.find("w:highlight", namespaces=self.nsmap)
        if highlight is not None:
            font["highlight"] = highlight.attrib.get(f"{{{self.nsmap['w']}}}val")

    def _load_relationships(self) -> Dict[str, str]:
        """Load document.xml.rels to resolve hyperlink relationship IDs to URLs."""
        rels_path = os.path.join(self.docx_extract_dir, "word", "_rels", "document.xml.rels")
        if not os.path.exists(rels_path):
            return {}

        try:
            tree = ET.parse(rels_path)
            root = tree.getroot()
            # Namespace for relationships
            rels_ns = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}

            relationships = {}
            for rel in root.findall("r:Relationship", namespaces=rels_ns):
                rel_id = rel.attrib.get("Id")
                rel_type = rel.attrib.get("Type", "")
                target = rel.attrib.get("Target", "")

                # Only store hyperlinks (external relationships)
                if "hyperlink" in rel_type.lower():
                    relationships[rel_id] = target

            return relationships
        except Exception:
            return {}

    def _extract_hyperlinks(self, p: ET.Element) -> List[Dict[str, Any]]:
        """Extract hyperlink information from paragraph."""
        hyperlinks = []
        # Extended namespace map including relationships
        ns = {**self.nsmap, "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}

        for hyperlink_elem in p.findall(".//w:hyperlink", namespaces=ns):
            rel_id = hyperlink_elem.attrib.get(f"{{{ns['r']}}}id")
            if rel_id and rel_id in self.relationships:
                # Get text from runs within hyperlink
                text = " ".join(
                    t.text for t in hyperlink_elem.findall(".//w:t", namespaces=ns) if t.text
                )
                hyperlinks.append({
                    "text": text,
                    "url": self.relationships[rel_id],
                    "rel_id": rel_id
                })

        return hyperlinks
