"""Base lineage class and registry for Domo entity lineage handling.

This module contains the core DomoLineage abstract base class and the
registry system for mapping entity types to lineage handlers.
"""

from __future__ import annotations

__all__ = [
    "DomoLineage",
    "FederatedLineageAuthRequiredError",
    "register_lineage_type",
    "get_lineage_type",
    "register_lineage",
    "_LINEAGE_REGISTRY",
    "_LINEAGE_TYPE_REGISTRY",
]

import inspect
import warnings
from abc import ABC
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

import httpx

from ....auth import DomoAuth
from ....base.exceptions import ClassError, DomoError
from ....client.context import RouteContext
from ....routes import datacenter as datacenter_routes
from ....utils import chunk_execution as dmce
from ....utils.logging import get_colored_logger
from .link import (
    DomoLineage_Link,
    DomoLineageLink_Subscription,
    _get_lineage_link_class,
    _map_entity_type,
)

dc_logger = get_colored_logger("DomoLineage")


class FederatedLineageAuthRequiredError(DomoError):
    """Raised when federated lineage is requested without publisher auth."""

    def __init__(
        self,
        *,
        entity_id: str,
        entity_type: str,
        domo_instance: str | None,
        partial_lineage: list[DomoLineage_Link] | None = None,
    ):
        self.partial_lineage = partial_lineage or []
        super().__init__(
            message=(
                "Federated lineage requires parent_auth or parent_auth_retrieval_fn to"
                " retrieve publisher-side dependencies."
            ),
            entity_id=entity_id,
            parent_class=entity_type,
            domo_instance=domo_instance,
        )


# ============================================================================
# Registry and Decorator for Lineage Type Registration
# ============================================================================

# Registry to store lineage type strings mapped by parent class names
_LINEAGE_TYPE_REGISTRY: dict[str, str] = {}


def register_lineage_type(*class_names: str, lineage_type: str):
    """Decorator to register lineage type for entity classes.

    This decorator registers one or more entity class names with their
    corresponding lineage type string (e.g., "DATAFLOW", "DATA_SOURCE", "PAGE").

    Args:
        *class_names: One or more class names that should use this lineage type
        lineage_type: The lineage type string (e.g., "DATAFLOW", "DATA_SOURCE")

    Example:
        @register_lineage_type("DomoDataflow", lineage_type="DATAFLOW")
        @dataclass
        class DomoDataflow(DomoEntity_w_Lineage):
            ...
    """

    def decorator(cls):
        for class_name in class_names:
            _LINEAGE_TYPE_REGISTRY[class_name] = lineage_type
        return cls

    return decorator


def get_lineage_type(class_name: str) -> str:
    """Get the lineage type string for a given class name.

    Args:
        class_name: The class name to look up

    Returns:
        The lineage type string (e.g., "DATAFLOW", "DATA_SOURCE")

    Raises:
        ValueError: If the class name is not registered
    """
    lineage_type = _LINEAGE_TYPE_REGISTRY.get(class_name)
    if lineage_type is None:
        raise ValueError(
            f"No lineage type registered for class '{class_name}'. "
            f"Known classes: {sorted(_LINEAGE_TYPE_REGISTRY.keys())}"
        )
    return lineage_type


# ============================================================================
# Registry and Decorator for Lineage Classes
# ============================================================================

# Registry to store lineage classes mapped by parent class names
_LINEAGE_REGISTRY: dict[str, type[DomoLineage]] = {}


def register_lineage(*parent_class_names: str):
    """Decorator to register a DomoLineage subclass for parent class names.

    Args:
        *parent_class_names: One or more parent class names that should use this lineage class

    Example:
        @register_lineage("DomoPage", "DomoPage_Default", "FederatedDomoPage", "DomoPublishPage")
        @dataclass
        class DomoLineage_Page(DomoLineage):
            ...
    """

    def decorator(cls: type[DomoLineage]) -> type[DomoLineage]:
        for parent_class_name in parent_class_names:
            _LINEAGE_REGISTRY[parent_class_name] = cls
        return cls

    return decorator


