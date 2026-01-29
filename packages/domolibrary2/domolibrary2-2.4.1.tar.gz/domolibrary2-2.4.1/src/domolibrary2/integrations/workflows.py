from __future__ import annotations

from typing import Any

from .DomoDataflowAnalyzer import DomoDataflowAnalyzer


def analyze_python_script(script: str) -> dict[str, Any]:
    """Convenience API: Analyze Python script and return recommendations.

    Tries to use the LangGraph workflow when available; falls back to the
    heuristic analyzer if LangGraph is not installed.
    """
    try:
        from .graphs.script_analyzer_graph import run_workflow

        return run_workflow(script)
    except Exception:
        analyzer = DomoDataflowAnalyzer()
        result = analyzer.analyze(script)
        # Basic fallback structure for consistency
        return {
            "operations": [vars(op) for op in result.operations],
            "suggestions": [vars(s) for s in result.suggestions],
            "notes": result.notes,
            "recommendations": [
                {
                    "action_type": s.action_type,
                    "category": s.category,
                    "rationale": s.rationale,
                    "confidence": s.confidence,
                    "columns": s.columns,
                }
                for s in result.suggestions
            ],
        }
