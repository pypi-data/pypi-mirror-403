"""Base converter class for lineage graph exports."""

from __future__ import annotations

__all__ = ["GraphConverter"]

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...classes.subentity.lineage.graph import LineageGraph


class GraphConverter(ABC):
    """Abstract base converter for lineage graph export.

    Converters transform LineageGraph (format-agnostic data model)
    into specific export formats (Mermaid, Neo4j, GraphML, etc.).

    All conversion is synchronous - operates on pre-loaded graph data.
    """

    @abstractmethod
    def convert(
        self,
        graph: LineageGraph,
        **options,
    ) -> Any:
        """Convert graph to target format.

        Args:
            graph: LineageGraph with pre-loaded nodes and edges
            **options: Format-specific conversion options

        Returns:
            Format-specific output (MermaidDiagram, Cypher queries, etc.)
        """
        pass

    @abstractmethod
    def export_to_file(
        self,
        output: Any,
        file_path: str,
        **options,
    ) -> None:
        """Export converted output to file.

        Args:
            output: Result from convert() method
            file_path: Destination file path
            **options: Format-specific export options
        """
        pass
