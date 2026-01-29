"""
Schema compression utilities.

Compresses schemas by deduplicating redundant selectors (pattern descriptors)
while preserving the most practical/highest-scoring instances.

Note: Supports both "selectors" (new) and "pattern_descriptors" (deprecated) keys.
"""
from typing import Dict, Any, List
from collections import defaultdict


def compress_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compress a schema by deduplicating redundant selectors.

    For selectors with the same type (e.g., multiple "H-SHORT" entries):
    1. Select the one with the highest score
    2. If scores are equal, prefer the one with style properties

    Args:
        schema: A Glyph schema dictionary with "selectors" or "pattern_descriptors" key

    Returns:
        Compressed schema with deduplicated selectors (outputs both keys for compatibility)

    Example:
        >>> schema = {
        ...     "pattern_descriptors": [
        ...         {"type": "H-SHORT", "score": 0.8, "style": {}, "paragraph_id": "p1"},
        ...         {"type": "H-SHORT", "score": 0.9, "style": {"pStyle": "Heading1"}, "paragraph_id": "p2"},
        ...         {"type": "P-BODY", "score": 0.7, "style": {}, "paragraph_id": "p3"}
        ...     ]
        ... }
        >>> compressed = compress_schema(schema)
        >>> len(compressed["pattern_descriptors"])
        2
    """
    # Create a deep copy to avoid modifying the input
    compressed = dict(schema)

    # Support both "selectors" (new) and "pattern_descriptors" (deprecated) keys
    # Use 'or' to handle None values gracefully
    pattern_descriptors = (
        schema.get("selectors") or schema.get("pattern_descriptors") or []
    )
    if not pattern_descriptors:
        return compressed

    # Group descriptors by type
    type_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for descriptor in pattern_descriptors:
        descriptor_type = descriptor.get("type", "UNKNOWN")
        type_groups[descriptor_type].append(descriptor)

    # For each group, select the best representative
    deduplicated = []
    for descriptor_type, descriptors in type_groups.items():
        if len(descriptors) == 1:
            # No duplicates, keep as-is
            deduplicated.append(descriptors[0])
        else:
            # Multiple descriptors of same type - select best one
            best = _select_best_descriptor(descriptors)
            deduplicated.append(best)

    # Output both keys for backward compatibility during transition
    compressed["selectors"] = deduplicated  # New primary key
    compressed["pattern_descriptors"] = deduplicated  # Deprecated, for backward compatibility
    return compressed


def _select_best_descriptor(descriptors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Select the best descriptor from a list of same-type descriptors.

    Priority:
    1. Highest score
    2. If scores are equal, prefer one with style properties
    3. If still tied, prefer first one

    Args:
        descriptors: List of pattern descriptors with the same type

    Returns:
        The best descriptor to keep
    """
    if not descriptors:
        return {}

    if len(descriptors) == 1:
        return descriptors[0]

    # Sort by score (descending), then by presence of style properties
    def score_descriptor(desc: Dict[str, Any]) -> tuple:
        score = desc.get("score", 0.0)
        style = desc.get("style", {})

        # Count non-empty style properties
        style_count = 0
        if isinstance(style, dict):
            style_count = sum(1 for k, v in style.items() if v)

        # Return tuple for sorting: (score, style_count)
        # Both in descending order (higher is better)
        return (-score, -style_count)

    # Sort and return the best (first after sorting)
    sorted_descriptors = sorted(descriptors, key=score_descriptor)
    return sorted_descriptors[0]


def get_compression_stats(original_schema: Dict[str, Any], compressed_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get statistics about the compression.

    Args:
        original_schema: Original uncompressed schema
        compressed_schema: Compressed schema

    Returns:
        Dictionary with compression statistics

    Example:
        >>> stats = get_compression_stats(original, compressed)
        >>> print(stats["reduction_count"])
        5
    """
    # Support both "selectors" and "pattern_descriptors" keys (handle None values)
    original_descriptors = (
        original_schema.get("selectors") or original_schema.get("pattern_descriptors") or []
    )
    compressed_descriptors = (
        compressed_schema.get("selectors") or compressed_schema.get("pattern_descriptors") or []
    )

    original_count = len(original_descriptors)
    compressed_count = len(compressed_descriptors)

    # Count duplicates by type in original
    type_counts = defaultdict(int)
    for desc in original_descriptors:
        descriptor_type = desc.get("type", "UNKNOWN")
        type_counts[descriptor_type] += 1

    duplicated_types = {t: count for t, count in type_counts.items() if count > 1}

    return {
        "original_count": original_count,
        "compressed_count": compressed_count,
        "reduction_count": original_count - compressed_count,
        "reduction_percentage": round((original_count - compressed_count) / original_count * 100, 2) if original_count > 0 else 0,
        "duplicated_types": duplicated_types,
    }
