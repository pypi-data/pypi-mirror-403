"""FederationContext - composition helper for entity publish/subscribe state.

This module provides the FederationContext class that handles publish and subscription
state for Domo entities. Separated from base.entities to avoid circular imports with
DomoEverywhere classes.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import httpx

from ...auth.base import DomoAuth
from ...client.context import RouteContext
from ...utils.logging import get_colored_logger

if TYPE_CHECKING:
    from ...base.entities import DomoEntity_w_Lineage
    from ..DomoEverywhere.core import DomoPublication, DomoSubscription

logger = get_colored_logger()


@dataclass
class FederationContext:
    """Holds resolved federation state for federated entities.

    Attached to subscriber-side entities that are copies from another instance.
    Manages subscription/publication discovery and caching.

    Can be attached to a parent entity via constructor, or created standalone
    using from_entity_id() for probing publish state without a full entity.
    """

    parent: DomoEntity_w_Lineage | None = field(repr=False, default=None)
    subscription: DomoSubscription | None = field(repr=False, default=None)
    parent_publication: DomoPublication | None = field(repr=False, default=None)
    publisher_entity: DomoEntity_w_Lineage | None = field(repr=False, default=None)

    _parent_auth_fn: Callable[[str], DomoAuth | Awaitable[DomoAuth]] | None = field(
        repr=False, default=None
    )
    _parent_auth: DomoAuth | None = field(repr=False, default=None)
    _content_type: str | None = field(repr=False, default=None)
    _entity_id: str | None = field(repr=False, default=None)
    _auth: DomoAuth | None = field(repr=False, default=None)

    @property
    def auth(self) -> DomoAuth:
        """Get auth from parent entity or standalone _auth."""
        if self._auth is not None:
            return self._auth
        if self.parent is not None:
            return self.parent.auth
        raise ValueError("No auth available - neither parent nor _auth is set")

    @property
    def entity_id(self) -> str:
        """Get entity ID from stored value or parent."""
        if self._entity_id is not None:
            return self._entity_id
        if self.parent is not None:
            return str(self.parent.id)
        raise ValueError(
            "No entity_id available - neither _entity_id nor parent is set"
        )

    @classmethod
    def from_entity_id(
        cls,
        *,
        auth: DomoAuth,
        entity_id: str,
        entity_type: str,
    ) -> FederationContext:
        """Create a federation context from entity identifiers (no parent entity required).

        Use this factory when you need to check publish state without constructing
        a full entity object.

        Args:
            auth: Authentication for the subscriber instance
            entity_id: The entity identifier to check
            entity_type: The entity type (DATA_SOURCE, CARD, PAGE, etc.)

        Returns:
            FederationContext instance ready for publish state checks
        """
        return cls(
            parent=None,
            _auth=auth,
            _entity_id=str(entity_id),
            _content_type=entity_type,
        )

    def hydrate_from_existing(
        self,
        *,
        subscription: DomoSubscription,
        parent_auth_retrieval_fn: (
            Callable[[str], DomoAuth | Awaitable[DomoAuth]] | None
        ) = None,
        parent_auth: DomoAuth | None = None,
        content_type: str,
        entity_id: str,
    ):
        """Attach an already-discovered subscription to this helper.

        Args:
            subscription: The subscription object
            parent_auth_retrieval_fn: Callable to retrieve parent auth by domain
            parent_auth: Pre-existing parent auth (alternative to retrieval function)
            content_type: Entity type (DATA_SOURCE, CARD, PAGE, etc.)
            entity_id: The entity identifier
        """
        self.subscription = subscription
        self._parent_auth_fn = parent_auth_retrieval_fn
        self._parent_auth = parent_auth
        self._content_type = content_type
        self._entity_id = entity_id

    @property
    def is_published(self) -> bool:
        return self.subscription is not None

    async def check_if_published(
        self,
        *,
        retrieve_parent_auth_fn: Callable[[str], DomoAuth | Awaitable[DomoAuth]],
        entity_type: str,
        entity_id: str | None = None,
        context: RouteContext | None = None,
        session: httpx.AsyncClient | None = None,
        debug_api: bool = False,
        max_subscriptions_to_check: int | None = None,
        **context_kwargs,
    ) -> bool:
        """Discover whether the entity participates in a subscription."""
        from ...base.publish_resolver import PublishResolver

        if not retrieve_parent_auth_fn:
            raise ValueError(
                "retrieve_parent_auth_fn is required to resolve published entities."
            )

        # Build context from provided parameters
        context = RouteContext.build_context(
            context=context,
            session=session,
            debug_api=debug_api,
            **context_kwargs,
        )

        self._parent_auth_fn = retrieve_parent_auth_fn
        self._content_type = entity_type
        if entity_id:
            self._entity_id = entity_id

        target_id = self.entity_id

        await logger.debug(
            f"Checking if {entity_type} {target_id} is published",
            extra={
                "entity_type": entity_type,
                "entity_id": target_id,
                "subscriber_instance": self.auth.domo_instance,
            },
        )

        resolver = PublishResolver(
            subscriber_auth=self.auth,
            parent_auth_retrieval_fn=retrieve_parent_auth_fn,
            session=context.session,
            debug_api=context.debug_api,
            max_subscriptions_to_check=max_subscriptions_to_check,
        )

        try:
            # PublishResolver returns raw dict - hydrate into DomoSubscription
            from ..DomoEverywhere.core import DomoSubscription

            subscription_data = await resolver.get_subscription_for_entity(
                entity_type=entity_type,
                subscriber_entity_id=target_id,
            )

            self.subscription = DomoSubscription.from_dict(
                auth=self.auth,
                parent_publication=None,
                obj=subscription_data,
            )
            await logger.info(
                f"✅ {entity_type} {target_id} is published",
                extra={
                    "entity_type": entity_type,
                    "entity_id": target_id,
                    "subscription_id": (
                        self.subscription.id if self.subscription else None
                    ),
                },
            )
        except ValueError as exc:
            await logger.debug(
                f"❌ {entity_type} {target_id} is not published: {exc}",
                extra={
                    "entity_type": entity_type,
                    "entity_id": target_id,
                    "error": str(exc),
                },
            )
            self.subscription = None

        return self.is_published

    async def ensure_subscription(
        self,
        *,
        retrieve_parent_auth_fn: (
            Callable[[str], DomoAuth | Awaitable[DomoAuth]] | None
        ) = None,
        parent_auth: DomoAuth | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        session: httpx.AsyncClient | None = None,
        debug_api: bool = False,
        max_subscriptions_to_check: int | None = None,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> DomoSubscription | None:
        """Ensure subscription data is loaded, running discovery if needed.

        Args:
            retrieve_parent_auth_fn: Callable to retrieve parent auth by domain
            parent_auth: Pre-existing parent auth (alternative to retrieval function)
            entity_type: Entity type (DATA_SOURCE, CARD, PAGE, etc.)
            entity_id: The entity identifier
            session: HTTP session for API calls
            debug_api: Enable debug logging
            max_subscriptions_to_check: Limit subscription search

        Returns:
            The subscription object if found

        Raises:
            ValueError: If no auth method available
        """

        context = RouteContext.build_context(
            context=context,
            session=session,
            debug_api=debug_api,
            **context_kwargs,
        )

        if self.subscription:
            return self.subscription

        # Store parent_auth if provided
        if parent_auth:
            self._parent_auth = parent_auth

        fn = retrieve_parent_auth_fn or self._parent_auth_fn
        # Allow proceeding if we have either a retrieval function OR direct parent_auth
        if not fn and not self._parent_auth:
            raise ValueError(
                "retrieve_parent_auth_fn or parent_auth must be provided to resolve subscriptions."
            )

        # Determine content type - try stored, then parent if available
        content_type = entity_type or self._content_type
        if not content_type and self.parent is not None:
            content_type = self.parent.entity_type

        if not content_type:
            raise ValueError("entity_type must be provided or set via _content_type")

        # Use entity_id property which handles both standalone and parent modes
        target_id = entity_id or self.entity_id

        # If we have parent_auth but no fn, create a simple lambda that returns the auth
        effective_fn = fn
        if not effective_fn and self._parent_auth:
            effective_fn = lambda _domain: self._parent_auth  # noqa: E731

        await self.check_if_published(
            retrieve_parent_auth_fn=effective_fn,
            entity_type=content_type,
            entity_id=target_id,
            context=context,
            session=session,
            debug_api=debug_api,
            max_subscriptions_to_check=max_subscriptions_to_check,
        )
        return self.subscription

    async def _resolve_parent_auth(
        self,
        parent_auth: DomoAuth | None = None,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> DomoAuth:
        """Resolve parent authentication using provided auth, stored auth, or retrieval function.

        Priority order:
        1. Explicitly provided parent_auth parameter
        2. Stored _parent_auth from hydration
        3. Call _parent_auth_fn to retrieve auth dynamically

        Args:
            parent_auth: Optional explicit parent auth to use

        Returns:
            DomoAuth for the publisher instance

        Raises:
            ValueError: If no auth available and no retrieval function configured
        """
        context = RouteContext.build_context(
            context=context,
            **context_kwargs,
        )

        if parent_auth:
            return parent_auth
        if self._parent_auth:
            return self._parent_auth
        if not self.subscription:
            raise ValueError("Subscription must be resolved before fetching auth.")
        if not self._parent_auth_fn:
            raise ValueError(
                "No parent auth retrieval function available for published entity. "
                "Provide parent_auth or parent_auth_retrieval_fn."
            )
        auth = self._parent_auth_fn(self.subscription.publisher_domain, context=context)
        if isinstance(auth, Awaitable):
            return await auth
        return auth

    async def get_publisher_auth(
        self,
        parent_auth: Any = None,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> DomoAuth:
        """Public helper to resolve publisher authentication."""

        context = RouteContext.build_context(
            context=context,
            **context_kwargs,
        )
        return await self._resolve_parent_auth(parent_auth, context=context)

    async def get_parent_publication(
        self,
        *,
        parent_auth: DomoAuth | None = None,
        is_fetch_content_details: bool = True,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> DomoPublication:
        """Fetch and cache the parent publication for this entity.
        
        Args:
            parent_auth: Pre-existing publisher auth
            is_fetch_content_details: If True, automatically call get_content_details()
                on the publication before returning. This ensures content mapping is
                available for indirect resolution. Default: True.
            context: Route context
            **context_kwargs: Additional context args
            
        Returns:
            DomoPublication with content details loaded (if is_fetch_content_details=True)
        """
        context = RouteContext.build_context(
            context=context,
            **context_kwargs,
        )

        from ..DomoEverywhere.core import DomoPublication

        if not self.subscription:
            raise ValueError(
                "Subscription must be loaded before fetching parent publication."
            )

        publisher_auth = await self._resolve_parent_auth(parent_auth, context=context)

        if not self.parent_publication:
            self.parent_publication = await DomoPublication.get_by_id(
                publication_id=self.subscription.publication_id,
                auth=publisher_auth,
                context=context,
            )

        # Automatically fetch content details if requested
        if is_fetch_content_details and self.parent_publication:
            await self.parent_publication.get_content_details(
                subscriber_domain=self.auth.domo_instance,
                context=context,
            )

        return self.parent_publication

    async def get_publisher_entity(
        self,
        *,
        parent_auth: DomoAuth | None = None,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> DomoEntity_w_Lineage:
        context = RouteContext.build_context(
            context=context,
            **context_kwargs,
        )

        """Fetch and cache the publisher-side entity."""
        if not self.subscription:
            raise ValueError(
                "Subscription must be loaded before resolving publisher entity."
            )

        if self.parent is None:
            raise ValueError(
                "Cannot resolve publisher entity in standalone mode - "
                "attach to a parent entity first."
            )

        # Check cache first
        cache_key = f"{self.parent.entity_type}:{self.parent.id}"
        cache = self.parent.raw.setdefault('_indirect_resolution_cache', {})
        
        if cache_key in cache:
            return cache[cache_key]

        publication = await self.get_parent_publication(
            parent_auth=parent_auth, context=context
        )

        self.publisher_entity = (
            await publication.get_publisher_entity_for_subscriber(
                subscriber_entity=self.parent,
                subscriber_domain=self.auth.domo_instance,
                include_indirect=True,
                context=context,
                **context_kwargs,
            )
        )
        
        # Cache the result
        if self.publisher_entity:
            cache[cache_key] = self.publisher_entity
        
        return self.publisher_entity
