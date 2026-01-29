from __future__ import annotations

from typing import Any

# Heuristic mapping of detected patterns → proposed Magic ETL tiles
# Extend as analyzer detects more operations (merge, groupby, distinct, etc.)

BASIC_MAPPINGS: dict[str, dict[str, Any]] = {
    # Detected function patterns from DomoDataflowAnalyzer
    "split_email_local_part": {
        "action_type": "SplitColumnAction",
        "category": "text",
        "rationale": "Split email by '@' to get local part, then '.' to separate name segments.",
        "confidence": 0.78,
    },
    "split_dot_segments": {
        "action_type": "SplitColumnAction",
        "category": "text",
        "rationale": "Split text by '.' into multiple columns.",
        "confidence": 0.75,
    },
    "capitalize_parts": {
        "action_type": "TextFormatting",
        "category": "text",
        "rationale": "Capitalize name segments after split; use title-case formatting.",
        "confidence": 0.62,
    },
}


def map_patterns_to_actions(patterns: list[str]) -> list[dict[str, Any]]:
    """Map analyzer function patterns to suggested actions.

    Args:
        patterns: List of string pattern IDs reported by analyzer

    Returns:
        A list of SuggestedAction-like dicts
    """
    suggestions: list[dict[str, Any]] = []
    for p in patterns:
        info = BASIC_MAPPINGS.get(p)
        if info:
            suggestions.append({**info})
    return suggestions
