# src/glyph/core/schema_runner/writers/base_writer.py

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.section import WD_SECTION, WD_ORIENT
from docx.shared import Inches


class BaseWriter:
    """
    Base class for all writers with section handling utilities.

    Provides:
    - Section change detection
    - Section creation and property application
    - Utility functions for columns, orientation, margins, page size

    All writers should inherit from this class to gain section handling capabilities.
    """

    def __init__(self, document):
        """
        Initialize base writer.

        Args:
            document: python-docx Document object
        """
        self.doc = document
        self.current_section_props = {}

    def _handle_section_change(self, section_props):
        """
        Handle section property changes by creating new sections as needed.

        This is a utility function that checks if section properties have changed
        and creates a new section with the updated properties if necessary.

        Args:
            section_props: Dict of section properties (columns, orientation, margins, etc.)
        """
        if not self._section_changed(section_props):
            return

        # Get or create section
        if self.doc.paragraphs:
            # There's already content - create a new section
            # Use CONTINUOUS to avoid page breaks unless orientation changes
            needs_page_break = False

            # Check if orientation is changing (requires page break)
            current_orientation = self.current_section_props.get("orientation")
            new_orientation = section_props.get("orientation")
            if current_orientation and new_orientation and current_orientation != new_orientation:
                needs_page_break = True

            # Create section with appropriate break type
            if needs_page_break:
                section = self.doc.add_section(WD_SECTION.NEW_PAGE)
            else:
                section = self.doc.add_section(WD_SECTION.CONTINUOUS)
        else:
            # No content yet - modify the first/default section
            section = self.doc.sections[0]

        # Apply section utilities
        if "columns" in section_props:
            self._apply_columns(section, section_props["columns"])

        if "orientation" in section_props:
            self._apply_orientation(section, section_props["orientation"])

        if "page_width" in section_props or "page_height" in section_props:
            self._apply_page_size(section, section_props)

        if "margin_left" in section_props or "margin_right" in section_props or \
           "margin_top" in section_props or "margin_bottom" in section_props:
            self._apply_margins(section, section_props)

        # Update tracking
        self.current_section_props = section_props.copy()

    def _section_changed(self, new_props):
        """
        Check if section properties differ from current section.

        Args:
            new_props: New section properties dict

        Returns:
            True if properties have changed, False otherwise
        """
        # If no current section props, this is a change
        if not self.current_section_props and new_props:
            return True

        # Compare relevant properties
        # Only check properties that actually affect section layout
        relevant_keys = ["columns", "orientation", "page_width", "page_height",
                        "margin_left", "margin_right", "margin_top", "margin_bottom"]

        for key in relevant_keys:
            if new_props.get(key) != self.current_section_props.get(key):
                return True

        return False

    def _apply_columns(self, section, num_cols):
        """
        Utility function: Apply column layout to section.

        Uses XML manipulation since python-docx doesn't expose columns API.

        Args:
            section: python-docx Section object
            num_cols: Number of columns (1-3)
        """
        sectPr = section._sectPr

        # Remove existing columns element
        cols_elem = sectPr.find(qn("w:cols"))
        if cols_elem is not None:
            sectPr.remove(cols_elem)

        # Add new columns element if > 1
        if num_cols > 1:
            cols = OxmlElement("w:cols")
            cols.set(qn("w:num"), str(num_cols))
            # Equal width columns with default spacing
            cols.set(qn("w:space"), "720")  # 0.5 inch spacing between columns
            sectPr.append(cols)

    def _apply_orientation(self, section, orientation):
        """
        Utility function: Apply page orientation to section.

        Args:
            section: python-docx Section object
            orientation: "portrait" or "landscape"
        """
        if orientation.lower() == "landscape":
            section.orientation = WD_ORIENT.LANDSCAPE
            # Swap width and height for landscape
            section.page_width, section.page_height = section.page_height, section.page_width
        elif orientation.lower() == "portrait":
            section.orientation = WD_ORIENT.PORTRAIT
            # Ensure width < height for portrait
            if section.page_width > section.page_height:
                section.page_width, section.page_height = section.page_height, section.page_width

    def _apply_page_size(self, section, section_props):
        """
        Utility function: Apply page dimensions to section.

        Args:
            section: python-docx Section object
            section_props: Dict with page_width and/or page_height in inches
        """
        if "page_width" in section_props:
            section.page_width = Inches(section_props["page_width"])

        if "page_height" in section_props:
            section.page_height = Inches(section_props["page_height"])

    def _apply_margins(self, section, section_props):
        """
        Utility function: Apply margins to section.

        Args:
            section: python-docx Section object
            section_props: Dict with margin_left, margin_right, margin_top, margin_bottom in inches
        """
        if "margin_left" in section_props:
            section.left_margin = Inches(section_props["margin_left"])

        if "margin_right" in section_props:
            section.right_margin = Inches(section_props["margin_right"])

        if "margin_top" in section_props:
            section.top_margin = Inches(section_props["margin_top"])

        if "margin_bottom" in section_props:
            section.bottom_margin = Inches(section_props["margin_bottom"])
