# src/glyph/core/analysis/context/context_tracker.py

from collections import deque

class ContextTracker:
    def __init__(self, window_size: int = 2):
        """
        Context window tracker.

        Args:
            window_size (int): number of indices to look behind and ahead.
                              Default = 2
        """
        self.window_size = window_size

    def update(self, i: int, descriptors: list[dict]) -> dict:
        """
        Compute context metadata for descriptor at index i.

        Args:
            i (int): current index
            descriptors (list[dict]): full sequence of descriptors

        Returns:
            dict: context metadata
        """
        start = max(0, i - self.window_size)
        end = i + self.window_size + 1

        prev = descriptors[start:i]
        nxt = descriptors[i + 1:end]

        return {
            "prev_types": [d.get("type") for d in prev],
            "next_types": [d.get("type") for d in nxt],
            "dominant_style": self._dominant_style(prev + nxt),
            "signal_strength": self._signal_strength(prev + nxt),
        }

    def _dominant_style(self, neighbors: list[dict]) -> str | None:
        styles = [d.get("style", {}).get("style_id") for d in neighbors if "style" in d]
        if not styles:
            return None
        # deterministic tie-breaker: pick the first most frequent
        counts = {s: styles.count(s) for s in set(styles)}
        return max(counts, key=counts.get)

    def _signal_strength(self, neighbors: list[dict]) -> str:
        # placeholder: regex > heuristic > fallback
        methods = [d.get("method") for d in neighbors if "method" in d]
        if "regex" in methods:
            return "regex>heuristic"
        if "heuristic" in methods:
            return "heuristic"
        return "fallback"

    def annotate(self, descriptors: list[dict]) -> list[dict]:
        """
        Annotate all descriptors with context.
        """
        results = []
        for i, d in enumerate(descriptors):
            d = d.copy()
            d["context"] = self.update(i, descriptors)
            results.append(d)
        return results
