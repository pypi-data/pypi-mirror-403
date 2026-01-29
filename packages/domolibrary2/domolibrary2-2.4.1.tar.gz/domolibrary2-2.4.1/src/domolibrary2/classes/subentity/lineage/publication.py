"""Lineage handlers for Publication and Subscription entities."""

from __future__ import annotations

__all__ = ["DomoLineage_Publication", "DomoLineage_Subscription"]

import inspect
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import httpx

from ....auth import DomoAuth
from ....base.exceptions import ClassError
from ....client.context import RouteContext
from ....utils import chunk_execution as dmce
from .base import DomoLineage, register_lineage
from .link import DomoLineageLink_Publication


@dataclass
class DomoLineage_Everywhere(DomoLineage, ABC):
    """Base class for lineage handlers that manage content collections.
    
    Provides property-based access to categorized lineage links (datasets, cards, pages).
    Used by both Publication and Subscription lineage handlers.
    
    Important Conceptual Model:
    - For Publication: datasets/cards/pages are the INPUTS (what was published)
    - For Subscription: datasets/cards/pages are the INPUTS from publication
    - Federated entities in subscriber instance are DOWNSTREAM/CHILDREN of subscription
      (created as a result of subscription, not part of lineage chain)
    
    Properties filter self.lineage (list of DomoLineageLink objects) by type:
    - datasets: Links with type="DATA_SOURCE" or "DATASET"
    - cards: Links with type="CARD"
    - pages: Links with type="PAGE"
    - unsorted: Links with unrecognized types
    """

    @property
    def datasets(self) -> list[Any]:
        """Get dataset links from lineage.
        
        Returns:
            List of DomoLineageLink objects with type DATA_SOURCE or DATASET
        """
        if not self.lineage:
            return []
        return [
            link for link in self.lineage 
            if link.type in ("DATA_SOURCE", "DATASET")
        ]
    
    @property
    def cards(self) -> list[Any]:
        """Get card links from lineage.
        
        Returns:
            List of DomoLineageLink objects with type CARD
        """
        if not self.lineage:
            return []
        return [link for link in self.lineage if link.type == "CARD"]
    
    @property
    def pages(self) -> list[Any]:
        """Get page links from lineage.
        
        Returns:
            List of DomoLineageLink objects with type PAGE
        """
        if not self.lineage:
            return []
        return [link for link in self.lineage if link.type == "PAGE"]
    
    @property
    def unsorted(self) -> list[Any]:
        """Get links with unrecognized types from lineage.
        
        Returns:
            List of DomoLineageLink objects that don't match known types
        """
        if not self.lineage:
            return []
        known_types = {"DATA_SOURCE", "DATASET", "CARD", "PAGE", "PUBLICATION", "SUBSCRIPTION"}
        unsorted = [link for link in self.lineage if link.type not in known_types]
        
        if unsorted:
            print(
                f"Unsorted lineage items: {', '.join([link.type for link in unsorted])}"
            )
        
        return unsorted

    @abstractmethod
    async def get(
        self,
        session: httpx.AsyncClient = None,
        debug_api: bool = False,
        return_raw: bool = False,
        parent_auth: DomoAuth = None,
        parent_auth_retrieval_fn: Callable = None,
        is_recursive: bool = False,
        max_depth: int | None = None,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ):
        """Get lineage for the entity - must be implemented by subclasses."""
        ...


