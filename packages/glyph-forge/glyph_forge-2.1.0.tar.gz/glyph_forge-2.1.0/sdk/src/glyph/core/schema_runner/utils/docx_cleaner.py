from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Twips

def strip_body_content(path: str, global_default: dict | None = None) -> Document:
    """
    Strip body content from source DOCX while preserving section properties and styles.

    CRITICAL: The source DOCX (tagged input) contains:
    - Page size/margins in sectPr
    - Style definitions in styles.xml
    - Theme colors/fonts

    This function PRESERVES these properties and optionally MODIFIES them with global_defaults.

    Args:
        path: Path to source DOCX (e.g., examples/outputs/default/input/docx/resume_<tag>.docx)
        global_default: Optional dict with global_defaults to override section properties

    Returns:
        Document with body content removed but styles/section properties preserved
    """
    # Load the original tagged input DOCX
    doc = Document(path)
    body = doc.element.body

    # CRITICAL: Find the existing sectPr element in the body's children
    # (We can't use body.sectPr property as it may create a new one with defaults)
    original_sectPr = None
    for child in body:
        if child.tag == qn('w:sectPr'):
            original_sectPr = child
            break

    if original_sectPr is None:
        # Fallback: If no sectPr exists, get it from body.sectPr property
        # This creates a new sectPr with default values
        original_sectPr = body.sectPr

    # Remove all children (paragraphs, tables) but keep sectPr
    for child in list(body):
        # Don't remove sectPr - we need to preserve it!
        if child.tag != qn('w:sectPr'):
            body.remove(child)

    # Now modify the ORIGINAL sectPr with global_defaults (if provided)
    if global_default:
        gd = global_default.get("global_defaults", global_default)
        sectPr = original_sectPr

        # Page size - handle both nested and flat structure
        # CRITICAL: Schema values are in TWIPS (1/1440 inch), but python-docx expects EMUs
        # Must convert using Twips() to avoid corruption (12240 twips → 7772400 EMUs)
        page_size = gd.get("page_size", {})
        if "width" in page_size:
            sectPr.pgSz.w = Twips(page_size["width"])
        elif "page_width" in gd:
            sectPr.pgSz.w = Twips(gd["page_width"])

        if "height" in page_size:
            sectPr.pgSz.h = Twips(page_size["height"])
        elif "page_height" in gd:
            sectPr.pgSz.h = Twips(gd["page_height"])

        if "orientation" in gd:
            sectPr.pgSz.orient = gd["orientation"]

        # Margins - handle both nested and flat structure
        # CRITICAL: Margin values also in TWIPS, must convert to EMUs
        margins = gd.get("margins", {})
        if "left" in margins:
            sectPr.pgMar.left = Twips(margins["left"])
        elif "left_margin" in gd:
            sectPr.pgMar.left = Twips(gd["left_margin"])

        if "right" in margins:
            sectPr.pgMar.right = Twips(margins["right"])
        elif "right_margin" in gd:
            sectPr.pgMar.right = Twips(gd["right_margin"])

        if "top" in margins:
            sectPr.pgMar.top = Twips(margins["top"])
        elif "top_margin" in gd:
            sectPr.pgMar.top = Twips(gd["top_margin"])

        if "bottom" in margins:
            sectPr.pgMar.bottom = Twips(margins["bottom"])
        elif "bottom_margin" in gd:
            sectPr.pgMar.bottom = Twips(gd["bottom_margin"])

        # Page borders
        page_borders = gd.get("page_borders")
        if page_borders:
            # Remove existing pgBorders if present
            existing_pgBorders = sectPr.find(qn('w:pgBorders'))
            if existing_pgBorders is not None:
                sectPr.remove(existing_pgBorders)

            # Create new pgBorders element
            pgBorders = OxmlElement('w:pgBorders')

            # Add individual border sides
            for side in ["top", "bottom", "left", "right"]:
                if side in page_borders:
                    border_elem = OxmlElement(f'w:{side}')
                    border_attrs = page_borders[side]

                    # Common border attributes
                    # Attributes from extraction have full namespace prefixes
                    for attr_key, attr_val in border_attrs.items():
                        # Extract the local name from namespaced key if present
                        # e.g., "{http://...}val" -> "val"
                        if attr_key.startswith('{'):
                            # Extract local name after closing brace
                            local_name = attr_key.split('}')[1] if '}' in attr_key else attr_key
                            # Set attribute with proper namespace
                            border_elem.set(qn(f'w:{local_name}'), str(attr_val))
                        else:
                            # Plain attribute name, add w: namespace
                            border_elem.set(qn(f'w:{attr_key}'), str(attr_val))

                    pgBorders.append(border_elem)

            # Insert pgBorders into sectPr (should come before pgSz typically)
            # Find the right position: after cols but before pgSz if present
            pgSz_elem = sectPr.find(qn('w:pgSz'))
            if pgSz_elem is not None:
                # Insert before pgSz
                sectPr.insert(list(sectPr).index(pgSz_elem), pgBorders)
            else:
                # Append to end
                sectPr.append(pgBorders)

        # Vertical alignment
        vertical_alignment = gd.get("vertical_alignment")
        if vertical_alignment:
            # Remove existing vAlign if present
            existing_vAlign = sectPr.find(qn('w:vAlign'))
            if existing_vAlign is not None:
                sectPr.remove(existing_vAlign)

            # Create new vAlign element
            vAlign = OxmlElement('w:vAlign')
            vAlign.set(qn('w:val'), str(vertical_alignment))
            sectPr.append(vAlign)

        # Section break type
        section_type = gd.get("section_type")
        if section_type:
            # Remove existing type if present
            existing_type = sectPr.find(qn('w:type'))
            if existing_type is not None:
                sectPr.remove(existing_type)

            # Create new type element
            # Valid values: continuous, nextPage, nextColumn, evenPage, oddPage
            type_elem = OxmlElement('w:type')
            type_elem.set(qn('w:val'), str(section_type))
            sectPr.append(type_elem)

    # NOTE: sectPr is already in body, don't re-append!
    # The old code was appending a new sectPr, which was wrong.

    return doc