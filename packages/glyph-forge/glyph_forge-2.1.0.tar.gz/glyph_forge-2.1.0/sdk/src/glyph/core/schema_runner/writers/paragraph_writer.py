# src/glyph/core/schema_runner/writers/paragraph_writer.py

from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.shared import Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from .font_utils import convert_underline_value
from .base_writer import BaseWriter


class ParagraphWriter(BaseWriter):
    """
    Handles writing headings and body paragraphs into the document.
    Applies style_id if available, then font overrides, then paragraph alignment.
    Inherits section handling from BaseWriter.
    """

    def _add_hyperlink(self, paragraph, url: str, text: str, run_properties=None):
        """
        Add a hyperlink to a paragraph using low-level XML manipulation.
        python-docx doesn't have built-in hyperlink support, so we use the XML API.

        :param paragraph: The paragraph to add the hyperlink to
        :param url: The URL for the hyperlink
        :param text: The text to display for the hyperlink
        :param run_properties: Optional dict of run properties to apply
        :return: The hyperlink element
        """
        # Get the paragraph element
        p = paragraph._p

        # Create a new relationship for the hyperlink
        part = paragraph.part
        r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)

        # Create hyperlink element
        hyperlink = OxmlElement('w:hyperlink')
        hyperlink.set(qn('r:id'), r_id)

        # Create a new run for the hyperlink text
        new_run = OxmlElement('w:r')

        # Add run properties if specified
        if run_properties:
            rPr = OxmlElement('w:rPr')
            if run_properties.get('underline', True):
                u = OxmlElement('w:u')
                u.set(qn('w:val'), 'single')
                rPr.append(u)
            if run_properties.get('color'):
                color_elem = OxmlElement('w:color')
                color_elem.set(qn('w:val'), '0563C1')  # Default hyperlink blue
                rPr.append(color_elem)
            new_run.append(rPr)

        # Add the text
        t = OxmlElement('w:t')
        t.text = text
        new_run.append(t)

        hyperlink.append(new_run)
        p.append(hyperlink)

        return hyperlink

    def write(self, descriptor, style, *, plaintext: str | None = None):
        """
        Write a paragraph for the given descriptor and style.

        CRITICAL: Apply styles in this exact order:
        0. Handle section changes (NEW - from BaseWriter)
        1. Create EMPTY paragraph
        2. Apply style_id (sets base from template)
        3. Add text in NEW run
        4. Apply font overrides to THIS run (overrides style_id fonts)
        5. Apply paragraph properties

        :param descriptor: pattern_descriptor dict from schema
        :param style: merged style dict from style_resolver
        """
        # STEP 0: Handle section changes (columns, orientation, etc.)
        if "section" in style:
            self._handle_section_change(style["section"])

        text = plaintext or descriptor.get("features", {}).get("text", "")

        # STEP 1: Create EMPTY paragraph
        p = self.doc.add_paragraph()

        # STEP 2: Apply style_id (sets base from template)
        if "style_id" in style:
            valid_names = [s.name for s in self.doc.styles]
            if style["style_id"] in valid_names:
                p.style = style["style_id"]

        # Check if this paragraph contains a hyperlink
        font_dict = style.get("font", {})
        hyperlink_url = font_dict.get("hyperlink")

        # STEP 3: Add text in NEW run (or hyperlink)
        if text and hyperlink_url:
            # Add as hyperlink instead of regular run
            self._add_hyperlink(p, hyperlink_url, text, run_properties={'underline': True, 'color': True})
            # Skip regular font application since hyperlink handles it
            run = None
        elif text:
            run = p.add_run(text)
        else:
            run = None

        # STEP 4: Override font on THIS run
        if run and "font" in style:
            font = style["font"]
            if "name" in font:
                run.font.name = font["name"]
            if "size" in font and font["size"]:
                run.font.size = Pt(font["size"])
            if "bold" in font:
                run.font.bold = font["bold"]
            if "italic" in font:
                run.font.italic = font["italic"]
            if "underline" in font:
                run.font.underline = convert_underline_value(font["underline"])
            if "strike" in font:
                run.font.strike = font["strike"]
            if "highlight" in font and font["highlight"]:
                # Map highlight color names to WD_COLOR_INDEX enum
                highlight_map = {
                    "yellow": WD_COLOR_INDEX.YELLOW,
                    "brightGreen": WD_COLOR_INDEX.BRIGHT_GREEN,
                    "turquoise": WD_COLOR_INDEX.TURQUOISE,
                    "pink": WD_COLOR_INDEX.PINK,
                    "blue": WD_COLOR_INDEX.BLUE,
                    "red": WD_COLOR_INDEX.RED,
                    "darkBlue": WD_COLOR_INDEX.DARK_BLUE,
                    "teal": WD_COLOR_INDEX.TEAL,
                    "green": WD_COLOR_INDEX.GREEN,
                    "violet": WD_COLOR_INDEX.VIOLET,
                    "darkRed": WD_COLOR_INDEX.DARK_RED,
                    "darkYellow": WD_COLOR_INDEX.DARK_YELLOW,
                    "gray50": WD_COLOR_INDEX.GRAY_50,
                    "gray25": WD_COLOR_INDEX.GRAY_25,
                }
                highlight_val = font["highlight"]
                if highlight_val in highlight_map:
                    run.font.highlight_color = highlight_map[highlight_val]
            if "color" in font and font["color"]:
                color_val = font["color"]
                if isinstance(color_val, str):
                    # accept "FF0000" or "#FF0000"
                    hex_str = color_val.lstrip("#")
                    run.font.color.rgb = RGBColor.from_string(hex_str)
                elif isinstance(color_val, RGBColor):
                    run.font.color.rgb = color_val
            if "all_caps" in font:
                run.font.all_caps = font["all_caps"]
            if "small_caps" in font:
                run.font.small_caps = font["small_caps"]

        # STEP 5: Paragraph properties
        if "paragraph" in style:
            para = style["paragraph"]
            if "alignment" in para:
                align = para["alignment"].lower()
                if align == "left":
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                elif align == "center":
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                elif align == "right":
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                elif align == "justify":
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

            # Spacing before paragraph (in twips, convert to points)
            if "spacing_before" in para:
                p.paragraph_format.space_before = Pt(para["spacing_before"] / 20)

            # Spacing after paragraph (in twips, convert to points)
            if "spacing_after" in para:
                p.paragraph_format.space_after = Pt(para["spacing_after"] / 20)

            # Line spacing
            if "line_spacing" in para:
                p.paragraph_format.line_spacing = para["line_spacing"]

            # Paragraph shading (background color)
            # Handle both dict {"fill": "color"} and string "color" formats
            if "shading" in para and para["shading"]:
                shading_value = para["shading"]
                if isinstance(shading_value, dict) and "fill" in shading_value:
                    self._apply_paragraph_shading(p, shading_value["fill"])
                elif isinstance(shading_value, str):
                    self._apply_paragraph_shading(p, shading_value)

            # Paragraph borders
            if "borders" in para and para["borders"]:
                self._apply_paragraph_borders(p, para["borders"])

            # Indentation
            if "left_indent" in para:
                p.paragraph_format.left_indent = Pt(para["left_indent"] / 20)
            if "right_indent" in para:
                p.paragraph_format.right_indent = Pt(para["right_indent"] / 20)
            if "first_line_indent" in para:
                p.paragraph_format.first_line_indent = Pt(para["first_line_indent"] / 20)

        return p

    def _apply_paragraph_shading(self, paragraph, color: str):
        """
        Apply background shading to a paragraph.

        :param paragraph: The paragraph to shade
        :param color: Hex color string like "FFFF00" or "#FFFF00"
        """
        # Remove # prefix if present
        hex_color = color.lstrip("#")

        # Get paragraph properties element
        pPr = paragraph._element.get_or_add_pPr()

        # Remove existing shading if present
        existing_shd = pPr.find(qn('w:shd'))
        if existing_shd is not None:
            pPr.remove(existing_shd)

        # Create new shading element
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')  # Pattern type
        shd.set(qn('w:color'), 'auto')  # Foreground color
        shd.set(qn('w:fill'), hex_color)  # Background color

        pPr.append(shd)

    def _apply_paragraph_borders(self, paragraph, borders: dict):
        """
        Apply borders to a paragraph.

        :param paragraph: The paragraph to add borders to
        :param borders: Dict with border definitions for top, bottom, left, right
                       Each border should have: color, size, style (optional)
                       Example: {"bottom": {"color": "FF0000", "size": 6, "style": "single"}}
        """
        # Get paragraph properties element
        pPr = paragraph._element.get_or_add_pPr()

        # Remove existing borders if present
        existing_pBdr = pPr.find(qn('w:pBdr'))
        if existing_pBdr is not None:
            pPr.remove(existing_pBdr)

        # Create new paragraph borders element
        pBdr = OxmlElement('w:pBdr')

        # Define border sides
        border_sides = ['top', 'bottom', 'left', 'right']

        for side in border_sides:
            if side in borders:
                border_spec = borders[side]

                # Create border element for this side
                border_elem = OxmlElement(f'w:{side}')

                # Set border style (default: single line)
                border_style = border_spec.get('style', 'single')
                border_elem.set(qn('w:val'), border_style)

                # Set border color (required)
                if 'color' in border_spec:
                    hex_color = border_spec['color'].lstrip('#')
                    border_elem.set(qn('w:color'), hex_color)
                else:
                    border_elem.set(qn('w:color'), '000000')  # Default to black

                # Set border size in eighths of a point (default: 6 = 0.75pt)
                border_size = border_spec.get('size', 6)
                border_elem.set(qn('w:sz'), str(border_size))

                # Set space between border and text (in points)
                border_space = border_spec.get('space', 1)
                border_elem.set(qn('w:space'), str(border_space))

                pBdr.append(border_elem)

        # Only add pBdr if we have at least one border
        if len(pBdr) > 0:
            pPr.append(pBdr)
