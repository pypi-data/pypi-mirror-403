# src/glyph/core/schema_runner/runner.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional, Union
from pathlib import Path
from docx import Document

from glyph.core.schema_runner.resolvers.style_resolver import resolve_style
from glyph.core.schema_runner.router import SchemaRouter
from glyph.core.schema_runner.utils.docx_cleaner import strip_body_content
from glyph.settings import get_settings

# Plaintext analysis path
from glyph.core.analysis.plaintext.intake import intake_plaintext
from glyph.core.analysis.plaintext.builder import build_emittables_from_plaintext

# Markup integration
from glyph.core.markup.parser import parse_markup
from glyph.core.markup.engine.schema_converter import ast_to_schema


# ==================== PRIORITY SYSTEM ====================
# Default priorities for selector types (0-1000, higher = higher priority)

# Tier 1: Exact Matches (900-1000)
PRIORITY_EXACT = 1000

# Tier 2: Specific Patterns (700-899)
PRIORITY_REGEX_SPECIFIC = 800  # Will be adjusted based on pattern specificity

# Tier 3: Structural Classifications (400-699)
PRIORITY_H_SECTION_N = 600
PRIORITY_H_CONTENTS = 600
PRIORITY_L_ORDERED = 500
PRIORITY_L_BULLET = 500
PRIORITY_L_DEFINITION = 400
PRIORITY_T_BASIC = 600
PRIORITY_T_COMPLEX = 650
PRIORITY_T_DATA = 650

# Tier 4: Generic Classifications (100-399)
PRIORITY_H_SHORT = 300
PRIORITY_H_LONG = 300
PRIORITY_H_SUBTITLE = 250
PRIORITY_P_LEAD = 250
PRIORITY_P_SUMMARY = 250
PRIORITY_P_BODY = 200

# Tier 5: Fallbacks (0-99)
PRIORITY_P_UNKNOWN = 50
PRIORITY_L_UNKNOWN = 50
PRIORITY_DEFAULT = 0

# Context bonuses (added to base priority)
CONTEXT_BONUS_ISOLATED = 50      # Blank lines before/after
CONTEXT_BONUS_TITLE_CASE = 30    # First word title-cased
CONTEXT_BONUS_SHORT = 20         # ≤6 words
CONTEXT_BONUS_ALLCAPS = 20       # All uppercase
CONTEXT_BONUS_IN_SEQUENCE = 30   # Part of numbered sequence
CONTEXT_BONUS_HIGH_SCORE = 10    # Detector score > 0.9


def get_default_priority(type_str: str) -> int:
    """
    Get default priority for a selector type.

    Args:
        type_str: Selector type (e.g., "H-SECTION-N", "L-BULLET-SOLID", "REGEX:pattern")

    Returns:
        Default priority value (0-1000)
    """
    if not type_str or not isinstance(type_str, str):
        return PRIORITY_DEFAULT

    # Exact matches
    if type_str.startswith("EXACT:"):
        return PRIORITY_EXACT

    # Regex patterns (use specificity-based priority)
    if type_str.startswith("REGEX:"):
        return PRIORITY_REGEX_SPECIFIC

    # Headings
    if type_str == "H-SECTION-N":
        return PRIORITY_H_SECTION_N
    if type_str == "H-CONTENTS":
        return PRIORITY_H_CONTENTS
    if type_str == "H-SHORT":
        return PRIORITY_H_SHORT
    if type_str == "H-LONG":
        return PRIORITY_H_LONG
    if type_str == "H-SUBTITLE":
        return PRIORITY_H_SUBTITLE

    # Lists (all variants map to base priorities)
    if type_str.startswith("L-BULLET"):
        return PRIORITY_L_BULLET
    if type_str.startswith("L-ORDERED"):
        return PRIORITY_L_ORDERED
    if type_str == "L-DEFINITION":
        return PRIORITY_L_DEFINITION
    if type_str == "L-CONTINUATION":
        return PRIORITY_L_UNKNOWN  # Low priority
    if type_str == "L-UNKNOWN":
        return PRIORITY_L_UNKNOWN

    # Paragraphs
    if type_str == "P-LEAD":
        return PRIORITY_P_LEAD
    if type_str == "P-SUMMARY":
        return PRIORITY_P_SUMMARY
    if type_str == "P-BODY":
        return PRIORITY_P_BODY
    if type_str == "P-UNKNOWN":
        return PRIORITY_P_UNKNOWN

    # Tables
    if type_str == "T-BASIC":
        return PRIORITY_T_BASIC
    if type_str == "T-COMPLEX":
        return PRIORITY_T_COMPLEX
    if type_str == "T-DATA":
        return PRIORITY_T_DATA

    # Default
    return PRIORITY_DEFAULT


def calculate_context_bonus(text: str, type_str: str) -> int:
    """
    Calculate context-based priority bonus for text.

    Args:
        text: Text to analyze
        type_str: Selector type being evaluated

    Returns:
        Bonus points to add to base priority (0-150)
    """
    bonus = 0

    if not text:
        return bonus

    # Normalize whitespace
    text_clean = ' '.join(text.strip().split())
    words = text_clean.split()
    word_count = len(words)

    # Short text bonus (≤6 words)
    if word_count <= 6:
        bonus += CONTEXT_BONUS_SHORT

    # Remove markers for title case check
    import re
    # Pattern supports hierarchical numbering (1.1.1), roman numerals, letters, bullets
    text_without_marker = re.sub(r'^\s*(\d+(\.\d+)*\.?\s*|\d+\)\s*|[ivxlcdmIVXLCDM]+[\.)]\s*|[a-zA-Z][\.)]\s*|[\-–—•▪◦●·\*■o]\s*)', '', text_clean)

    # Title case bonus (first word capitalized)
    if text_without_marker:
        first_word = text_without_marker.split()[0] if text_without_marker.split() else ""
        if first_word and first_word[0].isupper():
            bonus += CONTEXT_BONUS_TITLE_CASE

    # ALLCAPS bonus (entire text uppercase, minimum 2 words)
    if word_count >= 2 and text_without_marker.isupper():
        bonus += CONTEXT_BONUS_ALLCAPS

    return bonus


def _verbose_print(*args, **kwargs):
    """Print only if SDK_VERBOSE_LOGGING is enabled."""
    settings = get_settings()
    if settings.SDK_VERBOSE_LOGGING:
        print(*args, **kwargs)


def _detect_markup_syntax(text: str) -> bool:
    """
    Detect if text contains Glyph markup syntax.

    Args:
        text: Text to check

    Returns:
        True if markup syntax detected ($glyph markers)
    """
    import re
    # Look for $glyph opening tags (with or without utilities)
    # Pattern: $glyph or $glyph-{utilities}
    markup_pattern = r'\$glyph(?:-|\s|$)'
    return bool(re.search(markup_pattern, text))


