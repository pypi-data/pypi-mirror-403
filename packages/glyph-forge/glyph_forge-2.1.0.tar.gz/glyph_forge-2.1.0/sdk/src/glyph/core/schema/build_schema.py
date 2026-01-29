from __future__ import annotations
import os
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

from glyph.core.analysis.matcher import route_match
from glyph.core.analysis.utils.section import Section
from glyph.core.schema.utils.section_builder import build_sections_from_headings
from glyph.core.schema.schema_generator import SchemaGenerator

from glyph.core.analysis.detectors.heuristics.heading_detector import detect_headings
from glyph.core.schema.utils.mappers.docx_styles_mapper import DocxStylesMapper
from glyph.core.schema.utils.mappers.docx_sections_mapper import DocxSectionsMapper
from glyph.core.schema.utils.mappers.docx_tables_mapper import DocxTablesMapper
from glyph.core.schema.utils.mappers.docx_numbering_mapper import DocxNumberingMapper
from glyph.core.schema.utils.mappers.docx_headers_footers_mapper import DocxHeadersFootersMapper
from glyph.core.schema.utils.mappers.docx_themes_mapper import DocxThemesMapper
from glyph.core.schema.utils.mappers.docx_text_mapper import DocxTextMapper

from glyph.core.analysis.context.context_enricher import ContextEnricher
from glyph.core.analysis.context.heading_enricher import heading_context_enricher
from glyph.core.analysis.forms.headings import detect_subtitle_context, HeadingForm


