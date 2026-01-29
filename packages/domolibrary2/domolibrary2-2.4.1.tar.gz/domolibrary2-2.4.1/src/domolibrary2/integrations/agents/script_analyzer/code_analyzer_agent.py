from __future__ import annotations

from typing import Any

from ...DomoDataflowAnalyzer import DomoDataflowAnalyzer


def run_code_analysis(state: dict[str, Any]) -> dict[str, Any]:
    """Node: Analyze Python script via AST to detect operations.

    Expects:
        state["python_script"]: str

    Returns state updates:
        operations: list[dict]
        suggestions: list[dict]
        notes: list[str]
    """
    script = state.get("python_script")
    analyzer = DomoDataflowAnalyzer()
    result = analyzer.analyze(script)

    # Convert dataclasses to plain dicts for graph state
    ops = [vars(op) for op in result.operations]
    sug = [vars(s) for s in result.suggestions]

    return {
        "operations": ops,
        "suggestions": sug,
        "notes": result.notes,
    }
