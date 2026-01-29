"""
Glyph Markup Layout Resolver
=============================

Resolves utility classes to normalized layout properties.

Takes a list of utility class names and merges them into a single
layout bundle with properties for run, paragraph, and section scopes.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from ..language.registry import get_utility, UtilityDef
from ..language.errors import UnknownUtilityError


@dataclass
class LayoutBundle:
    """
    Bundle of resolved layout properties across all scopes.

    Attributes:
        run_props: Run-level properties (font, color, etc.)
        paragraph_props: Paragraph-level properties (alignment, spacing, etc.)
        section_props: Section-level properties (margins, columns, etc.)
        row_props: Row-level properties (cols, widths, alignment, etc.)
        cell_props: Cell-level properties (align, valign, padding, etc.)
        image_props: Image-level properties
        break_props: Break-level properties
        unknown_utilities: List of utility names that couldn't be resolved
    """

    run_props: Dict[str, Any] = field(default_factory=dict)
    paragraph_props: Dict[str, Any] = field(default_factory=dict)
    section_props: Dict[str, Any] = field(default_factory=dict)
    row_props: Dict[str, Any] = field(default_factory=dict)
    cell_props: Dict[str, Any] = field(default_factory=dict)
    image_props: Dict[str, Any] = field(default_factory=dict)
    break_props: Dict[str, Any] = field(default_factory=dict)
    unknown_utilities: List[str] = field(default_factory=list)

    def merge(self, other: "LayoutBundle") -> "LayoutBundle":
        """
        Merge another layout bundle into this one.

        Later properties override earlier ones (last wins).

        Args:
            other: Another LayoutBundle to merge

        Returns:
            New merged LayoutBundle
        """
        return LayoutBundle(
            run_props={**self.run_props, **other.run_props},
            paragraph_props={**self.paragraph_props, **other.paragraph_props},
            section_props={**self.section_props, **other.section_props},
            row_props={**self.row_props, **other.row_props},
            cell_props={**self.cell_props, **other.cell_props},
            image_props={**self.image_props, **other.image_props},
            break_props={**self.break_props, **other.break_props},
            unknown_utilities=self.unknown_utilities + other.unknown_utilities,
        )


def resolve_utility(util_name: str, util_def: Optional[UtilityDef]) -> Dict[str, Any]:
    """
    Resolve a single utility to its properties.

    Handles parametric utilities by extracting values and calling prop builders.

    Args:
        util_name: The utility name (e.g., "font-size-12")
        util_def: The utility definition (may have pattern matching)

    Returns:
        Dictionary of resolved properties
    """
    if not util_def:
        return {}

    props = dict(util_def.props)

    # Handle parametric utilities with prop builders
    if "_builder" in props:
        # This is a parametric utility
        builder = props.pop("_builder")
        match = util_def.matches(util_name)
        if match is not None:
            # Call builder with matched parameters
            built_props = builder(match) if match else builder({})
            return built_props

    return props


def resolve_classes(classes: List[str], strict: bool = False) -> LayoutBundle:
    """
    Resolve a list of utility classes into a layout bundle.

    Args:
        classes: List of utility class names
        strict: If True, raise UnknownUtilityError for unknown utilities

    Returns:
        LayoutBundle with resolved properties

    Raises:
        UnknownUtilityError: If strict=True and unknown utility encountered

    Examples:
        >>> bundle = resolve_classes(["bold", "font-size-12", "align-center"])
        >>> bundle.run_props
        {'bold': True, 'size': 12}
        >>> bundle.paragraph_props
        {'alignment': 'center'}
    """
    bundle = LayoutBundle()

    for class_name in classes:
        # Look up utility definition
        util_def = get_utility(class_name)

        if not util_def:
            if strict:
                raise UnknownUtilityError(class_name)
            bundle.unknown_utilities.append(class_name)
            continue

        # Resolve utility properties
        props = resolve_utility(class_name, util_def)

        # Add to appropriate scope
        if util_def.scope == "run":
            bundle.run_props.update(props)
        elif util_def.scope == "paragraph":
            bundle.paragraph_props.update(props)
        elif util_def.scope == "section":
            bundle.section_props.update(props)
        elif util_def.scope == "row":
            bundle.row_props.update(props)
        elif util_def.scope == "cell":
            bundle.cell_props.update(props)
        elif util_def.scope == "image":
            bundle.image_props.update(props)
        elif util_def.scope == "break":
            bundle.break_props.update(props)

    return bundle


def merge_layout_bundles(bundles: List[LayoutBundle]) -> LayoutBundle:
    """
    Merge multiple layout bundles.

    Later bundles override earlier ones.

    Args:
        bundles: List of LayoutBundle objects

    Returns:
        Merged LayoutBundle
    """
    if not bundles:
        return LayoutBundle()

    result = bundles[0]
    for bundle in bundles[1:]:
        result = result.merge(bundle)

    return result
