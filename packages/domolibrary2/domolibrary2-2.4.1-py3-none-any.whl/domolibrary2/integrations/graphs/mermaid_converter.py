"""Mermaid diagram converter for lineage graphs."""

from __future__ import annotations

__all__ = ["MermaidConverter"]

from typing import TYPE_CHECKING

from .base import GraphConverter
from .registry import register_converter
from ..mermaid import MermaidDiagram, MermaidNode, MermaidRelationship

if TYPE_CHECKING:
    from ...classes.subentity.lineage.graph import LineageGraph


@register_converter("mermaid")
class MermaidConverter(GraphConverter):
    """Convert lineage graph to Mermaid diagram."""

    def convert(
        self,
        graph: LineageGraph,
        direction: str = "TD",
        include_entity_ids: bool = True,
        **options,
    ) -> MermaidDiagram:
        """Convert LineageGraph to MermaidDiagram.

        Args:
            graph: LineageGraph with nodes and edges
            direction: Flowchart direction ("TD", "LR", "RL", "BT")
            include_entity_ids: Show entity IDs in node labels
            **options: Additional options (unused)

        Returns:
            MermaidDiagram ready for rendering
        """
        diagram = MermaidDiagram(
            direction=direction,
            title=f"Lineage for {graph.root_node.name if graph.root_node else 'Entity'}" if graph.root_node else None,
        )

        # Track nodes for relationship creation
        mermaid_nodes = {}

        # Add all nodes using factory method
        for node_key, node in graph.nodes.items():
            mermaid_node = MermaidNode.from_lineage_node(
                node=node,
                include_entity_ids=include_entity_ids,
            )
            diagram.add_node(mermaid_node)
            mermaid_nodes[node_key] = mermaid_node

        # Add all edges
        for edge in graph.edges:
            from_node = mermaid_nodes.get(edge.from_node_key)
            to_node = mermaid_nodes.get(edge.to_node_key)

            if from_node and to_node:
                # Map RelationshipType enum to lowercase string
                rel_type = edge.relationship_type.value.lower().replace("_", " ")

                relationship = MermaidRelationship(
                    from_node=from_node,
                    to_node=to_node,
                    type=rel_type,
                )
                diagram.add_relationship(relationship)

        return diagram

    def export_to_file(
        self,
        output: MermaidDiagram,
        file_path: str,
        footer_text: str | None = None,
        **options,
    ) -> None:
        """Export MermaidDiagram to markdown file.

        Args:
            output: MermaidDiagram from convert()
            file_path: Destination file path
            footer_text: Optional footer text for markdown
            **options: Additional options passed to export_to_markdown()
        """
        output.export_to_markdown(
            export_file=file_path,
            footer_text=footer_text,
            **options,
        )