@dataclass
class DomoLineage(ABC):
    """Lineage handler for Domo entities.

    The `parent` attribute refers to the entity that this lineage is based off of
    (the entity we're getting lineage for). This matches the `from_parent()` method.

    Note: `parent` is NOT a dependency. Dependencies are what the parent entity
    depends on (upstream entities), and are returned by the `get()` method.
    """

    auth: DomoAuth = field(repr=False)

    parent: Any = field(
        repr=False,
        default=None,
        metadata={
            "description": "The entity this lineage is based off of (not a dependency). "
            "This is the entity we're getting lineage for."
        },
    )

    lineage: list[DomoLineage_Link] = field(repr=False, default_factory=list)
    
    immediate_dependencies: list[DomoLineage_Link] = field(
        repr=False,
        default_factory=list,
        metadata={
            "description": "The direct/first-level dependencies of the parent entity. "
            "Populated by _get_immediate_lineage() - entity-type specific logic."
        }
    )

    Federation: Any = field(default=None, repr=False, init=False)

    _seen_link_keys: set[tuple[str, str]] = field(
        default_factory=set, repr=False, init=False
    )

    _pending_federated_error: FederatedLineageAuthRequiredError | None = field(
        default=None, repr=False, init=False
    )

    _cached_lineage_params: dict[str, Any] | None = field(
        default=None, repr=False, init=False
    )

    @property
    def parent_type(self) -> str:
        """Return the lineage type string for this lineage's parent entity."""
        if not self.parent:
            raise ValueError("Parent must be set to determine lineage type")
        return get_lineage_type(self.parent.__class__.__name__)

    async def _get_immediate_lineage(
        self,
        session: httpx.AsyncClient = None,
        debug_api: bool = False,
        return_raw: bool = False,
        max_depth: int | None = None,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> list[DomoLineage_Link]:
        """Get the entity's immediate (first-level) dependencies.
        
        This is the hook for entity-type specific lineage logic:
        - Dataset: parent dataset or dataflow (via datacenter API)
        - Card: datasets powering the card (via datacenter API)
        - Page: cards on the page (via Layout API)
        - Publication/Subscription: complex content aggregation
        
        Subclasses override this method to customize dependency discovery.
        
        Returns:
            List of immediate dependency links (max_depth=1 concept)
        """
        return await self.get_datacenter_lineage(
            session=session,
            debug_api=debug_api,
            return_raw=return_raw,
            max_depth=max_depth,
            traverse_up=True,
            context=context,
        )

    @classmethod
    async def get_lineage_from_entity(
        cls,
        entity,
        auth: DomoAuth = None,
        check_is_published: bool = False,
        parent_auth_retrieval_fn: Callable | None = None,
        session: httpx.AsyncClient | None = None,
        debug_api: bool = False,
        max_subscriptions_to_check: int | None = None,
    ):
        """Create a DomoLineage instance from an entity.

        Args:
            entity: The entity to create lineage for
            auth: Authentication object (defaults to entity.auth)
            check_is_published: If True, check if entity is published and populate Publish attribute
            parent_auth_retrieval_fn: Function to retrieve parent instance auth for federated entities
            session: HTTP client session
            debug_api: Enable API debug logging
            max_subscriptions_to_check: Limit subscription search scope

        Returns:
            DomoLineage instance with optional Publish attribute populated
        """
        parent_class_name = entity.__class__.__name__
        lineage_class = _LINEAGE_REGISTRY.get(parent_class_name)

        if lineage_class is None:
            raise ValueError(
                f"No lineage class registered for parent type: {parent_class_name}. "
                f"Known types: {sorted(_LINEAGE_REGISTRY.keys())}"
            )

        lineage = lineage_class(
            auth=auth or entity.auth,
            parent=entity,
        )

        if check_is_published:
            await lineage.check_is_published(
                parent_auth_retrieval_fn=parent_auth_retrieval_fn,
                session=session,
                debug_api=debug_api,
                max_subscriptions_to_check=max_subscriptions_to_check,
            )

        return lineage

    @classmethod
    def from_parent(cls, parent, auth: DomoAuth = None):
        """Create a DomoLineage instance from a parent entity synchronously.

        This is a simple factory for synchronous initialization (e.g., __post_init__).
        For async usage with publish checking, use get_lineage_from_entity() instead.
        """
        parent_class_name = parent.__class__.__name__
        lineage_class = _LINEAGE_REGISTRY.get(parent_class_name)

        if lineage_class is None:
            raise ValueError(
                f"No lineage class registered for parent type: {parent_class_name}. "
                f"Known types: {sorted(_LINEAGE_REGISTRY.keys())}"
            )

        return lineage_class(
            auth=auth or parent.auth,
            parent=parent,
        )

    async def get_datacenter_lineage(
        self,
        session: httpx.AsyncClient = None,
        debug_api: bool = False,
        return_raw: bool = False,
        max_depth: int | None = None,
        traverse_up: bool = True,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> list[DomoLineage_Link]:
        """Query the datacenter lineage API."""
        context = RouteContext.build_context(
            context=context,
            session=session,
            debug_api=debug_api,
            **context_kwargs,
        )

        res = await datacenter_routes.get_lineage_upstream(
            auth=self.parent.auth,
            entity_type=self.parent_type,
            entity_id=self.parent.id,
            max_depth=max_depth,
            traverse_up=traverse_up,
            traverse_down=False,
            context=context,
        )

        if return_raw:
            return res

        async def _get_entity_from_dict(obj):
            link_cls = _get_lineage_link_class(obj["type"])
            entity = await link_cls.get_entity(
                entity_id=obj["id"],
                auth=self.auth,
                context=context,
            )
            return link_cls.from_dict(obj=obj, entity=entity)

        dx_classes = await dmce.gather_with_concurrency(
            *[
                _get_entity_from_dict(obj)
                for _, obj in res.response.items()
                if str(obj["id"]) != str(self.parent.id)
            ],
            n=30,
        )

        return list(dx_classes)

    def _filter_lineage(
        self, lineage: list[DomoLineage_Link]
    ) -> list[DomoLineage_Link]:
        """Hook for subclasses to filter/adjust lineage after fetching."""
        return lineage

    def _build_cache_key(
        self,
        *,
        is_recursive: bool,
        parent_auth: DomoAuth | None,
        parent_auth_retrieval_fn: Callable | None,
        max_depth: int | None,
        return_raw: bool,
    ) -> dict[str, Any]:
        """Create a hashable cache key for lineage requests."""

        return {
            "is_recursive": is_recursive,
            "has_parent_auth": bool(parent_auth or parent_auth_retrieval_fn),
            "max_depth": max_depth,
            "return_raw": return_raw,
        }

    async def get_federated_lineage(
        self,
        session: httpx.AsyncClient | None = None,
        debug_api: bool = False,
        return_raw: bool = False,
        parent_auth: DomoAuth | None = None,
        parent_auth_retrieval_fn: Callable | None = None,
        _debug_num_stacks_to_drop: int = 3,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> list[DomoLineage_Link]:
        """Get lineage for a federated entity."""
        if not self.parent and (not self.parent_type):
            raise ValueError(
                "Parent must be set. Use from_parent() to create lineage with a parent."
            )

        federation = getattr(self.parent, "Federation", None)
        await dc_logger.info(
            f"get_federated_lineage: federation={federation}, "
            f"is_published={federation.is_published if federation else 'N/A'}"
        )
        if federation and federation.is_published:
            return await self.get_publish_lineage(
                publish_helper=federation,
                parent_auth=parent_auth,
                parent_auth_retrieval_fn=parent_auth_retrieval_fn,
                context=context,
                **context_kwargs,
            )

        # Ensure federation context exists
        if not self.parent.Federation:
            self.parent.enable_federation_support()

        federation = self.parent.Federation

        # Ensure subscription is resolved
        await federation.ensure_subscription(
            retrieve_parent_auth_fn=parent_auth_retrieval_fn,
            parent_auth=parent_auth,
            entity_type=self.parent.entity_type,
            entity_id=str(self.parent.id),
            session=session,
            debug_api=debug_api,
        )

        # Get parent_auth if not provided
        if parent_auth is None and parent_auth_retrieval_fn is not None:
            # Subscription should be loaded by ensure_subscription above
            if not federation.subscription:
                raise ValueError(
                    "Subscription must be loaded before resolving parent auth."
                )
            auth_or_coro = parent_auth_retrieval_fn(federation.subscription.publisher_domain)
            if inspect.isawaitable(auth_or_coro):
                parent_auth = await auth_or_coro
            else:
                parent_auth = auth_or_coro

        if not parent_auth:
            raise ValueError(
                "Parent auth must be provided to get the federated parent entity."
            )

        # Get publisher entity via FederationContext
        parent_entity = await federation.get_publisher_entity(
            parent_auth=parent_auth,
            context=context,
            **context_kwargs,
        )

        entity_type = getattr(parent_entity, "entity_type", None)
        if not entity_type:
            raise ValueError(
                f"Parent entity {parent_entity.id} does not have entity_type attribute"
            )

        link_type = _map_entity_type(entity_type)
        link_cls = _get_lineage_link_class(link_type)

        parent_lineage_link = link_cls(
            auth=parent_auth,
            id=parent_entity.id,
            entity=parent_entity,
            _type=None,
            dependents=[],
            dependencies=[],
        )

        parent_lineage = await parent_entity.Lineage.get(
            return_raw=return_raw,
            context=context,
            **context_kwargs,
        )

        return [parent_lineage_link] + list(parent_lineage)

    async def get_publish_lineage(
        self,
        *,
        publish_helper=None,
        parent_auth: DomoAuth | None = None,
        parent_auth_retrieval_fn: Callable | None = None,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> list[DomoLineage_Link]:
        """Build lineage chain for published entities.

        Args:
            publish_helper: FederationContext helper (uses self.Federation if not provided)
            parent_auth: Authentication for parent instance
            parent_auth_retrieval_fn: Function to retrieve parent auth
            context: Route context for API calls
            **context_kwargs: Additional context arguments

        Returns:
            List of lineage links including subscription and publisher-side lineage
        """
        # Use provided helper or self.Federation
        helper = publish_helper or self.Federation

        if not helper:
            raise ValueError(
                "No publish helper available. Call check_is_published() first or provide publish_helper parameter."
            )

        subscription = await helper.ensure_subscription(
            retrieve_parent_auth_fn=parent_auth_retrieval_fn,
            parent_auth=parent_auth,
            entity_type=self.parent.entity_type,
            entity_id=str(self.parent.id),
        )

        if not subscription:
            raise DomoError(
                f"Failed to resolve subscription for published entity "
                f"{self.parent.entity_type}:{self.parent.id}"
            )

        # Note: Parent content details are already resolved by ensure_subscription()
        # No need to call a separate method on the parent entity

        subscription_link = DomoLineageLink_Subscription(
            auth=self.parent.auth,
            id=str(subscription.id),
            entity=subscription,
            _type="SUBSCRIPTION",
            dependents=[],
            dependencies=[],
        )

        # Store subscriber entity on subscription for lineage resolution
        subscription.raw['_subscriber_entity'] = self.parent

        subscription_lineage = await subscription.Lineage.get(
            return_raw=False,
            parent_auth=parent_auth,
            parent_auth_retrieval_fn=parent_auth_retrieval_fn,
            is_recursive=True,
            context=context,
            **context_kwargs,
        )

        subscription_link.dependencies = list(subscription_lineage)

        return [subscription_link, *subscription_lineage]

    async def _apply_federated_strategy(
        self,
        return_raw: bool = False,
        parent_auth: DomoAuth = None,
        parent_auth_retrieval_fn: Callable = None,
        max_depth: int = 1,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> list[DomoLineage_Link]:
        """Apply federated lineage strategy for federated entities."""
        is_federated_entity = (
            hasattr(self.parent, "is_federated") and self.parent.is_federated
        )

        if not is_federated_entity:
            return []

        await dc_logger.info(
            f"_apply_federated_strategy: parent_auth={'set' if parent_auth else 'unset'}, "
            f"parent_auth_retrieval_fn={'set' if parent_auth_retrieval_fn else 'unset'}, "
            f"_active_is_recursive={getattr(self, '_active_is_recursive', False)}"
        )

        if parent_auth is not None or parent_auth_retrieval_fn is not None:
            include_publisher_lineage = getattr(self, "_active_is_recursive", False)
            self._pending_federated_error = None
            local_context_kwargs = dict(context_kwargs)
            subscriber_lineage = await self._get_immediate_lineage(
                return_raw=return_raw,
                max_depth=max_depth,
                context=context,
                parent_auth_retrieval_fn=parent_auth_retrieval_fn,
                check_if_published=False,
                **local_context_kwargs,
            )

            if include_publisher_lineage:
                federated_lineage = await self.get_federated_lineage(
                    parent_auth=parent_auth,
                    parent_auth_retrieval_fn=parent_auth_retrieval_fn,
                    context=context,
                    **context_kwargs,
                )
                combined = list(subscriber_lineage) + list(federated_lineage)
                return combined

            return list(subscriber_lineage)

        local_lineage = await self._get_immediate_lineage(
            return_raw=return_raw,
            max_depth=max_depth,
            context=context,
            parent_auth_retrieval_fn=parent_auth_retrieval_fn,
            check_if_published=False,
            **dict(context_kwargs),
        )

        self._pending_federated_error = FederatedLineageAuthRequiredError(
            entity_id=str(getattr(self.parent, "id", "")),
            entity_type=getattr(
                self.parent,
                "entity_type",
                self.parent.__class__.__name__,
            ),
            domo_instance=getattr(
                getattr(self.parent, "auth", None),
                "domo_instance",
                None,
            ),
            partial_lineage=list(local_lineage),
        )

        return local_lineage

    async def check_is_published(
        self,
        *,
        parent_auth_retrieval_fn: Callable[[str], Any | Awaitable[Any]],
        entity_type: str | None = None,
        entity_id: str | None = None,
        session: httpx.AsyncClient | None = None,
        debug_api: bool = False,
        max_subscriptions_to_check: int | None = None,
    ) -> bool:
        """Check if this entity is published and populate Publish attribute.

        Args:
            parent_auth_retrieval_fn: Function to retrieve parent instance auth
            entity_type: Override entity type (defaults to parent.entity_type)
            entity_id: Override entity ID (defaults to parent.id)
            session: HTTP client session
            debug_api: Enable API debug logging
            max_subscriptions_to_check: Limit subscription search scope

        Returns:
            bool: True if entity is published, False otherwise
        """
        from ..federation_context import FederationContext

        if not self.parent:
            raise ValueError(
                "Parent must be set. Use get_lineage_from_entity() to create lineage with a parent."
            )

        # Create or reuse Federation helper
        if self.Federation is None:
            self.Federation = FederationContext(parent=self.parent)

        # Check if already published
        if self.Federation.is_published:
            return True

        # Determine entity type and ID
        content_type = entity_type or self.parent.entity_type
        target_id = entity_id or str(self.parent.id)

        # Perform publish check
        is_published = await self.Federation.check_if_published(
            retrieve_parent_auth_fn=parent_auth_retrieval_fn,
            entity_type=content_type,
            entity_id=target_id,
            session=session,
            debug_api=debug_api,
            max_subscriptions_to_check=max_subscriptions_to_check,
        )

        return is_published

    async def _ensure_immediate_lineage(
        self,
        session: httpx.AsyncClient = None,
        debug_api: bool = False,
        return_raw: bool = False,
        parent_auth: DomoAuth = None,
        parent_auth_retrieval_fn: Callable = None,
        max_depth: int = 1,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> list[DomoLineage_Link]:
        """Ensure immediate lineage is fetched if not already populated."""
        cache_key = self._build_cache_key(
            is_recursive=getattr(self, "_active_is_recursive", False),
            parent_auth=parent_auth,
            parent_auth_retrieval_fn=parent_auth_retrieval_fn,
            max_depth=max_depth,
            return_raw=return_raw,
        )

        if self.lineage and self._cached_lineage_params == cache_key:
            await dc_logger.info(
                f"_ensure_immediate_lineage: returning cached lineage (len={len(self.lineage)})"
            )
            return list(self.lineage)

        is_federated_entity = (
            hasattr(self.parent, "is_federated") and self.parent.is_federated
        )

        await dc_logger.info(
            f"_ensure_immediate_lineage: parent={self.parent.id if self.parent else 'None'}, "
            f"is_federated={is_federated_entity}, "
            f"parent_auth={'set' if parent_auth else 'unset'}, "
            f"parent_auth_retrieval_fn={'set' if parent_auth_retrieval_fn else 'unset'}"
        )

        if is_federated_entity:
            lineage = await self._apply_federated_strategy(
                session=session,
                debug_api=debug_api,
                return_raw=return_raw,
                parent_auth=parent_auth,
                parent_auth_retrieval_fn=parent_auth_retrieval_fn,
                max_depth=max_depth,
                context=context,
                **context_kwargs,
            )
        else:
            lineage = await self._get_immediate_lineage(
                return_raw=return_raw,
                max_depth=max_depth,
                context=context,
                parent_auth=parent_auth,
                parent_auth_retrieval_fn=parent_auth_retrieval_fn,
                **context_kwargs,
            )

        self._cached_lineage_params = cache_key
        return lineage

    async def check_is_federated(
        self,
        *,
        check_is_published: bool = False,
        parent_auth_retrieval_fn: Callable[[str], Any | Awaitable[Any]] | None = None,
        session: httpx.AsyncClient | None = None,
        debug_api: bool = False,
        max_subscriptions_to_check: int | None = None,
    ) -> bool:
        """Check if this entity is federated, optionally check if published.

        Args:
            check_is_published: If True, also check publish state and populate Publish attribute
            parent_auth_retrieval_fn: Function to retrieve parent instance auth (required if check_is_published=True)
            session: HTTP client session
            debug_api: Enable API debug logging
            max_subscriptions_to_check: Limit subscription search scope

        Returns:
            bool: True if entity is federated, False otherwise
        """
        if not self.parent:
            raise ValueError(
                "Parent must be set. Use get_lineage_from_entity() to create lineage with a parent."
            )

        # Check federation state
        is_federated_entity = (
            hasattr(self.parent, "is_federated") and self.parent.is_federated
        )

        # Optionally check publish state
        if check_is_published and is_federated_entity:
            if not parent_auth_retrieval_fn:
                raise ValueError(
                    "parent_auth_retrieval_fn is required when check_is_published=True"
                )

            await self.check_is_published(
                parent_auth_retrieval_fn=parent_auth_retrieval_fn,
                session=session,
                debug_api=debug_api,
                max_subscriptions_to_check=max_subscriptions_to_check,
            )

        return is_federated_entity

    @property
    def is_published(self) -> bool:
        """Check if entity has been identified as published.

        Returns:
            bool: True if Federation attribute exists and indicates published state
        """
        return self.Federation is not None and self.Federation.is_published

    async def get(
        self,
        session: httpx.AsyncClient = None,
        debug_api: bool = False,
        return_raw: bool = False,
        return_graph: bool = False,
        parent_auth: DomoAuth = None,
        parent_auth_retrieval_fn: Callable = None,
        is_recursive: bool = False,
        max_depth: int | None = None,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> list[DomoLineage_Link] | Any:  # Returns LineageGraph when return_graph=True
        """Get lineage for this entity.

        Args:
            session: HTTP session for reuse
            debug_api: Enable API debug logging
            return_raw: Return raw response
            return_graph: Return LineageGraph instead of list of links
            parent_auth: Authentication for publisher instance
            parent_auth_retrieval_fn: Callable to retrieve publisher auth by domain
            is_recursive: Enable recursive lineage traversal
            max_depth: Maximum lineage depth (forced to 1 when is_recursive=True)
            context: Route context for API configuration
            **context_kwargs: Additional context parameters

        Returns:
            List of lineage links (default) or LineageGraph (if return_graph=True)

        Raises:
            ClassError: If parent is not set
            FederatedLineageAuthRequiredError: When federated entity requires auth (gracefully degraded to warning)
        """
        if not self.parent:
            raise ClassError(
                message="Parent must be set. Use from_parent() to create lineage with a parent.",
                cls_instance=self,
            )

        previous_recursive_flag = getattr(self, "_active_is_recursive", False)
        self._active_is_recursive = is_recursive

        self._seen_link_keys.clear()
        self._pending_federated_error = None

        try:
            entity_key = (str(self.parent.id), str(self.parent.entity_type))
            self._seen_link_keys.add(entity_key)

            if is_recursive:
                if max_depth is not None and max_depth != 1:
                    warnings.warn(
                        f"When is_recursive=True, max_depth must be 1. Setting max_depth=1 (was {max_depth}).",
                        UserWarning,
                    )
                max_depth = 1
            elif max_depth is None:
                max_depth = 1

            pending_error: FederatedLineageAuthRequiredError | None = None
            try:
                lineage = await self._ensure_immediate_lineage(
                    parent_auth=parent_auth,
                    parent_auth_retrieval_fn=parent_auth_retrieval_fn,
                    max_depth=max_depth,
                    context=context,
                    **context_kwargs,
                )
            except FederatedLineageAuthRequiredError as exc:
                lineage = list(exc.partial_lineage)
                pending_error = exc
            # Let unexpected exceptions propagate; avoid catching bare Exception

            lineage = self._filter_lineage(lineage)
            
            # Store immediate dependencies before recursive traversal
            self.immediate_dependencies = list(lineage)

            result = await self._traverse_lineage(
                lineage=lineage,
                is_recursive=is_recursive,
                max_depth=max_depth,
                context=context,
                parent_auth=parent_auth,
                parent_auth_retrieval_fn=parent_auth_retrieval_fn,
                **context_kwargs,
            )

            self.lineage = result
            self._cached_lineage_params = self._build_cache_key(
                is_recursive=is_recursive,
                parent_auth=parent_auth,
                parent_auth_retrieval_fn=parent_auth_retrieval_fn,
                max_depth=max_depth,
                return_raw=return_raw,
            )

            error_to_raise = pending_error or self._pending_federated_error
            if error_to_raise:
                # Gracefully degrade - warn and return partial lineage instead of raising
                await dc_logger.warning(
                    f"Federated entity {self.parent.id} may be published. "
                    "Pass parent_auth or parent_auth_retrieval_fn to retrieve publisher-side lineage."
                )
                self._pending_federated_error = None

            # Build and return graph if requested (synchronous operation)
            if return_graph:
                from .graph import LineageGraph

                # Pre-load publication content lineage for graph building
                # Graph building is synchronous, so we must load data beforehand
                if hasattr(self.parent, "Federation") and self.parent.Federation:
                    subscription = self.parent.Federation.subscription
                    if subscription:
                        publication = getattr(subscription, "parent_publication", None)
                        if publication and hasattr(publication, "content"):
                            # Load lineage for each page in publication content
                            for content_item in publication.content:
                                if (hasattr(content_item, "entity") 
                                    and content_item.entity
                                    and content_item.entity.__class__.__name__ == "DomoPage"):
                                    # Ensure page lineage is loaded (includes cards)
                                    if hasattr(content_item.entity, "Lineage") and content_item.entity.Lineage:
                                        # Only load if not already cached
                                        if not content_item.entity.Lineage.lineage:
                                            await content_item.entity.Lineage.get(
                                                session=session,
                                                debug_api=debug_api,
                                                context=context,
                                                **context_kwargs,
                                            )

                graph = LineageGraph.from_lineage_links(
                    links=result,
                    root_entity=self.parent,
                )
                return graph

            return result
        finally:
            self._active_is_recursive = previous_recursive_flag

    async def expand_lineage_links(
        self,
        lineage_links: list[DomoLineage_Link] | None,
        *,
        recursive: bool = True,
        include_card_datasets: bool = True,
        parent_auth: DomoAuth | None = None,
        parent_auth_retrieval_fn: Callable | None = None,
    ) -> tuple[list[DomoLineage_Link], list[tuple[Any, Any]]]:
        """Expand lineage links and optionally collect card->dataset relationships."""
        if not recursive or not lineage_links:
            return [], []

        expansion_kwargs: dict[str, Any] = {}
        if parent_auth is not None:
            expansion_kwargs["parent_auth"] = parent_auth
        if parent_auth_retrieval_fn is not None:
            expansion_kwargs["parent_auth_retrieval_fn"] = parent_auth_retrieval_fn

        expanded: list[DomoLineage_Link] = []
        dataset_relationships: list[tuple[Any, Any]] = []

        for link in lineage_links:
            entity = getattr(link, "entity", None)
            if not entity:
                continue

            if getattr(entity, "Lineage", None):
                try:
                    entity_lineage = await entity.Lineage.get(
                        is_recursive=True,
                        **expansion_kwargs,
                    )
                except FederatedLineageAuthRequiredError as exc:
                    entity_lineage = list(exc.partial_lineage)
                except DomoError as exc:
                    warnings.warn(
                        f"Unable to expand lineage for entity {getattr(entity, 'id', 'unknown')}: {exc}",
                        UserWarning,
                    )
                    entity_lineage = []

                if entity_lineage:
                    expanded.extend(entity_lineage)

            if include_card_datasets:
                datasets_manager = getattr(entity, "Datasets", None)
                if datasets_manager:
                    dataset_kwargs: dict[str, Any] = {}
                    if parent_auth_retrieval_fn is not None:
                        dataset_kwargs["parent_auth_retrieval_fn"] = (
                            parent_auth_retrieval_fn
                        )
                    try:
                        datasets = await datasets_manager.get(**dataset_kwargs)
                    except DomoError as exc:
                        warnings.warn(
                            f"Unable to retrieve datasets for entity {getattr(entity, 'id', 'unknown')}: {exc}",
                            UserWarning,
                        )
                        datasets = []

                    for dataset in datasets or []:
                        dataset_relationships.append((entity, dataset))

        return expanded, dataset_relationships

    async def _traverse_lineage(
        self,
        lineage: list[DomoLineage_Link],
        is_recursive: bool,
        max_depth: int | None,
        session: httpx.AsyncClient = None,
        debug_api: bool = False,
        return_raw: bool = False,
        *,
        context: RouteContext | None = None,
        parent_auth: DomoAuth | None = None,
        parent_auth_retrieval_fn: Callable | None = None,
        **context_kwargs,
    ) -> list[DomoLineage_Link]:
        """Traverse lineage recursively/iteratively."""
        if not is_recursive:
            return lineage

        for link in lineage:
            if link and hasattr(link, "entity") and link.entity:
                link_key = (str(link.entity.id), str(link.entity.entity_type))
                if link_key not in self._seen_link_keys:
                    self._seen_link_keys.add(link_key)

        all_lineage = list(lineage)
        i = 0

        while i < len(all_lineage):
            link = all_lineage[i]
            i += 1

            if not link or not hasattr(link, "entity") or not link.entity:
                continue
            
            # Skip SUBSCRIPTION links - their dependencies should not be recursively expanded
            # The subscription's lineage already includes the publication + its content
            if link.type == "SUBSCRIPTION":
                continue

            link_key = (str(link.entity.id), str(link.entity.entity_type))

            if link_key in self._seen_link_keys:
                continue

            self._seen_link_keys.add(link_key)

            child_lineage = await link.entity.Lineage.get(
                return_raw=return_raw,
                is_recursive=False,
                max_depth=1,
                context=context,
                parent_auth=parent_auth,
                parent_auth_retrieval_fn=parent_auth_retrieval_fn,
                **context_kwargs,
            )

            discovered_dependencies = []
            for child_link in child_lineage:
                if (
                    not child_link
                    or not hasattr(child_link, "entity")
                    or not child_link.entity
                ):
                    continue

                child_link_key = (
                    str(child_link.entity.id),
                    str(child_link.entity.entity_type),
                )
                discovered_dependencies.append(child_link)

                if child_link_key not in self._seen_link_keys:
                    self._seen_link_keys.add(child_link_key)
                    all_lineage.append(child_link)

            if discovered_dependencies:
                link.dependencies.extend(discovered_dependencies)

        return all_lineage
