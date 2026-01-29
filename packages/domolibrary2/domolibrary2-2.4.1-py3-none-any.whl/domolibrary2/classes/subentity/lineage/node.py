"""Lineage node and edge data structures for graph representation."""

from __future__ import annotations

__all__ = ["LineageNode", "LineageEdge"]

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ....auth import DomoAuth
    from ....base.entities import DomoEntity_w_Lineage
    from ..federation_context import FederationContext
    from .link import DomoLineage_Link
    from ..Relationships import RelationshipType


@dataclass
class LineageNode:
    """Core node representation for lineage graph operations.

    Separates data model (LineageNode) from presentation (MermaidNode).
    Designed for graph traversal, deduplication, and relationship tracking.

    All graph construction is synchronous - nodes are created from pre-loaded
    entity objects, no API calls occur during node creation.
    """

    # Core identity
    id: str
    entity_type: str  # Lineage type (CARD, DATA_SOURCE, SUBSCRIPTION, etc.)

    # Display metadata
    name: str | None = None

    # Entity reference (pre-loaded)
    entity: DomoEntity_w_Lineage | Any | None = None  # Any for Subscription/Publication

    # Instance context
    auth: DomoAuth | None = None
    domo_instance: str | None = None
    entity_class: str | None = None  # Entity class name without "Domo" prefix

    # Federation metadata
    is_federated: bool = False
    federation_context: FederationContext | None = None

    # Metadata
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __eq__(self, other: object) -> bool:
        """Equality by ID and entity_type (like DomoLineage_Link)."""
        if not isinstance(other, LineageNode):
            return False
        return self.id == other.id and self.entity_type == other.entity_type

    def __hash__(self) -> int:
        """Hash by ID and entity_type for set/dict operations."""
        return hash((self.id, self.entity_type))

    @property
    def node_key(self) -> tuple[str, str]:
        """Unique key for graph operations: (id, entity_type)."""
        return (self.id, self.entity_type)

    @classmethod
    def from_entity(cls, entity: DomoEntity_w_Lineage) -> LineageNode:
        """Create node from pre-loaded entity instance.

        Args:
            entity: Loaded DomoEntity_w_Lineage instance

        Returns:
            LineageNode with metadata extracted from entity
        """
        # Import here to avoid circular dependency
        from .link import _map_entity_type
        
        # Extract entity class name and remove "Domo" prefix
        entity_class = entity.__class__.__name__
        if entity_class.startswith("Domo"):
            entity_class = entity_class[4:]  # Remove "Domo" prefix
        
        return cls(
            id=entity.id,
            entity_type=_map_entity_type(entity.entity_type),  # Normalize to lineage type
            entity=entity,
            name=entity.name,
            auth=entity.auth,
            domo_instance=entity.auth.domo_instance,
            entity_class=entity_class,
            is_federated=getattr(entity, "is_federated", False),
            federation_context=(
                entity.Federation if hasattr(entity, "Federation") else None
            ),
            raw=entity.raw,
        )

    @classmethod
    def from_lineage_link(cls, link: DomoLineage_Link) -> LineageNode:
        """Create node from lineage link.

        Args:
            link: DomoLineage_Link (may or may not have loaded entity)

        Returns:
            LineageNode with available metadata
        """
        if link.entity:
            return cls.from_entity(link.entity)

        # Placeholder node (entity not loaded)
        entity_class = link.type.replace("_", "").title() if link.type else None
        return cls(
            id=link.id,
            entity_type=link.type,
            entity=None,
            auth=link.auth,
            domo_instance=link.auth.domo_instance if link.auth else None,
            entity_class=entity_class,
        )

    @classmethod
    def from_subscription(cls, subscription: Any) -> LineageNode:
        """Create node from DomoSubscription.

        Args:
            subscription: DomoSubscription instance

        Returns:
            LineageNode representing subscription
        """
        return cls(
            id=subscription.id,
            entity_type="SUBSCRIPTION",
            entity=subscription,
            name=subscription.name,
            entity_class="Subscription",
            domo_instance=(
                subscription.subscriber_domain.replace(".domo.com", "")
                if hasattr(subscription, "subscriber_domain")
                else None
            ),
            raw=getattr(subscription, "raw", {}),
        )

    @classmethod
    def from_publication(cls, publication: Any) -> LineageNode:
        """Create node from DomoPublication.

        Args:
            publication: DomoPublication instance

        Returns:
            LineageNode representing publication
        """
        return cls(
            id=publication.id,
            entity_type="PUBLICATION",
            entity=publication,
            name=publication.name,
            entity_class="Publication",
            # Publications exist on publisher instance
            raw=getattr(publication, "raw", {}),
        )


@dataclass
class LineageEdge:
    """Represents a directed relationship between two nodes in the lineage graph."""

    from_node_key: tuple[str, str]  # (id, entity_type)
    to_node_key: tuple[str, str]  # (id, entity_type)
    relationship_type: RelationshipType

    # Edge metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def __eq__(self, other: object) -> bool:
        """Equality by node keys and relationship type."""
        if not isinstance(other, LineageEdge):
            return False
        return (
            self.from_node_key == other.from_node_key
            and self.to_node_key == other.to_node_key
            and self.relationship_type == other.relationship_type
        )

    def __hash__(self) -> int:
        """Hash by node keys and relationship type."""
        return hash((self.from_node_key, self.to_node_key, self.relationship_type))
