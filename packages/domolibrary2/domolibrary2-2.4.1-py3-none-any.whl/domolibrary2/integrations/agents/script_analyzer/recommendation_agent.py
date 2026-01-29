from __future__ import annotations

from typing import Any


def run_recommendations(state: dict[str, Any]) -> dict[str, Any]:
    """Node: Aggregate suggestions into final recommendations.

    Produces a compact output list with action_type, category, rationale, and confidence.
    """
    suggestions: list[dict[str, Any]] = state.get("suggestions", [])

    # Deduplicate by (action_type, category, rationale)
    seen = set()
    compact: list[dict[str, Any]] = []

    for s in suggestions:
        key = (s.get("action_type"), s.get("category"), s.get("rationale"))
        if key in seen:
            continue
        seen.add(key)
        compact.append(
            {
                "action_type": s.get("action_type"),
                "category": s.get("category"),
                "rationale": s.get("rationale"),
                "confidence": float(s.get("confidence", 0.5)),
                "columns": list(s.get("columns", [])),
            }
        )

    return {"recommendations": compact}
