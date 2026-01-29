"""Neo4j Cypher query converter for lineage graphs."""

from __future__ import annotations

__all__ = ["Neo4jConverter"]

from typing import TYPE_CHECKING

from .base import GraphConverter
from .registry import register_converter

if TYPE_CHECKING:
    from ...classes.subentity.lineage.graph import LineageGraph


@register_converter("neo4j")
class Neo4jConverter(GraphConverter):
    """Convert lineage graph to Neo4j Cypher queries."""

    def convert(
        self,
        graph: LineageGraph,
        **options,
    ) -> list[str]:
        """Convert LineageGraph to Cypher CREATE queries.

        Args:
            graph: LineageGraph with nodes and edges
            **options: Additional options (unused)

        Returns:
            List of Cypher queries (nodes first, then relationships)
        """
        queries = []

        # Generate node creation queries
        queries.append("// Create nodes")
        for node_key, node in graph.nodes.items():
            labels = f":{node.entity_type}:DomoEntity"
            props = self._format_properties(node)
            query = f"CREATE (n{labels} {props})"
            queries.append(query)

        queries.append("")
        queries.append("// Create relationships")

        # Generate relationship creation queries
        for edge in graph.edges:
            from_id, from_type = edge.from_node_key
            to_id, to_type = edge.to_node_key
            rel_type = edge.relationship_type.value

            query = f"""
MATCH (start:{from_type} {{id: '{from_id}'}})
MATCH (end:{to_type} {{id: '{to_id}'}})
CREATE (start)-[r:{rel_type}]->(end)"""
            queries.append(query)

        return queries

    def _format_properties(self, node) -> str:
        """Format node properties as Cypher map.

        Args:
            node: LineageNode

        Returns:
            Cypher property map string
        """
        props = {
            "id": node.id,
            "name": node.name or "Unnamed",
            "entity_type": node.entity_type,
        }

        if node.domo_instance:
            props["domo_instance"] = node.domo_instance

        if node.is_federated:
            props["is_federated"] = True

        # Format as Cypher map
        prop_strs = []
        for key, value in props.items():
            if isinstance(value, bool):
                prop_strs.append(f"{key}: {str(value).lower()}")
            elif isinstance(value, str):
                # Escape single quotes in string values
                escaped_value = value.replace("'", "\\'")
                prop_strs.append(f"{key}: '{escaped_value}'")
            else:
                prop_strs.append(f"{key}: {value}")

        return "{" + ", ".join(prop_strs) + "}"

    def export_to_file(
        self,
        output: list[str],
        file_path: str,
        **options,
    ) -> None:
        """Export Cypher queries to .cypher file.

        Args:
            output: List of Cypher queries from convert()
            file_path: Destination file path
            **options: Additional options (unused)
        """
        with open(file_path, "w", encoding="utf-8") as f:
            for query in output:
                f.write(query)
                if not query.startswith("//"):
                    f.write(";")
                f.write("\n\n")
