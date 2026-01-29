from __future__ import annotations

from typing import Any

from .mappings import map_patterns_to_actions


def run_pattern_matching(state: dict[str, Any]) -> dict[str, Any]:
    """Node: Map detected function patterns to ETL tile suggestions.

    Expects state from code analysis:
        operations: list[dict] with 'detail.patterns' keys
        suggestions: list[dict] (initial suggestions from analyzer)

    Returns updates:
        suggestions: extended list
    """
    operations: list[dict[str, Any]] = state.get("operations", [])
    suggestions: list[dict[str, Any]] = list(state.get("suggestions", []))

    for op in operations:
        patterns = op.get("detail", {}).get("patterns", [])
        if patterns:
            suggestions.extend(map_patterns_to_actions(patterns))

    return {"suggestions": suggestions}