class GlyphSchemaBuilder:
    """
    Parse a DOCX XML and build a glyph schema.

    Orchestrates extraction via mappers, then delegates schema assembly
    to SchemaGenerator.
    """

    def __init__(self, document_xml_path: str, docx_extract_dir: str | None = None, source_docx: str | None = None, tag: str | None = None):
        if not os.path.exists(document_xml_path):
            raise FileNotFoundError(f"document.xml not found: {document_xml_path}")

        with open(document_xml_path, "r", encoding="utf-8") as f:
            document_xml = f.read()

        self.nsmap = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        self.tree = ET.fromstring(document_xml)
        self.body = self.tree.find(".//w:body", namespaces=self.nsmap)

        self.document_xml_path = document_xml_path
        self.docx_extract_dir = docx_extract_dir
        self.source_docx = source_docx
        self.tag = tag
        # containers for extraction results
        self.sections: List[Section] = []
        self.layout_groups: List[Dict[str, Any]] = []
        self.global_defaults: Dict[str, Any] = {}
        self.pattern_descriptors: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Extractors
    # ------------------------------------------------------------------
    def generate_pattern_descriptors(self) -> List[Dict[str, Any]]:
        """
        Detect all paragraphs and build pattern descriptors with taxonomy + styles.

        Uses two-pass approach:
        1. First pass: Generate base descriptors using route_match
        2. Second pass: Enrich with context and refine classifications (e.g., subtitle detection)
        """
        # preload styles + defaults + numbering
        styles = self.extract_styles()
        defaults = self.extract_global_defaults()
        numbering = self.extract_numbering()

        # pass numbering and extract_dir into text mapper
        text_mapper = DocxTextMapper(self.nsmap, styles, defaults, numbering, self.docx_extract_dir)

        paragraphs_info = text_mapper.extract_paragraphs(self.body)
        descriptors = []
        lines = []
        para_ids = []

        # --- FIRST PASS: Generate base descriptors ---
        if paragraphs_info:
            for i, pinfo in enumerate(paragraphs_info):
                text = (pinfo["text"] or "").strip()
                if not text:
                    continue

                para_id = pinfo["paragraph_id"] or f"p_{i+1}"

                desc = route_match(
                    text=text,
                    features=pinfo["style"],
                )

                # attach metadata
                desc.paragraph_id = para_id
                desc.features.update({"text": text})
                desc.style = pinfo["style"]

                # CRITICAL: Generate regex pattern for plaintext matching
                # Normalize whitespace in regex for flexible matching
                import re
                # Normalize multiple spaces to single space for regex
                normalized_text = ' '.join(text.split())
                desc.regex = f"^{re.escape(normalized_text)}$"

                descriptors.append(desc)
                lines.append(text)
                para_ids.append(para_id)

        # --- Table descriptors ---
        tables_info = self.extract_tables()
        if tables_info:
            for tinfo in tables_info:
                desc = route_match(
                    text="[TABLE]",  # placeholder text
                    features=tinfo["features"],  # pass only abstract features
                )
                desc.table_id = tinfo["id"]
                descriptors.append(desc)

        # --- SECOND PASS: Context enrichment and refinement ---
        descriptors = self._refine_with_context(descriptors)

        # Convert all to dict (will be output as "selectors" in schema)
        # Note: Internal variable name remains pattern_descriptors for backward compatibility
        self.pattern_descriptors = [d.to_dict() for d in descriptors]
        return self.pattern_descriptors

    def _refine_with_context(self, descriptors: List[Any]) -> List[Any]:
        """
        Second pass: Apply context-aware refinements to descriptors.

        Currently focuses on subtitle detection for headings.
        Can be extended for other context-aware classifications.

        Args:
            descriptors: List of PatternDescriptor objects from first pass

        Returns:
            Refined list of PatternDescriptor objects
        """
        if not descriptors:
            return descriptors

        # Convert descriptors to dict format for context enrichment
        base_descriptors = [d.to_dict() for d in descriptors]

        # Initialize context enricher with heading-specific enricher
        enricher = ContextEnricher(window_size=2, skip_blank_lines=True)
        enricher.register_enricher(heading_context_enricher)

        # Build context windows for all descriptors
        for i, desc in enumerate(descriptors):
            # Build context window for current element
            context = enricher.build_window(i, base_descriptors, base_descriptors[i])

            # Check if this is a heading that should be reclassified as subtitle
            current_type = desc.type
            text = desc.features.get("text", "")
            style = getattr(desc, "style", None)

            # Apply subtitle detection for heading types
            if current_type in ["H-SHORT", "H-LONG", "H-SECTION-N"]:
                is_subtitle = detect_subtitle_context(
                    text=text,
                    current_type=current_type,
                    context=context,
                    style=style
                )

                if is_subtitle:
                    # Reclassify as subtitle
                    desc.type = HeadingForm.H_SUBTITLE.value
                    desc.signals.append("CONTEXT-SUBTITLE")
                    if hasattr(desc, "form"):
                        desc.form = HeadingForm.H_SUBTITLE

        return descriptors

    def extract_global_defaults(self) -> Dict[str, Any]:
        """
        Extract global defaults from the first section of the document.
        Falls back to baseline defaults if section info is not available.
        """
        # Start with baseline defaults
        self.global_defaults = {
            "page_size": {"width": 12240, "height": 15840},
            "margins": {
                "left": 1440,    # 1 inch = 1440 twips
                "right": 1440,
                "top": 1440,
                "bottom": 1440,
            },
            "font": {"name": "Arial", "size": 12},
            "paragraph": {"alignment": "left"},
        }

        # Extract sections and merge first section's properties into global_defaults
        sections = self.extract_sections()
        if sections:
            first_section = sections[0]

            # Merge page_size if present (convert strings to integers)
            if "page_size" in first_section:
                page_size = first_section["page_size"]
                for key in ["width", "height"]:
                    if key in page_size:
                        # Convert string to int if needed
                        val = page_size[key]
                        self.global_defaults["page_size"][key] = int(val) if isinstance(val, str) else val
                # Copy orientation as-is (it's a string like "portrait")
                if "orientation" in page_size:
                    self.global_defaults["page_size"]["orientation"] = page_size["orientation"]

            # Merge margins if present (convert strings to integers)
            if "margins" in first_section:
                margins = first_section["margins"]
                for key in ["left", "right", "top", "bottom"]:
                    if key in margins:
                        # Convert string to int if needed
                        val = margins[key]
                        self.global_defaults["margins"][key] = int(val) if isinstance(val, str) else val

            # Add page_borders if present
            if "page_borders" in first_section:
                self.global_defaults["page_borders"] = first_section["page_borders"]

            # Add vertical_alignment if present
            if "vertical_alignment" in first_section:
                self.global_defaults["vertical_alignment"] = first_section["vertical_alignment"]

            # Add section_type if present
            if "section_type" in first_section:
                self.global_defaults["section_type"] = first_section["section_type"]

        return self.global_defaults

    def extract_styles(self) -> Dict[str, Any]:
        mapper = DocxStylesMapper(self.document_xml_path, self.docx_extract_dir)
        return mapper.collect_styles()

    def extract_sections(self) -> List[Dict[str, Any]]:
        mapper = DocxSectionsMapper(self.document_xml_path)
        return mapper.collect_sections()

    def extract_tables(self) -> List[Dict[str, Any]]:
        mapper = DocxTablesMapper(self.document_xml_path)
        return mapper.collect_tables()

    def extract_numbering(self) -> Dict[str, Any]:
        if not self.docx_extract_dir:
            return {}
        numbering_path = os.path.join(self.docx_extract_dir, "word", "numbering.xml")
        if os.path.exists(numbering_path):
            return DocxNumberingMapper(numbering_path).collect_numbering()
        return {}

    def extract_headers_footers(self) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]]]:
        if not self.docx_extract_dir:
            return [], []
        mapper = DocxHeadersFootersMapper(self.docx_extract_dir)
        hf = mapper.collect_headers_footers()
        return hf["headers"], hf["footers"]

    def extract_theme(self) -> Dict[str, Any]:
        if not self.docx_extract_dir:
            return {}
        theme_path = os.path.join(self.docx_extract_dir, "word", "theme", "theme1.xml")
        if os.path.exists(theme_path):
            return DocxThemesMapper(theme_path).collect_theme()
        return {}

    def extract_hyperlinks(self) -> List[Dict[str, Any]]:
        if not self.docx_extract_dir:
            return []
        rels_path = os.path.join(self.docx_extract_dir, "word", "_rels", "document.xml.rels")
        rels_map = {}
        if os.path.exists(rels_path):
            rels_tree = ET.parse(rels_path).getroot()
            for rel in rels_tree.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
                r_id = rel.attrib.get("Id")
                target = rel.attrib.get("Target")
                rels_map[r_id] = target
        links = []
        for link in self.body.findall(".//w:hyperlink", namespaces=self.nsmap):
            r_id = link.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            text = "".join(t.text for t in link.findall(".//w:t", namespaces=self.nsmap) if t.text)
            links.append({"text": text, "target": rels_map.get(r_id, "")})
        return links

    def extract_images(self) -> List[Dict[str, Any]]:
        """
        Extract images with full metadata including:
        - Path to extracted image file
        - Dimensions (width/height in EMUs, converted to inches)
        - Position (paragraph index where image appears)
        - Alt text
        - Unique image ID for plaintext reference
        """
        if not self.docx_extract_dir:
            return []

        # Load relationships to map rId to file paths
        rels_path = os.path.join(self.docx_extract_dir, "word", "_rels", "document.xml.rels")
        rels_map = {}
        if os.path.exists(rels_path):
            rels_tree = ET.parse(rels_path).getroot()
            rels_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
            for rel in rels_tree.findall(f".//{{{rels_ns}}}Relationship"):
                target = rel.attrib.get("Target", "")
                if "image" in target.lower() or target.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
                    rels_map[rel.attrib.get("Id")] = target

        images = []
        image_counter = 1

        # Find all paragraphs to track position
        paragraphs = self.body.findall(".//w:p", namespaces=self.nsmap)

        for para_idx, para in enumerate(paragraphs):
            for drawing in para.findall(".//w:drawing", namespaces=self.nsmap):
                image_data = self._extract_drawing_data(drawing, rels_map, para_idx, image_counter)
                if image_data:
                    images.append(image_data)
                    image_counter += 1

        return images

    def _extract_drawing_data(
        self, drawing, rels_map: Dict[str, str], para_idx: int, counter: int
    ) -> Dict[str, Any] | None:
        """Extract comprehensive image data from a drawing element."""
        # Namespaces for drawing elements
        nsmap_a = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
        nsmap_wp = {"wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"}
        nsmap_r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

        # Find the blip element (contains the image reference)
        blip = drawing.find(".//a:blip", namespaces=nsmap_a)
        if blip is None:
            return None

        r_id = blip.attrib.get(f"{{{nsmap_r}}}embed", "")
        rel_path = rels_map.get(r_id, "")

        if not rel_path:
            return None

        # Full path to extracted image
        full_path = os.path.join(self.docx_extract_dir, "word", rel_path)

        # Extract dimensions from extent element (in EMUs - English Metric Units)
        # 914400 EMU = 1 inch
        extent = drawing.find(".//wp:extent", namespaces=nsmap_wp)
        width_emu = int(extent.attrib.get("cx", 0)) if extent is not None else 0
        height_emu = int(extent.attrib.get("cy", 0)) if extent is not None else 0

        # Convert EMU to inches
        width_inches = round(width_emu / 914400, 2) if width_emu else None
        height_inches = round(height_emu / 914400, 2) if height_emu else None

        # Extract alt text and name from docPr element
        doc_pr = drawing.find(".//wp:docPr", namespaces=nsmap_wp)
        alt_text = ""
        name = f"image{counter}"

        if doc_pr is not None:
            alt_text = doc_pr.attrib.get("descr", "")
            name = doc_pr.attrib.get("name", name)

        # Generate unique ID for plaintext reference
        image_id = f"img_{counter}"

        return {
            "id": image_id,
            "rId": r_id,
            "path": full_path,
            "rel_path": rel_path,
            "name": name,
            "alt_text": alt_text,
            "width_inches": width_inches,
            "height_inches": height_inches,
            "width_emu": width_emu,
            "height_emu": height_emu,
            "paragraph_index": para_idx,
        }

    def extract_bookmarks(self) -> List[Dict[str, Any]]:
        bookmarks = []
        for bm in self.body.findall(".//w:bookmarkStart", namespaces=self.nsmap):
            name = bm.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}name")
            bookmarks.append({"name": name})
        return bookmarks

    def extract_inline_formatting(self) -> List[Dict[str, Any]]:
        flags = []
        for p in self.body.findall(".//w:p", namespaces=self.nsmap):
            formats = {"bold": False, "italic": False, "underline": False}
            for r in p.findall(".//w:r", namespaces=self.nsmap):
                rPr = r.find("w:rPr", namespaces=self.nsmap)
                if rPr is not None:
                    if rPr.find("w:b", namespaces=self.nsmap) is not None:
                        formats["bold"] = True
                    if rPr.find("w:i", namespaces=self.nsmap) is not None:
                        formats["italic"] = True
                    if rPr.find("w:u", namespaces=self.nsmap) is not None:
                        formats["underline"] = True
            flags.append(formats)
        return flags

    def extract_metadata(self) -> Dict[str, Any]:
        if not self.docx_extract_dir:
            return {}
        core_path = os.path.join(self.docx_extract_dir, "docProps", "core.xml")
        if not os.path.exists(core_path):
            return {}
        core_tree = ET.parse(core_path).getroot()
        nsmap = {
            "dc": "http://purl.org/dc/elements/1.1/",
            "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
        }
        return {
            "title": (core_tree.find("dc:title", nsmap).text if core_tree.find("dc:title", nsmap) is not None else ""),
            "subject": (core_tree.find("dc:subject", nsmap).text if core_tree.find("dc:subject", nsmap) is not None else ""),
            "creator": (core_tree.find("dc:creator", nsmap).text if core_tree.find("dc:creator", nsmap) is not None else ""),
            "keywords": (core_tree.find("cp:keywords", nsmap).text if core_tree.find("cp:keywords", nsmap) is not None else ""),
        }

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------
    def run(self, workspace: Any | None = None, copy_images: bool = True) -> Dict[str, Any]:
        """
        Run the schema building pipeline.

        Args:
            workspace: Optional workspace instance for copying images
            copy_images: Whether to copy images to workspace (default True)

        Returns:
            Generated schema dict
        """
        pattern_descriptors = self.generate_pattern_descriptors()
        global_defaults = self.extract_global_defaults()

        styles = self.extract_styles()
        sections = self.extract_sections()
        tables = self.extract_tables()
        numbering = self.extract_numbering()
        headers, footers = self.extract_headers_footers()
        theme = self.extract_theme()

        hyperlinks = self.extract_hyperlinks()
        images = self.extract_images()
        bookmarks = self.extract_bookmarks()
        inline_formatting = self.extract_inline_formatting()
        metadata = self.extract_metadata()

        # Copy images to workspace if provided
        if workspace and copy_images and images:
            for idx, img in enumerate(images, 1):
                if os.path.exists(img["path"]):
                    copied_path = workspace.copy_image(
                        src_path=img["path"],
                        image_id=img["id"],
                        index=idx,
                    )
                    img["workspace_path"] = copied_path

        generator = SchemaGenerator(
            sections=self.sections,
            layout_groups=self.layout_groups,
            global_defaults=global_defaults,
            # styles=styles,
            # tables=tables,
            # numbering=numbering,
            headers=headers,
            footers=footers,
            theme=theme,
            # hyperlinks=hyperlinks,
            images=images,
            # bookmarks=bookmarks,
            # inline_formatting=inline_formatting,
            # metadata=metadata,
            pattern_descriptors=pattern_descriptors,
            source_docx=self.source_docx,
            tag=self.tag,
        )
        return generator.generate()
