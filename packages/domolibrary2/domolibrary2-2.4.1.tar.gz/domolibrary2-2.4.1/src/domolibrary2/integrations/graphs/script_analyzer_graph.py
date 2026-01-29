from __future__ import annotations

from typing import Any

from ..agents.script_analyzer.code_analyzer_agent import run_code_analysis
from ..agents.script_analyzer.models import PythonAnalysisState
from ..agents.script_analyzer.pattern_matcher_agent import run_pattern_matching
from ..agents.script_analyzer.recommendation_agent import run_recommendations


def compile_script_analyzer_graph():
    """Compile the LangGraph workflow for script analysis.

    This function imports langgraph dynamically to avoid hard dependency
    when only the basic analyzer is used.
    """
    try:
        from langgraph.graph import END, START, StateGraph
    except Exception as exc:  # ImportError or other
        raise RuntimeError(
            "LangGraph not installed; please add 'langgraph' dependency to use the graph."
        ) from exc

    workflow = StateGraph(PythonAnalysisState)

    workflow.add_node("code_analyzer", run_code_analysis)
    workflow.add_node("pattern_matcher", run_pattern_matching)
    workflow.add_node("recommendations", run_recommendations)

    workflow.add_edge(START, "code_analyzer")
    workflow.add_edge("code_analyzer", "pattern_matcher")
    workflow.add_edge("pattern_matcher", "recommendations")
    workflow.add_edge("recommendations", END)

    return workflow.compile()


def run_workflow(script: str) -> dict[str, Any]:
    """Run the compiled workflow against a Python script and return output state."""
    graph = compile_script_analyzer_graph()
    initial: PythonAnalysisState = {"python_script": script}
    result = graph.invoke(initial)
    return dict(result)
