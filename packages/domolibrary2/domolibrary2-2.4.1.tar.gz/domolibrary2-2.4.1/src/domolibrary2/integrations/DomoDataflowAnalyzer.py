from __future__ import annotations

"""Analyze scripting tiles and suggest Magic ETL alternatives.

This module inspects Python scripts from Magic ETL "Scripting" tiles and
suggests equivalent DomoDataflow actions that avoid data science tiles when
possible. It is intentionally heuristic and lightweight (AST-based) so it can
run locally without LLMs. LLM-based refinements can be added later using the
LangGraph multi-agent pattern.
"""

import ast
from dataclasses import dataclass, field
from typing import Any


@dataclass
class OperationDetection:
    """Represents an operation discovered inside the scripting tile."""

    kind: str
    description: str
    columns: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    confidence: float = 0.5
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class SuggestedAction:
    """Represents a proposed Magic ETL action alternative."""

    action_type: str
    category: str
    rationale: str
    confidence: float
    columns: list[str] = field(default_factory=list)


@dataclass
class ScriptAnalysisResult:
    """Container for the full analysis output."""

    operations: list[OperationDetection] = field(default_factory=list)
    suggestions: list[SuggestedAction] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class DomoDataflowAnalyzer:
    """Analyze scripting tiles and suggest Magic ETL substitutions.

    Usage:
        analyzer = DomoDataflowAnalyzer()
        result = analyzer.analyze(script_str)
    """

    def analyze(self, script: str) -> ScriptAnalysisResult:
        if not script:
            raise ValueError("script must be a non-empty string")

        tree = ast.parse(script)
        function_patterns = self._index_function_patterns(tree)
        operations = self._detect_operations(tree, function_patterns)
        suggestions = self._suggest_actions(operations)
        notes = self._build_notes(operations, suggestions)

        return ScriptAnalysisResult(
            operations=operations,
            suggestions=suggestions,
            notes=notes,
        )

    def _index_function_patterns(self, tree: ast.AST) -> dict[str, set[str]]:
        patterns: dict[str, set[str]] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                detected = self._detect_function_patterns(node)
                if detected:
                    patterns[node.name] = detected

        return patterns

    def _detect_operations(
        self, tree: ast.AST, function_patterns: dict[str, set[str]]
    ) -> list[OperationDetection]:
        operations: list[OperationDetection] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_op = self._detect_io_operation(node)
                if call_op:
                    operations.append(call_op)

            if isinstance(node, ast.Assign):
                apply_op = self._detect_apply_operation(node, function_patterns)
                if apply_op:
                    operations.append(apply_op)

        return operations

    def _detect_io_operation(self, call_node: ast.Call) -> OperationDetection | None:
        func = call_node.func

        if isinstance(func, ast.Name) and func.id in {
            "read_dataframe",
            "write_dataframe",
        }:
            target_name = None
            if call_node.args and isinstance(call_node.args[0], ast.Constant):
                target_name = str(call_node.args[0].value)

            direction = "input" if func.id == "read_dataframe" else "output"
            description = f"{func.id} detected" + (
                f" for {target_name}" if target_name else ""
            )

            return OperationDetection(
                kind=func.id,
                description=description,
                columns=[],
                functions=[],
                confidence=0.9,
                detail={"direction": direction, "target_name": target_name},
            )

        return None

    def _detect_apply_operation(
        self, assign_node: ast.Assign, function_patterns: dict[str, set[str]]
    ) -> OperationDetection | None:
        value = assign_node.value
        if not isinstance(value, ast.Call):
            return None

        func = value.func
        if not isinstance(func, ast.Attribute) or func.attr != "apply":
            return None

        source_column = self._extract_column_name(func.value)
        target_column = self._extract_column_name(assign_node.targets[0])

        applied_function = None
        if value.args and isinstance(value.args[0], ast.Name):
            applied_function = value.args[0].id

        patterns = function_patterns.get(applied_function, set())
        description = "Column apply() detected"
        columns = [c for c in [source_column, target_column] if c]
        functions = [applied_function] if applied_function else []

        return OperationDetection(
            kind="apply",
            description=description,
            columns=columns,
            functions=functions,
            confidence=0.7,
            detail={
                "source_column": source_column,
                "target_column": target_column,
                "applied_function": applied_function,
                "patterns": sorted(patterns),
            },
        )

    def _detect_function_patterns(self, func_def: ast.FunctionDef) -> set[str]:
        patterns: set[str] = set()

        for node in ast.walk(func_def):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "split" and node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Constant):
                        delimiter = str(arg.value)
                        if delimiter == "@":
                            patterns.add("split_email_local_part")
                        if delimiter == ".":
                            patterns.add("split_dot_segments")
                if node.func.attr == "capitalize":
                    patterns.add("capitalize_parts")
                if node.func.attr in {"upper", "lower", "title"}:
                    patterns.add(f"text_{node.func.attr}")

            if isinstance(node, ast.JoinedStr):
                patterns.add("fstring_concatenation")

        return patterns

    def _extract_column_name(self, subscript: ast.AST) -> str | None:
        if not isinstance(subscript, ast.Subscript):
            return None

        slice_value = subscript.slice
        if isinstance(slice_value, ast.Constant) and isinstance(slice_value.value, str):
            return slice_value.value

        return None

    def _suggest_actions(
        self, operations: list[OperationDetection]
    ) -> list[SuggestedAction]:
        suggestions: list[SuggestedAction] = []

        for op in operations:
            if op.kind == "apply":
                patterns = set(op.detail.get("patterns", []))
                source_col = op.detail.get("source_column")
                target_col = op.detail.get("target_column")

                if (
                    "split_email_local_part" in patterns
                    or "split_dot_segments" in patterns
                ):
                    suggestions.append(
                        SuggestedAction(
                            action_type="SplitColumnAction",
                            category="text",
                            rationale=(
                                "Detected string splitting; consider Split Column with delimiter '@'"
                                " followed by '.' to derive names."
                            ),
                            confidence=0.78,
                            columns=[c for c in [source_col, target_col] if c],
                        )
                    )

                if "capitalize_parts" in patterns:
                    suggestions.append(
                        SuggestedAction(
                            action_type="TextFormatting",
                            category="text",
                            rationale="Detected capitalization of split parts; apply Text Formatting to title-case segments.",
                            confidence=0.62,
                            columns=[c for c in [target_col] if c],
                        )
                    )

                if not patterns:
                    suggestions.append(
                        SuggestedAction(
                            action_type="ExpressionEvaluator",
                            category="utility",
                            rationale="Custom apply detected; consider translating logic into a formula tile (Expression Evaluator).",
                            confidence=0.4,
                            columns=[c for c in [source_col, target_col] if c],
                        )
                    )

        return suggestions

    def _build_notes(
        self, operations: list[OperationDetection], suggestions: list[SuggestedAction]
    ) -> list[str]:
        notes: list[str] = []

        if any(op.kind == "apply" for op in operations):
            notes.append(
                "Scripting tiles are heavier; prefer native text/utility tiles when possible."
            )

        if any(s.action_type == "SplitColumnAction" for s in suggestions):
            notes.append(
                "Split Column can replace email parsing; combine with Text Formatting for capitalization."
            )

        if not suggestions:
            notes.append(
                "No clear ETL substitutions detected; keep scripting tile or refine heuristics."
            )

        return notes
