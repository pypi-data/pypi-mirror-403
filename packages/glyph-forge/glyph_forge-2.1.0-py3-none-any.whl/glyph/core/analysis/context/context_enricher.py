# src/glyph/core/analysis/context/context_enricher.py

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ContextWindow:
    """Rich contextual metadata for a single element."""

    index: int

    # Neighbor references
    prev_descriptors: List[Dict[str, Any]] = field(default_factory=list)
    next_descriptors: List[Dict[str, Any]] = field(default_factory=list)

    # Hierarchical signals
    parent_candidate: Optional[Dict[str, Any]] = None
    depth_hint: int = 0

    # Style continuity (DOCX-specific)
    style_break: bool = False
    alignment_shift: bool = False

    # Semantic signals
    follows_title: bool = False
    precedes_content: bool = False

    # Additional enrichment data (extensible)
    custom_data: Dict[str, Any] = field(default_factory=dict)


class ContextEnricher:
    """
    Modular context enricher - extensible for new properties.

    Builds rich context windows around elements by applying pluggable
    enricher functions that add domain-specific signals.
    """

    def __init__(self, window_size: int = 2, skip_blank_lines: bool = True):
        """
        Initialize context enricher.

        Args:
            window_size: Number of elements to include before/after current element
            skip_blank_lines: If True, skip over blank lines when finding neighbors
        """
        self.window_size = window_size
        self.skip_blank_lines = skip_blank_lines
        self.enrichers: List[Callable[[ContextWindow, Dict[str, Any], List[Dict[str, Any]]], None]] = []

    def register_enricher(self, enricher: Callable[[ContextWindow, Dict[str, Any], List[Dict[str, Any]]], None]):
        """
        Add custom context enricher.

        Args:
            enricher: Function that takes (context_window, current_descriptor, all_descriptors)
                     and modifies the context_window in place
        """
        self.enrichers.append(enricher)

    def build_window(
        self,
        index: int,
        descriptors: List[Dict[str, Any]],
        current_descriptor: Optional[Dict[str, Any]] = None
    ) -> ContextWindow:
        """
        Build context window with all registered enrichments.

        Args:
            index: Current element index
            descriptors: Full list of descriptors
            current_descriptor: Optional current descriptor (defaults to descriptors[index])

        Returns:
            Enriched ContextWindow
        """
        if current_descriptor is None:
            current_descriptor = descriptors[index] if 0 <= index < len(descriptors) else {}

        # Build base context window
        context = ContextWindow(
            index=index,
            prev_descriptors=self._get_neighbors(index, descriptors, direction="prev"),
            next_descriptors=self._get_neighbors(index, descriptors, direction="next"),
        )

        # Apply basic signals
        self._add_basic_signals(context, current_descriptor, descriptors)

        # Apply all registered enrichers
        for enricher in self.enrichers:
            enricher(context, current_descriptor, descriptors)

        return context

    def _get_neighbors(
        self,
        index: int,
        descriptors: List[Dict[str, Any]],
        direction: str
    ) -> List[Dict[str, Any]]:
        """
        Get neighboring descriptors in specified direction.

        Args:
            index: Current element index
            descriptors: Full list of descriptors
            direction: "prev" or "next"

        Returns:
            List of neighboring descriptors (up to window_size)
        """
        neighbors = []
        step = -1 if direction == "prev" else 1
        current = index + step

        while len(neighbors) < self.window_size and 0 <= current < len(descriptors):
            descriptor = descriptors[current]

            # Skip blank lines if configured
            if self.skip_blank_lines:
                # Support both direct text field and features.text field
                text = descriptor.get("text", "")
                if not text and "features" in descriptor:
                    text = descriptor["features"].get("text", "")

                if not text.strip():
                    current += step
                    continue

            neighbors.append(descriptor)
            current += step

        # Return in original order (oldest to newest for prev)
        if direction == "prev":
            neighbors.reverse()

        return neighbors

    def _add_basic_signals(
        self,
        context: ContextWindow,
        current_descriptor: Dict[str, Any],
        all_descriptors: List[Dict[str, Any]]
    ):
        """
        Add basic semantic signals to context window.

        Args:
            context: ContextWindow to enrich
            current_descriptor: Current element descriptor
            all_descriptors: Full list of descriptors
        """
        # Check if follows title-like heading
        if context.prev_descriptors:
            prev = context.prev_descriptors[-1]  # Most recent previous
            prev_type = prev.get("type", "")
            context.follows_title = prev_type in [
                "H-SHORT",
                "H-SECTION-N",
                "H-LONG",
                "H-CONTENTS"
            ]

        # Check if precedes body content
        if context.next_descriptors:
            next_elem = context.next_descriptors[0]  # Most immediate next
            next_type = next_elem.get("type", "")
            context.precedes_content = next_type in [
                "PARAGRAPH",
                "LIST",
                "BODY",
                "TEXT"
            ]

        # Find parent candidate (nearest heading above)
        context.parent_candidate = self._find_parent_candidate(context.index, all_descriptors)

        # Estimate depth hint
        context.depth_hint = self._estimate_depth(context.index, all_descriptors)

    def _find_parent_candidate(
        self,
        index: int,
        descriptors: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find nearest heading-like element above current index.

        Args:
            index: Current element index
            descriptors: Full list of descriptors

        Returns:
            Parent heading descriptor or None
        """
        for i in range(index - 1, -1, -1):
            descriptor = descriptors[i]
            desc_type = descriptor.get("type", "")

            # Skip blank lines
            if self.skip_blank_lines:
                # Support both direct text field and features.text field
                text = descriptor.get("text", "")
                if not text and "features" in descriptor:
                    text = descriptor["features"].get("text", "")

                if not text.strip():
                    continue

            # Check if heading-like (all valid heading types start with "H-")
            if desc_type.startswith("H-"):
                return descriptor

        return None

    def _estimate_depth(
        self,
        index: int,
        descriptors: List[Dict[str, Any]]
    ) -> int:
        """
        Estimate hierarchical depth based on heading sequence.

        Args:
            index: Current element index
            descriptors: Full list of descriptors

        Returns:
            Estimated depth (0 = no hierarchy, 1+ = nested)
        """
        depth = 0

        for i in range(index - 1, -1, -1):
            descriptor = descriptors[i]
            desc_type = descriptor.get("type", "")

            # Skip blank lines
            if self.skip_blank_lines:
                # Support both direct text field and features.text field
                text = descriptor.get("text", "")
                if not text and "features" in descriptor:
                    text = descriptor["features"].get("text", "")

                if not text.strip():
                    continue

            # Count heading-like elements (all valid heading types start with "H-")
            if desc_type.startswith("H-"):
                depth += 1

            # Stop at first non-heading content block
            if desc_type in ["PARAGRAPH", "LIST", "BODY", "TEXT"]:
                break

        return depth

    def enrich_all(
        self,
        descriptors: List[Dict[str, Any]]
    ) -> List[ContextWindow]:
        """
        Build context windows for all descriptors.

        Args:
            descriptors: Full list of descriptors

        Returns:
            List of ContextWindow objects, one per descriptor
        """
        return [
            self.build_window(i, descriptors, descriptor)
            for i, descriptor in enumerate(descriptors)
        ]
