"""Lineage graph data structure for representing entity relationships."""

from __future__ import annotations

__all__ = ["LineageGraph"]

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .node import LineageEdge, LineageNode
from ..Relationships import RelationshipType

if TYPE_CHECKING:
    from ....base.entities import DomoEntity_w_Lineage
    from .link import DomoLineage_Link


@dataclass
class LineageGraph:
    """Format-agnostic lineage graph data structure.

    Manages nodes and edges representing lineage relationships across
    potentially multiple Domo instances (subscriber + publisher).

    Graph construction is synchronous - operates on pre-loaded entity
    objects from DomoLineage_Link list.
    """

    nodes: dict[tuple[str, str], LineageNode] = field(default_factory=dict)
    edges: list[LineageEdge] = field(default_factory=list)
    root_node: LineageNode | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: LineageNode) -> None:
        """Add node to graph (deduplicates by node_key).

        Args:
            node: LineageNode to add
        """
        self.nodes[node.node_key] = node

    def add_edge(
        self,
        from_node: LineageNode,
        to_node: LineageNode,
        relationship_type: RelationshipType,
    ) -> None:
        """Add directed edge between nodes.

        Args:
            from_node: Source node
            to_node: Target node
            relationship_type: Type of relationship
        """
        edge = LineageEdge(
            from_node_key=from_node.node_key,
            to_node_key=to_node.node_key,
            relationship_type=relationship_type,
        )
        if edge not in self.edges:
            self.edges.append(edge)

    def get_node(self, node_key: tuple[str, str]) -> LineageNode | None:
        """Get node by key.

        Args:
            node_key: (id, entity_type) tuple

        Returns:
            LineageNode or None if not found
        """
        return self.nodes.get(node_key)

    def get_dependencies(self, node: LineageNode) -> list[LineageNode]:
        """Get all nodes that the given node depends on (upstream).

        Args:
            node: Node to get dependencies for

        Returns:
            List of upstream nodes
        """
        return [
            self.nodes[edge.to_node_key]
            for edge in self.edges
            if edge.from_node_key == node.node_key
            and edge.to_node_key in self.nodes
        ]

    def get_dependents(self, node: LineageNode) -> list[LineageNode]:
        """Get all nodes that depend on the given node (downstream).

        Args:
            node: Node to get dependents for

        Returns:
            List of downstream nodes
        """
        return [
            self.nodes[edge.from_node_key]
            for edge in self.edges
            if edge.to_node_key == node.node_key
            and edge.from_node_key in self.nodes
        ]

    @classmethod
    def _process_lineage_dependencies(
        cls,
        graph: LineageGraph,
        parent_link: Any,  # DomoLineageLink
        parent_node: LineageNode,
    ):
        """Process dependencies of a lineage link recursively.
        
        Args:
            graph: The LineageGraph to add nodes/edges to
            parent_link: The DomoLineageLink whose dependencies to process
            parent_node: The LineageNode for the parent
        """
        if not hasattr(parent_link, 'dependencies') or not parent_link.dependencies:
            return
        
        for dep_link in parent_link.dependencies:
            if not dep_link.entity:
                continue
            
            # Prevent self-loops
            if dep_link.id == parent_link.id:
                continue
            
            dep_node = LineageNode.from_lineage_link(dep_link)
            graph.add_node(dep_node)
            
            # Determine relationship type
            # Fixed: dependencies point TO consumers (dep_node → parent_node)
            rel_type = cls._determine_relationship_type(
                from_entity=dep_link.entity,
                to_entity=parent_link.entity,
            )
            
            graph.add_edge(dep_node, parent_node, rel_type)
            
            # Recursively process dependencies
            cls._process_lineage_dependencies(graph, dep_link, dep_node)

    @classmethod
    def from_lineage_links(
        cls,
        links: list[DomoLineage_Link],
        root_entity: DomoEntity_w_Lineage,
    ) -> LineageGraph:
        """Build graph from DomoLineage_Link list (synchronous operation).

        Constructs nodes and edges from pre-loaded entities. If root_entity
        has federation context (subscription/publication), includes federation
        nodes and publisher entities in the graph.

        Args:
            links: List of DomoLineage_Link with loaded entities
            root_entity: Root entity (card, dataset, etc.) that owns this lineage

        Returns:
            LineageGraph with nodes from subscriber and publisher instances
        """
        graph = cls()

        # Add root node
        root_node = LineageNode.from_entity(root_entity)
        graph.add_node(root_node)
        graph.root_node = root_node

        # Import _map_entity_type to normalize entity types for comparison
        from .link import _map_entity_type
        root_entity_type_mapped = _map_entity_type(root_entity.entity_type)

        # Process ALL links - these are the direct dependencies of the root
        # (API returns dependencies separately, not including the root entity itself)
        for link in links:
            if not link.entity:
                continue
            
            # Prevent self-loops (though API shouldn't return root in its own dependencies)
            if link.id == root_entity.id and link.type == root_entity_type_mapped:
                continue
            
            # Create node for this dependency
            node = LineageNode.from_lineage_link(link)
            graph.add_node(node)
            
            # Add edge: dependency → root (dependency feeds into root)
            rel_type = cls._determine_relationship_type(
                from_entity=link.entity,
                to_entity=root_entity,
            )
            graph.add_edge(node, root_node, rel_type)
            
            # Recursively process this dependency's own dependencies
            cls._process_lineage_dependencies(graph, link, node)

        # Add federation nodes if applicable
        if hasattr(root_entity, "Federation") and root_entity.Federation:
            federation = root_entity.Federation
            subscription = federation.subscription

            if subscription:
                # Add subscription node
                sub_node = LineageNode.from_subscription(subscription)
                graph.add_node(sub_node)

                # Add edge: root_entity SUBSCRIBES_TO subscription
                graph.add_edge(
                    root_node,
                    sub_node,
                    RelationshipType.SUBSCRIBES_TO,
                )

                # Add publication node if available
                publication = getattr(subscription, "parent_publication", None)
                if publication:
                    pub_node = LineageNode.from_publication(publication)
                    graph.add_node(pub_node)

                    # Add edge: subscription PUBLISHED_VIA publication
                    graph.add_edge(
                        sub_node,
                        pub_node,
                        RelationshipType.PUBLISHED_VIA,
                    )

                    # Determine target publisher entity ID for filtering
                    publisher_entity = federation.publisher_entity
                    target_publisher_id = publisher_entity.id if publisher_entity else None
                    
                    print(f"DEBUG: target_publisher_id={target_publisher_id}")
                    
                    # Process publication lineage using categorized properties
                    # Publication.Lineage.lineage contains DomoLineageLink objects for all content
                    if hasattr(publication, "Lineage") and publication.Lineage and publication.Lineage.lineage:
                        # Check if target entity is directly published (in cards/datasets)
                        target_link = None
                        for link in publication.Lineage.cards:
                            if target_publisher_id and link.entity and link.entity.id == target_publisher_id:
                                target_link = link
                                break
                        
                        # If not found in cards, check datasets
                        if not target_link:
                            for link in publication.Lineage.datasets:
                                if target_publisher_id and link.entity and link.entity.id == target_publisher_id:
                                    target_link = link
                                    break
                        
                        # If target is directly published, add it and its lineage
                        if target_link:
                            print(f"DEBUG: Target entity {target_publisher_id} is directly published")
                            target_node = LineageNode.from_lineage_link(target_link)
                            graph.add_node(target_node)
                            
                            # Add edge: publication CONTAINS target
                            graph.add_edge(
                                pub_node,
                                target_node,
                                RelationshipType.CONTAINS,
                            )
                            
                            # Add target's dependencies (recursive lineage)
                            cls._process_lineage_dependencies(
                                graph, target_link, target_node
                            )
                        
                        # Check if target is published indirectly via pages
                        else:
                            print(f"DEBUG: Checking pages for indirect publication of target {target_publisher_id}")
                            for page_link in publication.Lineage.pages:
                                if not page_link.entity:
                                    continue
                                
                                # Check if page has the target card in its dependencies
                                # Pages contain cards via Layout.cards, which are dependencies
                                page_contains_target = False
                                target_card_link = None
                                
                                # Check page's dependencies for target card
                                if hasattr(page_link, 'dependencies') and page_link.dependencies:
                                    for dep in page_link.dependencies:
                                        if dep.type == "CARD" and dep.entity and dep.entity.id == target_publisher_id:
                                            page_contains_target = True
                                            target_card_link = dep
                                            break
                                
                                # If page doesn't have dependencies loaded, check Layout.cards
                                if not page_contains_target and hasattr(page_link.entity, "Layout") and page_link.entity.Layout:
                                    if hasattr(page_link.entity.Layout, "cards") and page_link.entity.Layout.cards:
                                        for card in page_link.entity.Layout.cards:
                                            if card.id == target_publisher_id:
                                                page_contains_target = True
                                                # Create link for target card
                                                from .link import DomoLineageLink_Card
                                                target_card_link = DomoLineageLink_Card(
                                                    auth=page_link.auth,
                                                    id=str(card.id),
                                                    entity=card,
                                                    _type="CARD",
                                                    dependents=[],
                                                    dependencies=[],
                                                )
                                                break
                                
                                if page_contains_target:
                                    print(f"DEBUG: Page {page_link.id} contains target card {target_publisher_id}")
                                    
                                    # Add page node
                                    page_node = LineageNode.from_lineage_link(page_link)
                                    graph.add_node(page_node)
                                    
                                    # Add edge: publication CONTAINS page
                                    graph.add_edge(
                                        pub_node,
                                        page_node,
                                        RelationshipType.CONTAINS,
                                    )
                                    
                                    # Add target card node
                                    if target_card_link:
                                        card_node = LineageNode.from_lineage_link(target_card_link)
                                        graph.add_node(card_node)
                                        
                                        # Add edge: page CONTAINS card
                                        graph.add_edge(
                                            page_node,
                                            card_node,
                                            RelationshipType.CONTAINS,
                                        )
                                        
                                        # Add target card's dependencies (recursive lineage)
                                        cls._process_lineage_dependencies(
                                            graph, target_card_link, card_node
                                        )
                                    
                                    # Only process first page that contains target
                                    break

        return graph

    @staticmethod
    def _determine_relationship_type(
        from_entity: Any,
        to_entity: Any,
    ) -> RelationshipType:
        """Determine relationship type between two entities.

        Args:
            from_entity: Source entity
            to_entity: Target entity

        Returns:
            Appropriate RelationshipType enum value
        """
        from_type = getattr(from_entity, "entity_type", "UNKNOWN")
        to_type = getattr(to_entity, "entity_type", "UNKNOWN")

        if from_type in ("CARD", "PAGE") and to_type == "DATA_SOURCE":
            return RelationshipType.USES_DATA_FROM

        if from_type == "DATA_SOURCE" and to_type == "DATA_SOURCE":
            if hasattr(to_entity, "is_federated") and to_entity.is_federated:
                return RelationshipType.IS_FEDERATED_FROM
            return RelationshipType.IS_DERIVED_FROM

        if from_type == "DATAFLOW" and to_type == "DATA_SOURCE":
            return RelationshipType.IS_DERIVED_FROM

        return RelationshipType.USES_DATA_FROM

    @classmethod
    async def from_entity_with_federation(
        cls,
        entity: DomoEntity_w_Lineage,
        include_federation: bool = True,
        parent_auth_retrieval_fn: Callable[[str], Awaitable[DomoAuth]] | None = None,
        context: LineageContext | None = None,
    ) -> LineageGraph:
        """Build graph with pre-loaded federation content for complete relationships.

        This method ensures that Page → Card edges appear correctly by pre-loading
        all publication content lineage before graph construction.

        Args:
            entity: Entity to build graph for
            include_federation: Whether to include federation nodes
            parent_auth_retrieval_fn: Function to retrieve auth for parent instances
            context: Optional lineage context

        Returns:
            Complete lineage graph with all relationships

        Raises:
            ValueError: If entity doesn't support lineage
        """
        # Step 1: Get entity lineage (this populates entity.Lineage.lineage)
        await entity.Lineage.get(
            include_federation=include_federation,
            parent_auth_retrieval_fn=parent_auth_retrieval_fn,
            context=context,
        )

        # Step 2: If federated, ensure publication content lineage is loaded
        if include_federation and entity.is_federated and entity.Federation:
            try:
                # Get parent publication (may already be cached)
                publication = await entity.Federation.get_parent_publication(
                    parent_auth_retrieval_fn=parent_auth_retrieval_fn,
                )

                # Pre-load lineage for all publication content items
                if publication and hasattr(publication, "content") and publication.content:
                    # Import here to avoid circular dependency
                    from ...DomoEverywhere import DomoPage

                    for content_item in publication.content:
                        if not content_item.entity:
                            continue

                        # For pages, explicitly load cards
                        if isinstance(content_item.entity, DomoPage):
                            if content_item.entity.Layout:
                                await content_item.entity.Layout.get_cards(context=context)

                        # Load lineage for the content entity
                        if hasattr(content_item.entity, "Lineage"):
                            await content_item.entity.Lineage.get(
                                include_federation=False,  # Don't recurse federation
                                context=context,
                            )
            except Exception:
                # If federation loading fails, continue with base lineage
                pass

        # Step 3: Build graph from fully loaded lineage data
        return cls.from_lineage_links(
            entity=entity,
            include_federation=include_federation,
        )
