from __future__ import annotations

from typing import Any, TypedDict


class PythonAnalysisState(TypedDict, total=False):
    """Shared state used by the script analyzer graph.

    Keys:
        python_script: Raw Python script string
        operations: List of OperationDetection dicts
        suggestions: List of SuggestedAction dicts
        recommendations: Final recommendation dicts
        notes: List of strings
    """

    python_script: str
    operations: list[dict[str, Any]]
    suggestions: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    notes: list[str]
