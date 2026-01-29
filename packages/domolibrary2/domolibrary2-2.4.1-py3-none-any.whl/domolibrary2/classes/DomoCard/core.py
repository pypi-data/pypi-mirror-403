"""Core DomoCard classes"""

__all__ = [
    "DomoCard",
]

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ...auth import DomoAuth
from ..subentity.lineage import register_lineage_type
from .card_default import DomoCard_Default


@register_lineage_type("DomoCard", lineage_type="CARD")
@dataclass
class DomoCard(DomoCard_Default):
    """DomoCard factory class that uses composition for federated support"""

    @classmethod
    def from_dict(
        cls,
        auth: DomoAuth,
        obj: dict,
        owners: list[Any] = None,
        is_published: bool = False,
        parent_auth_retrieval_fn: Callable | None = None,
        parent_auth: DomoAuth | None = None,
        **kwargs,
    ) -> "DomoCard":
        """Convert API response dictionary to DomoCard instance.

        For federated cards, use composition via card.Federation helper.
        """

        # Build the card instance
        card = cls(
            auth=auth,
            id=obj.get("id"),
            raw=obj,
            title=obj.get("title"),
            description=obj.get("description"),
            type=obj.get("type"),
            urn=obj.get("urn"),
            certification=obj.get("certification"),
            chart_type=obj.get("metadata", {}).get("chartType"),
            dataset_id=(
                obj.get("datasources", [])[0].get("dataSourceId")
                if obj.get("datasources")
                else None
            ),
            owners=owners or [],
            datastore_id=obj.get("domoapp", {}).get("id"),
        )

        # Enable federation support if card is federated
        if card.is_federated:
            card.enable_federation_support()

        return card
