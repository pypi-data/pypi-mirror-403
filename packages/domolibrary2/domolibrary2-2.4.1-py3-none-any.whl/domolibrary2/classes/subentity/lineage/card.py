"""Lineage handler for Card entities."""

from __future__ import annotations

__all__ = ["DomoLineage_Card"]

from dataclasses import dataclass
from typing import Any, Callable, Awaitable, TYPE_CHECKING

from .base import DomoLineage, register_lineage
from .link import DomoLineage_Link

if TYPE_CHECKING:
    from ....auth import DomoAuth
    from ....classes.DomoCard import DomoCard


@register_lineage(
    "DomoCard", "DomoCard_Default", "FederatedDomoCard", "DomoPublishCard"
)
@dataclass
class DomoLineage_Card(DomoLineage):
    """Lineage handler for card entities."""

    def _filter_lineage(
        self, lineage: list[DomoLineage_Link]
    ) -> list[DomoLineage_Link]:
        """Filter card lineage to only include direct datasources.

        A card's lineage should only contain its direct datasource (dataset or dataset_view),
        not the parent dataset of a view. The parent dataset belongs to the view's lineage, not the card's.

        However, when recursive lineage is enabled (_active_is_recursive=True), we preserve
        the complete upstream chain including DataFlows, upstream datasets, and other entities
        that are part of the transformation pipeline.

        Args:
            lineage: The lineage list to filter

        Returns:
            Filtered lineage list containing only direct datasources (non-recursive) or
            complete upstream chain (recursive)
        """
        # If recursive lineage is active, preserve the complete upstream chain
        # This ensures DataFlows, upstream datasets, and other transformation steps are visible
        if getattr(self, "_active_is_recursive", False):
            return lineage
        
        # Get direct datasource IDs from card metadata
        direct_datasource_ids = set()
        parent_raw = getattr(self.parent, "raw", None)
        if parent_raw:
            datasources = parent_raw.get("datasources", [])
            direct_datasource_ids = {
                str(ds.get("dataSourceId"))
                for ds in datasources
                if ds.get("dataSourceId")
            }

        if not direct_datasource_ids:
            return lineage

        return [
            item
            for item in lineage
            if item.type == "DATA_SOURCE" and str(item.id) in direct_datasource_ids
        ]

    def validate_datasources(self) -> dict[str, Any]:
        """Validate that this card has at most one datasource.

        CustomApp/EnterpriseApp cards (identified by having a datastore_id) are allowed
        to have multiple datasources. Regular cards should have at most one.

        Returns:
            Dictionary with validation results:
            - valid: bool - True if card has valid datasource count
            - datasource_count: int - Number of datasources
            - is_custom_app: bool - True if card is part of CustomApp/EnterpriseApp
            - violation: dict | None - Violation details if invalid, None otherwise
        """
        # Count DATA_SOURCE items in lineage
        datasource_count = sum(1 for item in self.lineage if item.type == "DATA_SOURCE")

        # Check if card is part of CustomApp/EnterpriseApp
        # Cards with datastore_id are CustomApp/EnterpriseApp cards
        is_custom_app = bool(getattr(self.parent, "datastore_id", None))

        # CustomApp/EnterpriseApp cards can have multiple datasources
        # Regular cards should have at most one
        max_allowed = float("inf") if is_custom_app else 1
        is_valid = datasource_count <= max_allowed

        result = {
            "valid": is_valid,
            "datasource_count": datasource_count,
            "is_custom_app": is_custom_app,
            "violation": None,
        }

        if not is_valid:
            # Use entity_name property if available
            if hasattr(self.parent, "entity_name"):
                card_name = self.parent.entity_name
            else:
                card_name = (
                    getattr(self.parent, "title", None)
                    or getattr(self.parent, "name", None)
                    or str(self.parent.id)
                )

            result["violation"] = {
                "card_id": self.parent.id,
                "card_name": card_name,
                "datasource_count": datasource_count,
                "max_allowed": max_allowed,
                "datasources": [
                    {
                        "id": item.id,
                        "name": (
                            item.entity.entity_name
                            if item.entity and hasattr(item.entity, "entity_name")
                            else (
                                getattr(item.entity, "name", item.id)
                                if item.entity
                                else item.id
                            )
                        ),
                    }
                    for item in self.lineage
                    if item.type == "DATA_SOURCE"
                ],
            }

        return result

    async def _resolve_publisher_card(
        self,
        subscription,
        publisher_auth: DomoAuth,
        include_pages: bool = True,
    ) -> DomoCard | None:
        """Resolve publisher card with caching, supporting indirect publication.

        Resolution strategy:
        1. Check cache for previously resolved publisher card
        2. Try direct resolution (card published directly)
        3. Try indirect resolution via page (card on published page)
        4. Raise error for App Studio cards (not yet supported)

        Args:
            subscription: DomoSubscription instance
            publisher_auth: Auth for publisher instance
            include_pages: Whether to support indirect resolution via pages

        Returns:
            Publisher DomoCard or None if resolution fails

        Raises:
            NotImplementedError: If card is in App Studio app (not supported)
        """
        if not self.parent.Federation:
            return None

        # Check cache first
        cache_key = f"CARD:{self.parent.id}"
        cache = self.parent.raw.setdefault('_indirect_resolution_cache', {})
        
        if cache_key in cache:
            return cache[cache_key]

        # Try direct resolution via FederationContext
        try:
            publisher_card = await self.parent.Federation.get_publisher_entity(
                parent_auth=publisher_auth,
            )
            cache[cache_key] = publisher_card
            return publisher_card
        except NotImplementedError:
            # App Studio cards - re-raise with context
            raise
        except Exception:
            # Log and continue to fallback
            return None