@register_lineage("DomoPublication")
@dataclass
class DomoLineage_Publication(DomoLineage_Everywhere):
    """Lineage handler for publication entities.

    The parent is the publication entity this lineage is based off of (not a dependency).
    Publications contain multiple entities (datasets, cards, pages).
    """


    async def _get_content_item_lineage(
        self,
        pc,  # DomoEntity - publication content item
        session: httpx.AsyncClient | None = None,
        debug_api: bool = False,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ):
        """Get lineage for a single publication content item.

        Args:
            pc: Publication content entity
            session: HTTP session for API calls
            debug_api: Enable API debugging
            context: Optional RouteContext for API call configuration
            **context_kwargs: Additional context parameters

        Returns:
            Lineage list for the content item

        Note:
            All publication content types (Card, Dataset, Page, AppStudio) extend
            DomoEntity_w_Lineage, so they are guaranteed to have Lineage support.
        """
        context = RouteContext.build_context(
            context=context,
            session=session,
            debug_api=debug_api,
            **context_kwargs,
        )

        # Fetch the entity instance - all publication content types have Lineage
        await pc.get_entity(context=context)

        # If the entity is a page, fetch its full lineage (includes cards)
        # This ensures page->card relationships are available when building the graph
        # We call Lineage.get() which populates entity.Lineage.lineage for graph building
        if pc.entity.__class__.__name__ == "DomoPage":
            if hasattr(pc.entity, "Lineage") and pc.entity.Lineage:
                await pc.entity.Lineage.get(
                    session=session,
                    debug_api=debug_api,
                    context=context,
                    **context_kwargs,
                )

        # Get the immediate lineage (list of DomoLineage_Link objects)
        return await pc.entity.Lineage._get_immediate_lineage(
            session=session,
            debug_api=debug_api,
            context=context,
            **context_kwargs,
        )

    async def get(
        self,
        session: httpx.AsyncClient = None,
        debug_api: bool = False,
        return_raw: bool = False,
        parent_auth: DomoAuth = None,
        parent_auth_retrieval_fn: Callable = None,
        is_recursive: bool = False,
        max_depth: int | None = None,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ):
        """Get lineage for all content items in the publication.

        Orchestrates fetching lineage for each content item and categorizing the results.
        """
        context = RouteContext.build_context(
            context=context,
            session=session,
            debug_api=debug_api,
            **context_kwargs,
        )

        if not self.parent:
            raise ClassError(
                message="Parent must be set. Use from_parent() to create lineage with a parent.",
                cls_instance=self,
            )

        # Ensure content is loaded - if not already populated, refetch the publication
        if not self.parent.content:
            from ...DomoEverywhere import DomoPublication

            refreshed_pub = await DomoPublication.get_by_id(
                publication_id=self.parent.id,
                auth=self.parent.auth,
                context=context,
            )
            self.parent.content = refreshed_pub.content

        if return_raw:
            return self.parent.content

        # Gather lineage for all content items concurrently
        lineage = await dmce.gather_with_concurrency(
            *[
                self._get_content_item_lineage(
                    pc=pc,
                    context=context,
                )
                for pc in self.parent.content
                if pc
            ],
            n=10,
        )

        # Flatten the list of lists and filter out None values
        result = [ele for sublist in lineage if sublist for ele in sublist]

        # Cache the result for future use
        # Properties (datasets, cards, pages) will filter self.lineage by type
        self.lineage = result
        return result


