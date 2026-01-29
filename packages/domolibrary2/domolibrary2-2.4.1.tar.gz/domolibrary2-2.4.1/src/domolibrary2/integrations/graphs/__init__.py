"""Graph export converters for lineage data.

Provides pluggable converters to transform LineageGraph into various
export formats (Mermaid, Neo4j, GraphML, etc.).

Usage:
    from domolibrary2.integrations.graphs import get_converter

    converter = get_converter("mermaid")()
    diagram = converter.convert(graph, direction="LR")
    converter.export_to_file(diagram, "output.md")
"""

from __future__ import annotations

# Base classes
from .base import GraphConverter

# Registry
from .registry import get_converter, list_converters, register_converter

# Converters (import to register)
from . import mermaid_converter  # noqa: F401
from . import neo4j_converter  # noqa: F401

__all__ = [
    "GraphConverter",
    "get_converter",
    "list_converters",
    "register_converter",
]