class GlyphSchemaRunner:
    """
    Supports three input modes:
      1) Descriptor path (DOCX-oriented) - pattern_descriptors in schema
      2) Plaintext path (lines/text grouped into blocks) - plaintext in schema
      3) Markup path (Glyph markup syntax) - detected in plaintext, auto-converted to descriptors

    Returns list[ (text_or_block_label, descriptor_or_block, style_or_None) ]
    """

    def __init__(
        self,
        schema: Dict[str, Any],
        source_docx: Optional[Union[str, Path]] = None,
        **settings_overrides: Any,
    ):
        self.schema = schema
        # Support both "selectors" (new) and "pattern_descriptors" (deprecated) keys
        # "selectors" takes priority for forward compatibility
        self.pattern_descriptors: List[Dict[str, Any]] = (
            schema.get("selectors") or schema.get("pattern_descriptors") or []
        )
        self.global_defaults: Dict[str, Any] = schema.get("global_defaults", {})
        self.settings = get_settings(**settings_overrides)
        self._markup_descriptors: List[Dict[str, Any]] = []  # Stores inline markup descriptors for hybrid mode

        # 🔍 LOG: Schema received
        _verbose_print("[SDK] " + "="*80)
        _verbose_print(f"[SDK] 🔍 [SCHEMA RECEIVED] Initializing GlyphSchemaRunner")
        _verbose_print(f"[SDK] Document type: {schema.get('document_type', 'N/A')}")
        _verbose_print(f"[SDK] Selectors count: {len(self.pattern_descriptors)}")
        _verbose_print(f"[SDK] Global defaults keys: {list(self.global_defaults.keys())}")

        # Log each pattern descriptor in detail
        for idx, desc in enumerate(self.pattern_descriptors):
            _verbose_print(f"[SDK]   📋 Descriptor [{idx}]:")
            _verbose_print(f"[SDK]     - type: {desc.get('type', 'N/A')}")
            _verbose_print(f"[SDK]     - content: {str(desc.get('content', ''))[:50]}...")

            # Log style properties
            if 'font' in desc:
                _verbose_print(f"[SDK]     - font: {desc['font']}")
            if 'paragraph' in desc:
                _verbose_print(f"[SDK]     - paragraph: {desc['paragraph']}")
            if 'utilities' in desc:
                _verbose_print(f"[SDK]     - utilities: {desc['utilities']}")
            if 'style_id' in desc:
                _verbose_print(f"[SDK]     - style_id: {desc['style_id']}")
            if 'style' in desc:
                _verbose_print(f"[SDK]     - style: {desc['style']}")

        _verbose_print("[SDK] " + "="*80)

        # Handle source DOCX from multiple sources
        if source_docx:
            # Explicit parameter takes priority
            docx_path = source_docx
        elif "source_docx" in schema:
            # File path in schema
            docx_path = schema["source_docx"]
        elif "source_docx_base64" in schema:
            # CRITICAL: Decode base64 embedded DOCX and save to workspace
            import base64
            import tempfile

            # Decode base64 data
            docx_data = base64.b64decode(schema["source_docx_base64"])

            # Determine save location
            tag = schema.get("tag", "temp")

            # Try to save in workspace input directory if available
            if hasattr(self, 'settings') and hasattr(self.settings, 'workspace'):
                workspace = self.settings.workspace
                if hasattr(workspace, 'paths') and "input_docx" in workspace.paths:
                    input_docx_dir = Path(workspace.paths["input_docx"])
                    input_docx_dir.mkdir(parents=True, exist_ok=True)
                    docx_path = input_docx_dir / f"source_{tag}.docx"
                else:
                    # Fallback to temp file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
                    docx_path = Path(temp_file.name)
                    temp_file.close()
            else:
                # Fallback to temp file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
                docx_path = Path(temp_file.name)
                temp_file.close()

            # Write decoded DOCX data to file
            docx_path.write_bytes(docx_data)
            docx_path = str(docx_path)
        else:
            raise ValueError(
                "No source_docx provided. Expected one of:\n"
                "  - source_docx parameter\n"
                "  - schema['source_docx'] (file path)\n"
                "  - schema['source_docx_base64'] (embedded DOCX)"
            )

        # Debug: Verify we're using the correct source DOCX
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Loading source DOCX: {docx_path}")

        # Verify it exists
        if not Path(docx_path).exists():
            raise FileNotFoundError(f"Source DOCX not found: {docx_path}")

        # Now strip body content from the tagged DOCX
        self.document: Document = strip_body_content(str(docx_path), self.global_defaults)
        self.router = SchemaRouter(self.document)

        # Extract plaintext and check for markup BEFORE compiling regex patterns
        self._plaintext_lines: Optional[List[str]] = self._extract_plaintext_lines(schema)
        self._process_markup_if_present(schema)

        # Precompile all regex patterns for performance (after markup processing)
        self._compiled_regexes: Dict[Tuple[int, str], Any] = {}
        self._precompile_regex_patterns()

    def _process_markup_if_present(self, schema: Dict[str, Any]) -> None:
        """
        Detect and process Glyph markup syntax in plaintext.

        If plaintext contains $glyph markers, parse it as markup and convert
        ONLY explicit markup blocks to descriptors. Plaintext outside $glyph
        wrappers is preserved and will be matched against schema pattern_descriptors.

        This enables hybrid mode where:
        - $glyph wrapped content uses inline markup styling
        - Plaintext outside wrappers uses schema pattern matching
        - Schema styling remains active throughout the document

        Args:
            schema: The schema dict to check and potentially modify
        """
        import logging
        logger = logging.getLogger(__name__)

        # Extract plaintext text if available
        plaintext_text = None

        if isinstance(schema.get("plaintext_text"), str):
            plaintext_text = schema["plaintext_text"]
        elif isinstance(schema.get("plaintext"), dict):
            pt = schema["plaintext"]
            if isinstance(pt.get("text"), str):
                plaintext_text = pt["text"]
            elif pt.get("path"):
                path = Path(pt["path"])
                if path.exists():
                    plaintext_text = path.read_text(encoding="utf-8")

        # Check for markup syntax
        if plaintext_text and _detect_markup_syntax(plaintext_text):
            logger.info("Detected Glyph markup syntax in plaintext - enabling hybrid mode")

            try:
                # Parse markup to AST
                ast = parse_markup(plaintext_text)

                # Convert AST to schema format
                # Note: Don't pass template_path here as it's already in schema
                markup_schema = ast_to_schema(ast, template_path=None, tag=schema.get("tag", "markup"))

                # Extract markup descriptors (support both "selectors" and "pattern_descriptors")
                markup_descriptors = (
                    markup_schema.get("selectors") or markup_schema.get("pattern_descriptors") or []
                )

                if markup_descriptors:
                    # CRITICAL FIX: Store markup descriptors separately for hybrid processing
                    # Do NOT replace pattern_descriptors - keep schema patterns active!
                    self._markup_descriptors = markup_descriptors

                    # Keep original pattern_descriptors from schema (for pattern matching)
                    # self.pattern_descriptors already set in __init__

                    # Clear plaintext_lines to force hybrid descriptor mode
                    self._plaintext_lines = None

                    logger.info(
                        f"Enabled hybrid mode: {len(markup_descriptors)} markup selectors + "
                        f"{len(self.pattern_descriptors)} schema selectors"
                    )

            except Exception as e:
                # Enhanced error reporting for markup parsing failures
                error_location = ""
                if hasattr(e, 'line') and hasattr(e, 'col'):
                    error_location = f" at line {e.line}, column {e.col}"
                elif hasattr(e, 'line'):
                    error_location = f" at line {e.line}"

                logger.error(f"Failed to parse markup syntax: {e}{error_location}")

                # Log context for debugging (first 200 chars of markup)
                if plaintext_text:
                    context = plaintext_text[:200] + "..." if len(plaintext_text) > 200 else plaintext_text
                    logger.error(f"Markup context: {context}")

                # Check if strict mode is enabled (raises on markup errors)
                strict_mode = getattr(self.settings, 'STRICT_MARKUP_MODE', False)
                if strict_mode:
                    raise ValueError(f"Markup parsing failed in strict mode: {e}{error_location}") from e

                logger.warning("Falling back to plaintext mode")

    def _precompile_regex_patterns(self):
        """
        Precompile all regex patterns at initialization for performance.

        Validates patterns and fails fast if any are invalid.
        Stores compiled regex objects with descriptor index for O(1) lookup.

        Raises:
            ValueError: If any regex pattern is invalid
        """
        import re
        import logging
        logger = logging.getLogger(__name__)

        for i, desc in enumerate(self.pattern_descriptors):
            # Get pattern from type or heuristic field
            pattern_value = desc.get("type") or desc.get("heuristic")

            if pattern_value:
                # Handle array of patterns
                if isinstance(pattern_value, list):
                    for j, p in enumerate(pattern_value):
                        if isinstance(p, str) and p.startswith("REGEX:"):
                            regex_str = p[6:].strip()
                            try:
                                compiled = re.compile(regex_str)
                                # Store with (descriptor_index, pattern_index) key
                                self._compiled_regexes[(i, f"type_{j}")] = compiled
                                logger.debug(f"Precompiled regex pattern [{i}][{j}]: {regex_str}")
                            except re.error as e:
                                raise ValueError(
                                    f"Invalid REGEX pattern in descriptor {i}, pattern {j}: "
                                    f"'{regex_str}' - {e}"
                                )
                # Handle single string pattern
                elif isinstance(pattern_value, str) and pattern_value.startswith("REGEX:"):
                    regex_str = pattern_value[6:].strip()
                    try:
                        compiled = re.compile(regex_str)
                        # Store with descriptor index
                        self._compiled_regexes[(i, "type")] = compiled
                        logger.debug(f"Precompiled regex pattern [{i}]: {regex_str}")
                    except re.error as e:
                        raise ValueError(
                            f"Invalid REGEX pattern in descriptor {i}: '{regex_str}' - {e}"
                        )

            # Check legacy regex field
            regex_str = desc.get("regex")
            if regex_str:
                try:
                    compiled = re.compile(regex_str)
                    self._compiled_regexes[(i, "regex")] = compiled
                    logger.debug(f"Precompiled legacy regex [{i}]: {regex_str}")
                except re.error as e:
                    raise ValueError(
                        f"Invalid regex field in descriptor {i}: '{regex_str}' - {e}"
                    )

    def run(self) -> List[Tuple[str, Dict[str, Any], Optional[Dict[str, Any]]]]:
        if self._plaintext_lines is not None and len(self._plaintext_lines) > 0:
            return self._run_plaintext_path(self._plaintext_lines)
        return self._run_descriptor_path()

    def save(self, output_path: Union[str, Path], tag: Optional[str] = None) -> str:
        """
        Save the document with optional tag in filename.
        
        :param output_path: Base output path
        :param tag: Optional tag to include in filename
        :return: Actual path where file was saved
        """
        output_path = Path(output_path)
        
        if tag:
            # Insert tag before file extension
            name = output_path.stem
            suffix = output_path.suffix
            tagged_name = f"{name}_{tag}{suffix}"
            actual_path = output_path.parent / tagged_name
        else:
            actual_path = output_path
            
        self.document.save(str(actual_path))
        return str(actual_path)

    # -------- Descriptor (DOCX) path --------
    def _run_descriptor_path(self) -> List[Tuple[str, Dict[str, Any], Dict[str, Any]]]:
        import logging
        logger = logging.getLogger(__name__)

        # Determine which descriptors to process
        descriptors_to_process = self._markup_descriptors if self._markup_descriptors else self.pattern_descriptors
        is_hybrid_mode = len(self._markup_descriptors) > 0

        _verbose_print("[SDK] " + "="*80)
        _verbose_print(f"[SDK] 🔨 [PROCESSING DESCRIPTORS] Starting descriptor path")
        _verbose_print(f"[SDK] Mode: {'HYBRID (markup + schema)' if is_hybrid_mode else 'SCHEMA ONLY'}")
        _verbose_print(f"[SDK] Total descriptors to process: {len(descriptors_to_process)}")
        if is_hybrid_mode:
            _verbose_print(f"[SDK] Schema pattern rules available: {len(self.pattern_descriptors)}")
        _verbose_print("[SDK] " + "="*80)

        results: List[Tuple[str, Dict[str, Any], Dict[str, Any]]] = []
        docx_styles = {s.name: s for s in self.document.styles}

        for idx, desc in enumerate(descriptors_to_process):
            _verbose_print(f"")
            _verbose_print(f"[SDK] 📋 [DESCRIPTOR {idx}] Processing...")
            _verbose_print(f"[SDK]   Type: {desc.get('type', 'N/A')}")

            line_text = desc.get("features", {}).get("text", "") or ""
            _verbose_print(f"[SDK]   Content: {line_text[:80]}...")

            # HYBRID MODE: Check if this is an implicit block (no explicit styling from markup)
            # If so, match it against schema pattern_descriptors
            if is_hybrid_mode and self._is_implicit_markup_block(desc):
                _verbose_print(f"[SDK]   🔍 Implicit block detected - checking for multi-line paragraph...")

                # CRITICAL FIX: Multi-line paragraphs need to be split and processed line-by-line
                # The markup parser groups consecutive lines into paragraphs, but schema
                # pattern matching expects individual lines (like plaintext mode)
                if "\n" in line_text:
                    _verbose_print(f"[SDK]   📝 Multi-line paragraph detected - splitting into individual lines...")
                    # Split paragraph into individual lines and process each
                    lines = [l.strip() for l in line_text.split("\n") if l.strip()]

                    for line_idx, single_line in enumerate(lines):
                        _verbose_print(f"[SDK]   🔍 Line {line_idx + 1}/{len(lines)}: '{single_line[:50]}...'")
                        matched_desc = self._match_plaintext_to_pattern(single_line)
                        if matched_desc:
                            _verbose_print(f"[SDK]   ✅ Matched schema pattern: {matched_desc.get('type', 'N/A')}")
                            # Create a single-line descriptor for this line
                            line_desc = self._merge_descriptors(
                                markup_desc={"features": {"text": single_line}, "type": "P-NORMAL", "style": {}},
                                schema_desc=matched_desc
                            )
                        else:
                            # No match - try fallback
                            _verbose_print(f"[SDK]   ⚠️ No schema pattern match for line - looking for fallback...")
                            fallback_desc = self._find_fallback_descriptor()
                            if fallback_desc:
                                _verbose_print(f"[SDK]   ✅ Using P-NORMAL fallback from schema")
                                line_desc = self._merge_descriptors(
                                    markup_desc={"features": {"text": single_line}, "type": "P-NORMAL", "style": {}},
                                    schema_desc=fallback_desc
                                )
                            else:
                                _verbose_print(f"[SDK]   ⚠️ No fallback found - using markup default")
                                line_desc = {"features": {"text": single_line}, "type": "P-NORMAL", "style": {"style_id": "Normal"}}

                        # Resolve and dispatch this line
                        line_style_obj = resolve_style(
                            descriptor=line_desc,
                            schema=self.schema,
                            global_defaults=self.global_defaults,
                            docx_styles=docx_styles,
                        )
                        self.router.dispatch(line_desc, line_style_obj, plaintext=single_line)
                        results.append((single_line, line_desc, line_style_obj))

                    # Skip normal processing for this descriptor (we've processed all lines)
                    continue
                else:
                    # Single-line implicit block - match normally
                    _verbose_print(f"[SDK]   🔍 Single-line implicit block - matching against schema patterns...")
                    matched_desc = self._match_plaintext_to_pattern(line_text)
                    if matched_desc:
                        _verbose_print(f"[SDK]   ✅ Matched schema pattern: {matched_desc.get('type', 'N/A')}")
                        desc = self._merge_descriptors(markup_desc=desc, schema_desc=matched_desc)
                    else:
                        # No match - try to find a P-NORMAL fallback in schema
                        _verbose_print(f"[SDK]   ⚠️ No schema pattern match - looking for P-NORMAL fallback...")
                        fallback_desc = self._find_fallback_descriptor()
                        if fallback_desc:
                            _verbose_print(f"[SDK]   ✅ Using P-NORMAL fallback from schema")
                            desc = self._merge_descriptors(markup_desc=desc, schema_desc=fallback_desc)
                        else:
                            _verbose_print(f"[SDK]   ⚠️ No P-NORMAL fallback found - using markup default")

            # Log INPUT properties
            _verbose_print(f"[SDK]   INPUT PROPERTIES:")
            if 'font' in desc:
                _verbose_print(f"[SDK]     ✓ font (inline): {desc['font']}")
            if 'paragraph' in desc:
                _verbose_print(f"[SDK]     ✓ paragraph (inline): {desc['paragraph']}")
            if 'utilities' in desc:
                _verbose_print(f"[SDK]     ✓ utilities: {desc['utilities']}")
            if 'style_id' in desc:
                _verbose_print(f"[SDK]     ✓ style_id: {desc['style_id']}")
            if 'style' in desc:
                _verbose_print(f"[SDK]     ✓ style: {desc['style']}")

            # Call resolve_style and log the result
            _verbose_print(f"[SDK]   🔄 Calling resolve_style...")
            style_obj = resolve_style(
                descriptor=desc,
                schema=self.schema,
                global_defaults=self.global_defaults,
                docx_styles=docx_styles,
            )

            # Log OUTPUT style object
            _verbose_print(f"[SDK]   OUTPUT STYLE OBJECT:")
            if style_obj:
                for key, value in style_obj.items():
                    _verbose_print(f"[SDK]     ✓ {key}: {value}")
            else:
                _verbose_print(f"[SDK]     ⚠️ style_obj is None!")

            # ALWAYS pass plaintext (line_text) to writers
            _verbose_print(f"[SDK]   ✅ Dispatching to router...")
            self.router.dispatch(desc, style_obj, plaintext=line_text)
            results.append((line_text, desc, style_obj))

        _verbose_print(f"")
        _verbose_print("[SDK] " + "="*80)
        _verbose_print(f"[SDK] ✅ [PROCESSING COMPLETE] Processed {len(results)} descriptors")
        _verbose_print("[SDK] " + "="*80)
        return results

    # -------- Hybrid mode helpers --------
    def _find_fallback_descriptor(self) -> Optional[Dict[str, Any]]:
        """
        Find a fallback descriptor for unmatched implicit blocks.

        Looks for a P-NORMAL or P-BODY descriptor in the schema to use as
        a catch-all for paragraphs that don't match specific patterns.

        Returns:
            Fallback descriptor or None
        """
        # Look for P-NORMAL first (most common fallback)
        for desc in self.pattern_descriptors:
            if desc.get("type") == "P-NORMAL":
                return desc

        # Try P-BODY as secondary fallback
        for desc in self.pattern_descriptors:
            if desc.get("type") == "P-BODY":
                return desc

        # No fallback found
        return None

    def _is_implicit_markup_block(self, desc: Dict[str, Any]) -> bool:
        """
        Detect if a descriptor is from an implicit block (plaintext outside $glyph wrappers).

        Implicit blocks have no explicit styling from markup - they should fall back
        to schema pattern matching.

        Args:
            desc: Descriptor to check

        Returns:
            True if this is an implicit block with no explicit styling
        """
        # Check if descriptor has explicit styling from markup
        style = desc.get("style", {})

        # If it has font or paragraph properties, it's explicit markup
        if style.get("font") or style.get("paragraph"):
            return False

        # If it has a style_id that's not the default "Normal", it's explicit
        style_id = style.get("style_id")
        if style_id and style_id not in ("Normal", "Body Text", "P-NORMAL"):
            return False

        # If type is P-NORMAL (the default) and no styling, it's implicit
        if desc.get("type") == "P-NORMAL":
            return True

        # Check if type suggests explicit markup (headings, lists, etc.)
        desc_type = desc.get("type", "")
        if desc_type.startswith(("H1", "H2", "H3", "H4", "H5", "H6", "L-", "T-", "R")):
            return False

        # Default to implicit if no clear indicators
        return True

    def _merge_descriptors(
        self, markup_desc: Dict[str, Any], schema_desc: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge schema pattern descriptor with markup descriptor.

        The markup descriptor provides the text, while the schema descriptor
        provides the styling. Schema styling takes precedence for implicit blocks.

        Args:
            markup_desc: Descriptor from markup (contains text)
            schema_desc: Descriptor from schema pattern match (contains styling)

        Returns:
            Merged descriptor with text from markup and styling from schema
        """
        import copy

        # Start with a copy of the markup descriptor
        merged = copy.deepcopy(markup_desc)

        # Override type from schema pattern
        if "type" in schema_desc:
            merged["type"] = schema_desc["type"]

        # Merge style - schema style takes precedence for implicit blocks
        if "style" in schema_desc:
            schema_style = copy.deepcopy(schema_desc["style"])
            markup_style = merged.get("style", {})

            # Schema style takes full precedence for implicit blocks
            merged["style"] = schema_style

            # Preserve any section properties from markup (page layout)
            if "section" in markup_style:
                merged["style"]["section"] = markup_style["section"]

        # Preserve features from markup descriptor (text content)
        # Already in merged since we started with markup_desc

        return merged

    # -------- Pattern matching helper --------
    def _calculate_pattern_score(self, pattern: str) -> float:
        """
        Calculate automatic score based on pattern specificity.

        Scoring breakdown:
        - Exact quantifiers {n}: +3 each
        - Range quantifiers {n,m}: +2 each
        - Greedy quantifiers +, *, ?: +1 each
        - Anchors ^, $: +2 each
        - Literal characters: +0.5 each
        - Wildcards .*, .+: -2, -1 penalty
        - Special structures (email, URL, phone, date): +5 bonus
        """
        import re
        import logging
        logger = logging.getLogger(__name__)

        score = 0.0

        # Exact quantifiers: {n}
        exact_quant = re.findall(r'\{\\d+\}', pattern)
        score += len(exact_quant) * 3

        # Range quantifiers: {n,m} or {n,}
        range_quant = re.findall(r'\{\\d+,\\d*\}', pattern)
        score += len(range_quant) * 2

        # Greedy quantifiers: +, *, ? (not preceded by backslash)
        greedy = re.findall(r'(?<!\\)[+*?]', pattern)
        score += len(greedy) * 1

        # Anchors: ^, $
        if pattern.startswith('^'):
            score += 2
        if pattern.endswith('$'):
            score += 2

        # Literal characters (alphanumeric and common punctuation)
        # Count characters that aren't regex metacharacters
        literals = re.findall(r'[a-zA-Z0-9@/:.\s\-]', pattern)
        score += len(literals) * 0.5

        # Wildcards penalty
        score -= pattern.count('.*') * 2
        score -= pattern.count('.+') * 1

        # Special structure bonuses
        if '@' in pattern and ('\\.' in pattern or '.' in pattern):
            score += 5  # Email-like pattern
            logger.debug(f"Email pattern detected: +5 bonus")

        if 'https?' in pattern:
            score += 5  # URL pattern
            logger.debug(f"URL pattern detected: +5 bonus")

        if r'\d{3}' in pattern and r'\d{4}' in pattern:
            score += 3  # Phone/date-like pattern
            logger.debug(f"Phone/date pattern detected: +3 bonus")

        if pattern.count(r'\d{2}') >= 2:
            score += 3  # Date-like pattern (multiple 2-digit sequences)
            logger.debug(f"Date-like pattern detected: +3 bonus")

        logger.debug(f"Pattern score calculated: {pattern} → {score}")
        return score

    def _classify_text_heuristically(self, text: str) -> Optional[str]:
        """
        Classify text using heuristic detectors to determine its form.
        Returns a label like "H-SHORT", "H-LONG", "P-BODY", "P-LEAD", "L-BULLET-SOLID", etc.

        Uses context-aware disambiguation to handle pattern conflicts between
        H-SECTION-N (numbered headings) and L-ORDERED (numbered lists).
        """
        import logging
        from glyph.core.analysis.forms.headings import guess_heading_form, HeadingForm
        from glyph.core.analysis.forms.paragraphs import classify_paragraph_line
        from glyph.core.analysis.detectors.heuristics.heading_detector import score_heading
        from glyph.core.analysis.detectors.heuristics.list_detector import score_list_line
        from glyph.core.analysis.features import extract_line_features

        logger = logging.getLogger(__name__)

        # Get both heading and list classifications
        heading_score = 0.0
        heading_form = None
        list_label = None
        list_score = 0.0

        try:
            feats = extract_line_features(text)
            heading_score = score_heading(text, feats)
            heading_form = guess_heading_form(text)
        except Exception as e:
            logger.debug(f"Heading classification failed: {e}")

        try:
            list_label, list_score = score_list_line(text)
        except Exception as e:
            logger.debug(f"List classification failed: {e}")

        # PRIORITY 0: Special handling for hierarchical section numbers
        # If text starts with hierarchical numbering (X.Y or X.Y.Z), it's a STRONG signal for H-SECTION-N
        # Even if heading_score is low (which happens for longer headings)
        import re
        hierarchical_pattern = re.compile(r'^\s*\d+\.\d+')  # Matches 1.1, 2.3, 1.2.3, etc. (not just "1.")
        has_hierarchical_number = bool(hierarchical_pattern.match(text))

        if has_hierarchical_number and heading_form == HeadingForm.H_SECTION_N and list_label and list_label.startswith("L-ORDERED"):
            # Hierarchical numbering detected - apply lenient disambiguation
            words = text.split()
            word_count = len(words)

            # Strip marker for title case check
            text_without_marker = re.sub(r'^\s*(\d+(\.\d+)*\.?\s*|\d+\)\s*|[ivxlcdmIVXLCDM]+[\.)]\s*|[a-zA-Z][\.)]\s*)', '', text)
            first_word = text_without_marker.split()[0] if text_without_marker.split() else ""
            is_title_case = first_word and first_word[0].isupper()

            # More lenient rules for hierarchical section numbers:
            # - Allow up to 12 words (academic headings can be long)
            # - Title case required (but this is almost always true for section headings)
            if word_count <= 12 and is_title_case:
                logger.debug(f"Hierarchical section number detected: {heading_form.value} (words={word_count}, title_case={is_title_case})")
                return heading_form.value
            # If title case but too long, still prefer heading if not obviously a list
            elif is_title_case and word_count <= 15:
                logger.debug(f"Long hierarchical section: {heading_form.value} (words={word_count})")
                return heading_form.value

        # PRIORITY 1: Both heading and list detected - disambiguate using context
        if heading_score >= 0.55 and list_score >= 0.55 and heading_form:
            # Pattern conflict: H-SECTION-N vs L-ORDERED-*
            # Example: "1. Introduction" could be heading or list
            if heading_form == HeadingForm.H_SECTION_N and list_label and list_label.startswith("L-ORDERED"):
                # Disambiguation heuristics:
                # - Headings are typically SHORT (≤6 words)
                # - Headings use TITLE CASE or sentence case
                # - Lists are typically LONGER or lowercase
                words = text.split()
                word_count = len(words)

                # Remove the number/marker for analysis
                text_without_marker = text
                import re
                # Pattern supports hierarchical numbering (1.1.1), roman numerals, letters
                text_without_marker = re.sub(r'^\s*(\d+(\.\d+)*\.?\s*|\d+\)\s*|[ivxlcdmIVXLCDM]+[\.)]\s*|[a-zA-Z][\.)]\s*)', '', text)

                # Check if first word after marker is title-cased
                first_word_after_marker = text_without_marker.split()[0] if text_without_marker.split() else ""
                is_title_case = first_word_after_marker and first_word_after_marker[0].isupper()

                # Decision logic:
                # Title-cased + reasonable length = heading (e.g., "1. Introduction")
                # Long or lowercase = list (e.g., "1. this is a longer list item")
                # Increased from 6 to 10 words to support longer academic headings
                if word_count <= 10 and is_title_case:
                    logger.debug(f"Disambiguated as HEADING: {heading_form.value} (words={word_count}, title_case={is_title_case})")
                    return heading_form.value
                elif heading_score > list_score + 0.1:  # Heading significantly higher
                    logger.debug(f"Disambiguated as HEADING: {heading_form.value} (score advantage: {heading_score:.2f} vs {list_score:.2f})")
                    return heading_form.value
                else:
                    logger.debug(f"Disambiguated as LIST: {list_label} (long={word_count > 6} or score advantage)")
                    return list_label

            # No conflict - use highest score
            if heading_score >= list_score:
                logger.debug(f"Classified as heading: {heading_form.value} (score={heading_score:.2f} >= {list_score:.2f})")
                return heading_form.value
            else:
                logger.debug(f"Classified as list: {list_label} (score={list_score:.2f} > {heading_score:.2f})")
                return list_label

        # PRIORITY 2: Only heading detected
        if heading_score >= 0.55 and heading_form:
            logger.debug(f"Classified as heading: {heading_form.value} (score={heading_score:.2f})")
            return heading_form.value

        # PRIORITY 3: Only list detected
        if list_score >= 0.55 and list_label:
            logger.debug(f"Classified as list: {list_label} (score={list_score:.2f})")
            return list_label

        # PRIORITY 4: Fallback to paragraph classification
        try:
            para_form = classify_paragraph_line(text)
            logger.debug(f"Classified as paragraph: {para_form.value}")
            return para_form.value
        except Exception as e:
            logger.debug(f"Paragraph classification failed: {e}")

        return None

    def _match_plaintext_to_pattern(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Match plaintext against pattern_descriptors using multiple strategies with hybrid scoring.

        Priority hierarchy:
        1. type: "EXACT:Title" or ["EXACT:Title1", "EXACT:Title2"] - Exact title matching (always wins)
        2. type: "REGEX:^pattern$" - Custom regex with hybrid scoring:
           - Manual priority (if specified via "priority" field)
           - Auto-calculated score based on pattern specificity
        3. type: "H-SHORT", "P-BODY", etc. - Heuristic classification
        4. heuristic: (deprecated, backward compatibility) - Falls back to old behavior
        5. regex: "^pattern$" - Legacy regex support (backward compatibility)

        Hybrid scoring selects the BEST matching REGEX pattern, not just the first.
        """
        import logging
        from glyph.core.analysis.detectors.exact_matcher import find_exact_matches

        logger = logging.getLogger(__name__)

        # Normalize whitespace: strip and collapse multiple spaces to single space
        text_normalized = ' '.join(text.strip().split())

        # Helper to extract pattern from type or heuristic field (with type taking priority)
        def get_pattern_value(desc):
            """
            Get pattern value from type (new) or heuristic (backward compat).

            If type is a classification (H-SHORT, P-BODY, etc.) or pattern (EXACT:, REGEX:),
            use it. Otherwise, fallback to heuristic for backward compatibility.
            """
            type_val = desc.get("type")
            heuristic_val = desc.get("heuristic")

            # Heading classifications (from headings.py)
            HEADING_CLASSIFICATIONS = {"H-SHORT", "H-LONG", "H-SECTION-N", "H-CONTENTS", "H-SUBTITLE"}

            # Paragraph classifications (from paragraphs.py)
            PARAGRAPH_CLASSIFICATIONS = {"P-BODY", "P-LEAD", "P-SUMMARY", "P-UNKNOWN"}

            # List classifications (from list_detector.py)
            LIST_CLASSIFICATIONS = {
                # Generic types
                "L-BULLET", "L-ORDERED", "L-DEFINITION", "L-CONTINUATION", "L-UNKNOWN",
                # Granular bullet types
                "L-BULLET-SOLID", "L-BULLET-HOLLOW", "L-BULLET-SQUARE",
                # Granular ordered types
                "L-ORDERED-DOTTED", "L-ORDERED-PARA-NUM", "L-ORDERED-ROMAN-UPPER",
                "L-ORDERED-ALPHA-UPPER", "L-ORDERED-ALPHA-LOWER-PAREN",
                "L-ORDERED-ALPHA-LOWER-DOT", "L-ORDERED-ROMAN-LOWER"
            }

            # If type exists and is either:
            # 1. A pattern (EXACT:, REGEX:)
            # 2. A classification (H-SHORT, P-BODY, L-BULLET-SOLID, etc.)
            # 3. An array (for multiple EXACT/REGEX matches)
            # Then use it
            if type_val:
                if isinstance(type_val, list):
                    return type_val
                elif isinstance(type_val, str):
                    if (type_val.startswith("EXACT:") or
                        type_val.startswith("REGEX:") or
                        type_val in HEADING_CLASSIFICATIONS or
                        type_val in PARAGRAPH_CLASSIFICATIONS or
                        type_val in LIST_CLASSIFICATIONS):
                        return type_val

            # DEPRECATED: Fallback to heuristic (backward compatibility)
            if heuristic_val:
                logger.warning(
                    f"DEPRECATED: 'heuristic' field is deprecated and will be removed in a future version. "
                    f"Use 'type' field instead. Found heuristic='{heuristic_val}' in descriptor with type='{type_val}'"
                )
            return heuristic_val

        # PRIORITY 1: Check for EXACT matches (always win, highest priority)
        for desc in self.pattern_descriptors:
            pattern_value = get_pattern_value(desc)

            # Collect exact titles from pattern value (string or array)
            exact_titles = []

            if pattern_value:
                # Handle array of patterns
                if isinstance(pattern_value, list):
                    for p in pattern_value:
                        if isinstance(p, str) and p.startswith("EXACT:"):
                            exact_titles.append(p[6:].strip())
                # Handle single string pattern
                elif isinstance(pattern_value, str) and pattern_value.startswith("EXACT:"):
                    exact_titles.append(pattern_value[6:].strip())

            # Check for matches if we have any exact titles
            if exact_titles:
                matches = find_exact_matches([text_normalized], exact_titles, case_insensitive=True)
                if matches:
                    logger.debug(f"EXACT match found: '{matches[0].title}' for text '{text_normalized[:50]}'")
                    return desc

        # PRIORITY 2: Collect all REGEX matches with hybrid scoring
        # Uses precompiled regex objects for performance
        regex_matches = []

        for i, desc in enumerate(self.pattern_descriptors):
            pattern_value = get_pattern_value(desc)

            # Check for REGEX patterns (single or array)
            if pattern_value:
                # Handle array of patterns
                if isinstance(pattern_value, list):
                    for j, p in enumerate(pattern_value):
                        if isinstance(p, str) and p.startswith("REGEX:"):
                            # Look up precompiled regex
                            compiled_regex = self._compiled_regexes.get((i, f"type_{j}"))
                            if compiled_regex and compiled_regex.match(text_normalized):
                                regex_str = p[6:].strip()
                                # Hybrid scoring: use manual priority if provided, else auto-calculate
                                if "priority" in desc:
                                    score = float(desc["priority"])
                                    match_type = "manual"
                                    logger.debug(f"REGEX match (manual priority): {regex_str} | score={score}")
                                else:
                                    score = self._calculate_pattern_score(regex_str)
                                    match_type = "auto"
                                    logger.debug(f"REGEX match (auto score): {regex_str} | score={score}")

                                regex_matches.append({
                                    "score": score,
                                    "descriptor": desc,
                                    "pattern": regex_str,
                                    "match_type": match_type
                                })
                                # Only take first matching pattern from this descriptor
                                break
                # Handle single string pattern
                elif isinstance(pattern_value, str) and pattern_value.startswith("REGEX:"):
                    # Look up precompiled regex
                    compiled_regex = self._compiled_regexes.get((i, "type"))
                    if compiled_regex and compiled_regex.match(text_normalized):
                        regex_str = pattern_value[6:].strip()
                        # Hybrid scoring: use manual priority if provided, else auto-calculate
                        if "priority" in desc:
                            score = float(desc["priority"])
                            match_type = "manual"
                            logger.debug(f"REGEX match (manual priority): {regex_str} | score={score}")
                        else:
                            score = self._calculate_pattern_score(regex_str)
                            match_type = "auto"
                            logger.debug(f"REGEX match (auto score): {regex_str} | score={score}")

                        regex_matches.append({
                            "score": score,
                            "descriptor": desc,
                            "pattern": regex_str,
                            "match_type": match_type
                        })

        # Return highest-scoring REGEX match
        if regex_matches:
            best_match = max(regex_matches, key=lambda m: m["score"])
            logger.info(
                f"Best REGEX match for '{text_normalized[:50]}': "
                f"pattern={best_match['pattern']} | "
                f"score={best_match['score']} ({best_match['match_type']})"
            )

            # Log all matches if there are multiple (helpful for debugging)
            if len(regex_matches) > 1:
                logger.debug(f"All REGEX matches ({len(regex_matches)}):")
                for m in sorted(regex_matches, key=lambda x: -x["score"]):
                    logger.debug(
                        f"  - score={m['score']} ({m['match_type']}): {m['pattern']}"
                    )

            return best_match["descriptor"]

        # PRIORITY 3: Heuristic classification (H-SHORT, P-BODY, L-BULLET-SOLID, etc.)
        # Classify the text and collect ALL matching descriptors with priorities
        classified_label = self._classify_text_heuristically(text_normalized)
        heuristic_matches = []

        if classified_label:
            for desc in self.pattern_descriptors:
                pattern_value = get_pattern_value(desc)
                if pattern_value and isinstance(pattern_value, str):
                    # Skip if already handled by EXACT: or REGEX:
                    if pattern_value.startswith("EXACT:") or pattern_value.startswith("REGEX:"):
                        continue

                    # Match against the classification label (case-insensitive)
                    if pattern_value.upper() == classified_label.upper():
                        # Calculate priority for this match
                        base_priority = desc.get("priority")
                        if base_priority is None:
                            base_priority = get_default_priority(pattern_value)

                        # Add context bonus
                        context_bonus = calculate_context_bonus(text_normalized, pattern_value)
                        final_priority = base_priority + context_bonus

                        heuristic_matches.append({
                            "priority": final_priority,
                            "descriptor": desc,
                            "classified_label": classified_label,
                            "base_priority": base_priority,
                            "context_bonus": context_bonus
                        })

                        logger.debug(
                            f"Heuristic match: {classified_label} | "
                            f"priority={final_priority} (base={base_priority}, context={context_bonus})"
                        )

        # PRIORITY 4: Check regex field (legacy/backward compatibility)
        # Uses precompiled regex objects for performance
        legacy_matches = []
        for i, desc in enumerate(self.pattern_descriptors):
            regex_pattern = desc.get("regex")
            if regex_pattern:
                # Look up precompiled regex
                compiled_regex = self._compiled_regexes.get((i, "regex"))
                if compiled_regex and compiled_regex.match(text_normalized):
                    # Use same priority system
                    base_priority = desc.get("priority")
                    if base_priority is None:
                        base_priority = get_default_priority(desc.get("type", ""))

                    context_bonus = calculate_context_bonus(text_normalized, desc.get("type", ""))
                    final_priority = base_priority + context_bonus

                    legacy_matches.append({
                        "priority": final_priority,
                        "descriptor": desc,
                        "regex_pattern": regex_pattern
                    })

                    logger.debug(f"Legacy regex match: {regex_pattern} | priority={final_priority}")

        # FINAL SELECTION: Choose highest priority match across all categories
        all_matches = heuristic_matches + legacy_matches

        if all_matches:
            best_match = max(all_matches, key=lambda m: m["priority"])
            logger.info(
                f"Selected best match for '{text_normalized[:50]}': "
                f"priority={best_match['priority']}, "
                f"type={best_match['descriptor'].get('type', 'N/A')}"
            )
            return best_match["descriptor"]

        return None

    def _match_list_item_to_pattern(
        self, text: str, item_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Match list items to pattern descriptors with type-aware matching.

        Priority hierarchy:
        0. Disambiguation: Check if this "list" is actually a heading (H-SECTION-N vs L-ORDERED)
        1. Type-based matching: If pattern descriptor's type matches the list item's type,
           use it (regex becomes optional filter)
        2. Text-based matching: Fallback to standard text pattern matching

        This makes regex optional for list items - if a pattern descriptor has:
        - type: "L-BULLET" and style overrides
        - regex: "-+$" (optional)

        Then ALL L-BULLET items will get the style, and regex acts as an additional
        filter if present (not a requirement).
        """
        import logging
        from glyph.core.analysis.forms.headings import guess_heading_form, HeadingForm
        from glyph.core.analysis.detectors.heuristics.heading_detector import score_heading
        from glyph.core.analysis.features import extract_line_features

        logger = logging.getLogger(__name__)
        text_normalized = ' '.join(text.strip().split())

        # PRIORITY 0: Disambiguation - Check if this is actually a heading
        # Common conflict: "1. Introduction" detected as L-ORDERED-DOTTED but should be H-SECTION-N
        if item_type and item_type.startswith("L-ORDERED"):
            try:
                # Check heading classification
                # NOTE: Text may have marker already stripped (e.g., "Introduction" instead of "1. Introduction")
                # so heading_form might be H-SHORT instead of H-SECTION-N. That's OK - we check item_type.
                feats = extract_line_features(text_normalized)
                heading_score = score_heading(text_normalized, feats)
                heading_form = guess_heading_form(text_normalized)

                # Apply disambiguation logic
                # Accept BOTH H-SECTION-N (if marker still present) OR any heading form (if marker stripped)
                # The key indicator is: item_type is L-ORDERED but text looks like a heading
                if heading_score >= 0.55 and heading_form:
                    words = text_normalized.split()
                    word_count = len(words)

                    # Check if first word is title-cased
                    first_word = words[0] if words else ""
                    is_title_case = first_word and first_word[0].isupper()

                    # If title-cased + reasonable length, reclassify as heading
                    # Since marker was stripped by list parser, this is truly a SECTION heading
                    # Increased from 6 to 12 words to support longer academic section headings
                    if word_count <= 12 and is_title_case:
                        logger.debug(f"Reclassifying '{text_normalized}' from {item_type} to H-SECTION-N (heading, words={word_count})")
                        item_type = "H-SECTION-N"  # Override the detected list type
                    elif heading_score > 0.9:  # Very high heading confidence
                        logger.debug(f"Reclassifying '{text_normalized}' from {item_type} to H-SECTION-N (high heading score)")
                        item_type = "H-SECTION-N"
            except Exception as e:
                logger.debug(f"Disambiguation check failed: {e}")

        # PRIORITY 1: Type-based matching with unified priority system
        if item_type:
            type_matches = []

            for i, desc in enumerate(self.pattern_descriptors):
                desc_type = desc.get("type", "")

                # Handle heading types (H-*) after disambiguation
                if desc_type and isinstance(desc_type, str) and desc_type.startswith("H-") and item_type.startswith("H-"):
                    if desc_type == item_type:
                        # Calculate priority using unified system
                        base_priority = desc.get("priority")
                        if base_priority is None:
                            base_priority = get_default_priority(desc_type)

                        context_bonus = calculate_context_bonus(text_normalized, desc_type)
                        final_priority = base_priority + context_bonus

                        type_matches.append({
                            "priority": final_priority,
                            "descriptor": desc,
                            "type": desc_type,
                            "base_priority": base_priority,
                            "context_bonus": context_bonus
                        })
                        logger.debug(
                            f"Heading match: {desc_type} | "
                            f"priority={final_priority} (base={base_priority}, context={context_bonus})"
                        )

                # Check if types match (both start with "L-")
                # Skip array types (like REGEX/EXACT arrays) - they don't apply to list matching
                if desc_type and isinstance(desc_type, str) and desc_type.startswith("L-") and item_type.startswith("L-"):
                    # Extract the list category (BULLET, DECIMAL, etc.)
                    # Handle both specific types (L-BULLET-SOLID) and generic (L-BULLET)
                    desc_parts = desc_type.split("-")
                    item_parts = item_type.split("-")

                    if len(desc_parts) >= 2 and len(item_parts) >= 2:
                        # Check exact match first
                        is_exact_match = (desc_type == item_type)

                        # Check if item type starts with descriptor type (fallback match)
                        # "L-BULLET-SOLID" starts with "L-BULLET" → True
                        is_fallback_match = (
                            item_type.startswith(desc_type) and
                            len(desc_parts) <= len(item_parts)  # Descriptor must be less specific
                        )

                        is_type_match = is_exact_match or is_fallback_match

                        if is_type_match:
                            # Optional: apply regex filter if present
                            regex_pattern = desc.get("regex")
                            if regex_pattern:
                                compiled_regex = self._compiled_regexes.get((i, "regex"))
                                if compiled_regex and not compiled_regex.match(text_normalized):
                                    logger.debug(f"Type matched ({desc_type} == {item_type}) but regex filter failed: {regex_pattern}")
                                    continue  # Regex filter failed, try next descriptor

                            # Calculate priority using unified system
                            base_priority = desc.get("priority")
                            if base_priority is None:
                                base_priority = get_default_priority(desc_type)
                                # Add specificity bonus for exact matches
                                if is_exact_match:
                                    base_priority += 100  # Exact type match bonus

                            context_bonus = calculate_context_bonus(text_normalized, desc_type)
                            final_priority = base_priority + context_bonus

                            type_matches.append({
                                "priority": final_priority,
                                "descriptor": desc,
                                "type": desc_type,
                                "base_priority": base_priority,
                                "context_bonus": context_bonus,
                                "is_exact": is_exact_match
                            })
                            logger.debug(
                                f"List match: {desc_type} matches {item_type} | "
                                f"priority={final_priority} (base={base_priority}, context={context_bonus}, exact={is_exact_match})"
                            )

            # Return highest-priority type match
            if type_matches:
                best_match = max(type_matches, key=lambda m: m["priority"])
                logger.info(
                    f"Best type match for '{text_normalized[:50]}': "
                    f"type={best_match['type']} | priority={best_match['priority']}"
                )
                return best_match["descriptor"]

        # PRIORITY 2: Fallback to text-based pattern matching
        logger.debug(f"No type match for item_type={item_type}, falling back to text matching")
        return self._match_plaintext_to_pattern(text)

    # -------- Plaintext path --------
    def _run_plaintext_path(
        self, lines: List[str],
    ) -> List[Tuple[str, Dict[str, Any], Optional[Dict[str, Any]]]]:
        import logging
        logger = logging.getLogger(__name__)

        results: List[Tuple[str, Dict[str, Any], Optional[Dict[str, Any]]]] = []

        # Check if schema has any table pattern descriptors
        def has_table_type(desc_type):
            """Check if descriptor type indicates a table pattern."""
            table_prefixes = ("T-BASIC", "T-COMPLEX", "T-DATA")
            if isinstance(desc_type, str):
                return desc_type.startswith(table_prefixes)
            elif isinstance(desc_type, list):
                return any(isinstance(t, str) and t.startswith(table_prefixes) for t in desc_type)
            return False

        has_table_patterns = any(
            has_table_type(desc.get("type"))
            for desc in self.pattern_descriptors
        )

        # If no table patterns in schema, disable table detection in plaintext
        # This prevents pipes from being auto-detected as tables
        if not has_table_patterns:
            # Create new settings with "table" removed from enabled handlers
            enabled_handlers = list(self.settings.RANGE_HANDLERS_ENABLED or [])
            if "table" in enabled_handlers:
                enabled_handlers.remove("table")
            plaintext_settings = self.settings.with_overrides(RANGE_HANDLERS_ENABLED=enabled_handlers)
            emittables = build_emittables_from_plaintext(lines, settings=plaintext_settings)
        else:
            # Table patterns exist, allow table detection
            emittables = build_emittables_from_plaintext(lines, settings=self.settings)

        docx_styles = {s.name: s for s in self.document.styles}

        for e in emittables:
            if e["kind"] == "block":
                blk = e["block"]
                label = f"[BLOCK:{blk.get('kind','unknown')}]"
                # compute plaintext slice for the block
                start = int(blk.get("start_idx", 0))
                end = int(blk.get("end_idx", start))
                block_plaintext = "\n".join(lines[start:end+1])

                if hasattr(self.router, "dispatch_block"):
                    # PHASE 4: Post-processing extraction for list blocks
                    # Extract items that should be non-list types (headings, paragraphs, etc.)
                    if blk.get("kind") == "list":
                        items_to_extract = []  # Items that should be extracted
                        items_to_keep = []     # Items that stay in list

                        for it in blk["payload"].get("items", []):
                            text = it.get("text", "")
                            item_type = it.get("type")
                            marker = it.get("marker", "")

                            # HIERARCHICAL SECTION NUMBER CHECK
                            # If marker is hierarchical (e.g., "3.1 ", "1.2.3 "), force classification as H-SECTION-N
                            import re
                            hierarchical_pattern = re.compile(r'^\d+\.\d+')  # Matches 1.1, 2.3, 1.2.3, etc.
                            has_hierarchical_marker = bool(hierarchical_pattern.match(marker.strip()))

                            # If hierarchical marker + title case text, override to H-SECTION-N
                            if has_hierarchical_marker and item_type and item_type.startswith("L-ORDERED"):
                                words = text.split()
                                word_count = len(words)
                                first_word = words[0] if words else ""
                                is_title_case = first_word and first_word[0].isupper()

                                # Lenient rules for hierarchical sections (up to 12 words, title case)
                                if word_count <= 12 and is_title_case:
                                    logger.debug(f"Hierarchical marker '{marker.strip()}' detected, overriding to H-SECTION-N")
                                    item_type = "H-SECTION-N"

                            # Try type-aware pattern matching
                            matched_desc = self._match_list_item_to_pattern(text, item_type)
                            matched_type = None

                            if matched_desc:
                                matched_type = matched_desc.get("type")
                                # Merge matched descriptor's style into the item
                                matched_style = matched_desc.get("style", {})
                                if matched_style:
                                    # Enrich item with font and other style properties
                                    it["font"] = {**it.get("font", {}), **matched_style.get("font", {})}
                                    it["paragraph"] = {**it.get("paragraph", {}), **matched_style.get("paragraph", {})}
                                    # Store the matched descriptor type and descriptor
                                    it["matched_type"] = matched_type
                                    it["matched_descriptor"] = matched_desc
                                    # Store style at block level if needed
                                    if "style" not in blk:
                                        blk["style"] = {}
                                    # Merge style_id if present
                                    if "style_id" in matched_style:
                                        blk["style"]["style_id"] = matched_style["style_id"]

                            # EXTRACTION DECISION: Check if item should be extracted from list
                            # Extract headings (H-*) and paragraphs (P-*) that were misclassified as lists
                            should_extract = False
                            if matched_type:
                                # Extract headings
                                if matched_type.startswith("H-"):
                                    should_extract = True
                                    logger.info(f"Extracting '{text[:50]}' from list: matched as {matched_type}")
                                # Could also extract specific paragraph types if needed
                                # elif matched_type in ["P-LEAD", "P-SUMMARY"]:
                                #     should_extract = True

                            if should_extract:
                                items_to_extract.append(it)
                            else:
                                items_to_keep.append(it)

                        # Dispatch extracted items as separate paragraphs/headings
                        for extracted_item in items_to_extract:
                            text = extracted_item.get("text", "")
                            matched_desc = extracted_item.get("matched_descriptor", {})
                            matched_type = extracted_item.get("matched_type", "P-BODY")

                            # For H-SECTION-N headings, restore the section number marker
                            if matched_type == "H-SECTION-N":
                                marker = extracted_item.get("marker", "")
                                if marker and marker.strip():
                                    # Prepend marker to text (marker already includes trailing space)
                                    text = f"{marker}{text}"

                            # Create a paragraph-style descriptor
                            para_desc = {
                                "type": matched_type,
                                "features": {"text": text},
                                "style": matched_desc.get("style", {})
                            }

                            # Dispatch as paragraph (will route to appropriate writer based on type)
                            style_obj = resolve_style(
                                descriptor=para_desc,
                                schema=self.schema,
                                global_defaults=self.global_defaults,
                                docx_styles=self.document.styles
                            )
                            self.router.dispatch(para_desc, style=style_obj, plaintext=text)
                            results.append((f"[EXTRACTED:{para_desc['type']}]", para_desc, style_obj))

                        # If all items were extracted, skip the list block entirely
                        if not items_to_keep:
                            logger.info(f"List block fully extracted - all items reclassified")
                            continue

                        # Update block with remaining items
                        blk["payload"]["items"] = items_to_keep

                    # Dispatch the (possibly modified) block
                    self.router.dispatch_block(blk, style=None, plaintext=block_plaintext)
                    results.append((label, {"block": blk}, None))
                    continue

                # fallback (should rarely hit once writers implement write_block)
                if blk.get("kind") == "list":
                    for it in blk["payload"].get("items", []):
                        text = it.get("text", "")
                        item_type = it.get("type")  # Get the detected type (e.g., "L-BULLET", "L-DECIMAL")

                        # Try type-aware pattern matching first
                        matched_desc = self._match_list_item_to_pattern(text, item_type)
                        if matched_desc:
                            desc = matched_desc
                        else:
                            desc = {"type": "L-BULLET-SOLID",
                                    "features": {"text": text},
                                    "style": {"style_id": "ListParagraph"}}

                        style_obj = resolve_style(
                            descriptor=desc,
                            schema=self.schema,
                            global_defaults=self.global_defaults,
                            docx_styles=docx_styles,
                        )
                        self.router.dispatch(desc, style_obj, plaintext=text)
                        results.append((text, desc, style_obj))
                    continue

                if blk.get("kind") == "table":
                    for row in blk["payload"].get("rows", []):
                        text = " | ".join(row)

                        # Try pattern matching first
                        matched_desc = self._match_plaintext_to_pattern(text)
                        if matched_desc:
                            desc = matched_desc
                        else:
                            desc = {"type": "P-NORMAL",
                                    "features": {"text": text},
                                    "style": {"style_id": "Normal"}}

                        style_obj = resolve_style(
                            descriptor=desc,
                            schema=self.schema,
                            global_defaults=self.global_defaults,
                            docx_styles=docx_styles,
                        )
                        self.router.dispatch(desc, style_obj, plaintext=text)
                        results.append((text, desc, style_obj))
                    continue

                # unknown block → degrade to a paragraph note
                text = label

                # Try pattern matching even for unknown blocks
                matched_desc = self._match_plaintext_to_pattern(text)
                if matched_desc:
                    desc = matched_desc
                else:
                    desc = {"type": "P-NORMAL",
                            "features": {"text": text},
                            "style": {"style_id": "Normal"}}

                style_obj = resolve_style(
                    descriptor=desc,
                    schema=self.schema,
                    global_defaults=self.global_defaults,
                    docx_styles=docx_styles,
                )
                self.router.dispatch(desc, style_obj, plaintext=text)
                results.append((text, desc, style_obj))
                continue

            # kind == "single"
            text = e.get("text", "")
            if text.strip() == "":
                continue

            # CRITICAL: Match plaintext against pattern_descriptors
            matched_desc = self._match_plaintext_to_pattern(text)
            if matched_desc:
                # Use the matched pattern descriptor (includes its style!)
                desc = matched_desc
            else:
                # Fallback to generic descriptor
                desc = {"type": "P-NORMAL",
                        "features": {"text": text},
                        "style": {"style_id": "Normal"}}

            style_obj = resolve_style(
                descriptor=desc,
                schema=self.schema,
                global_defaults=self.global_defaults,
                docx_styles=docx_styles,
            )
            # ALWAYS pass plaintext (single line)
            self.router.dispatch(desc, style_obj, plaintext=text)
            results.append((text, desc, style_obj))

        return results

    # -------- Plaintext extraction helpers --------
    def _extract_plaintext_lines(self, schema: Dict[str, Any]) -> Optional[List[str]]:
        if isinstance(schema.get("plaintext_lines"), list):
            return [str(x) for x in schema["plaintext_lines"]]
        if isinstance(schema.get("plaintext_text"), str):
            res = intake_plaintext(schema["plaintext_text"])
            return res.lines
        pt = schema.get("plaintext")
        if isinstance(pt, dict):
            if isinstance(pt.get("lines"), list):
                return [str(x) for x in pt["lines"]]
            if isinstance(pt.get("text"), str):
                res = intake_plaintext(pt["text"]); return res.lines
            if pt.get("path"):
                p = Path(pt["path"]); res = intake_plaintext(p); return res.lines
        return None