@register_lineage("DomoSubscription")
@dataclass
class DomoLineage_Subscription(DomoLineage_Everywhere):
    """Lineage handler for subscription entities.
    
    Provides categorized access to subscription content via datasets, cards, pages properties.
    
    Conceptual Model:
    - self.lineage contains: [publication_link] + target_entity_upstream_lineage
    - datasets/cards/pages properties categorize items from lineage chain
    - These represent INPUTS to the publication (what was published)
    - Federated entities in subscriber instance are DOWNSTREAM/CHILDREN of subscription:
      * They are created as a result of the subscription
      * They depend ON the subscription (not part of subscription's upstream lineage)
      * They should be accessed via subscription.get_federated_entities() (if needed)
    """

    @property
    def parent_publication(self):
        """Get the parent publication entity from the subscription.
        
        Returns:
            DomoPublication entity if available in lineage
        """
        if not self.lineage:
            return None
        
        # First item in lineage is the publication link
        for link in self.lineage:
            if link.type == "PUBLICATION" and link.entity:
                return link.entity
        
        return None
    
    @property
    def content(self):
        """Get the publication content items (what was published/publication inputs).
        
        Returns:
            List of publication content items (PAGE, CARD, DATASET, etc.) that are
            INPUTS to the publication (what was published).
            
        Note:
            These are NOT the federated entities in the subscriber instance.
            Federated subscriber entities are DOWNSTREAM/CHILDREN of the subscription
            and should be accessed separately if needed.
        """
        pub = self.parent_publication
        if not pub:
            return []
        
        # If publication has lineage populated, return it (content items only)
        if hasattr(pub, 'Lineage') and pub.Lineage and pub.Lineage.lineage:
            return pub.Lineage.lineage
        
        # Otherwise return raw content
        return getattr(pub, 'content', [])

    async def get(
        self,
        session: httpx.AsyncClient = None,
        debug_api: bool = False,
        return_raw: bool = False,
        parent_auth: DomoAuth | None = None,
        parent_auth_retrieval_fn: Callable | None = None,
        is_recursive: bool = False,
        max_depth: int | None = None,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ):
        context = RouteContext.build_context(
            context=context,
            session=session,
            debug_api=debug_api,
            **context_kwargs,
        )

        publisher_auth = parent_auth
        if not publisher_auth and parent_auth_retrieval_fn:
            auth_or_coro = parent_auth_retrieval_fn(self.parent.publisher_domain)
            if inspect.isawaitable(auth_or_coro):
                publisher_auth = await auth_or_coro
            else:
                publisher_auth = auth_or_coro

        if not publisher_auth:
            raise ClassError(
                cls_instance=self.parent,
                message=(
                    "parent_auth (publisher auth) is required to resolve "
                    "subscription lineage."
                ),
            )

        publication = await self.parent.get_parent_publication(
            parent_auth=publisher_auth,
            parent_auth_retrieval_fn=parent_auth_retrieval_fn,
            context=context,
            **context_kwargs,
        )

        if return_raw:
            return publication.raw

        publication_link = DomoLineageLink_Publication(
            auth=publisher_auth,
            id=str(publication.id),
            entity=publication,
            _type="PUBLICATION",
            dependents=[],
            dependencies=[],
        )

        # Get publication content as dependencies (just the published items, not their lineage)
        # These are INPUTS to the publication (what was published)
        # Note: Federated entities in subscriber are DOWNSTREAM/CHILDREN (not in this lineage)
        publication_content_links = await publication.Lineage.get(
            session=session,
            debug_api=debug_api,
            return_raw=False,
            parent_auth=publisher_auth,
            parent_auth_retrieval_fn=parent_auth_retrieval_fn,
            is_recursive=False,  # Just content items, not their dependencies
            max_depth=None,
            context=context,
            **context_kwargs,
        )
        
        # Store content as publication dependencies
        publication_link.dependencies = list(publication_content_links)
        
        print(f"DEBUG publication_link.dependencies: {[(d.type, d.id) for d in publication_link.dependencies]}")
        
        # For the subscriber entity, get the matching publisher entity and its lineage
        # This is the entity we actually care about (not all publication content)
        subscriber_entity = self.parent.raw.get('_subscriber_entity')  # May be set by caller
        target_card_lineage = []
        
        if subscriber_entity and publication.Federation:
            # Get the publisher entity that matches our subscriber entity
            publisher_entity = await publication.Federation.get_publisher_entity_for_subscriber(
                subscriber_entity_id=subscriber_entity.id,
                subscriber_entity_type=subscriber_entity.entity_type,
                subscriber_domain=self.parent.subscriber_domain,
            )
            
            if publisher_entity and is_recursive:
                # Get ONLY this entity's lineage (not all publication content)
                target_card_lineage = await publisher_entity.Lineage.get(
                    session=session,
                    debug_api=debug_api,
                    return_raw=False,
                    is_recursive=True,
                    max_depth=max_depth,
                    context=context,
                    **context_kwargs,
                )
                print(f"DEBUG target card lineage: {len(target_card_lineage)} items")
        
        # Return subscription → publication → target card lineage
        # This represents the lineage CHAIN, not the federated children in subscriber
        # Federated entities are DOWNSTREAM (created by subscription) and not included here
        self.lineage = [publication_link] + list(target_card_lineage)
        
        # Properties (datasets, cards, pages) filter self.lineage by type automatically
        return list(self.lineage)
