from __future__ import annotations

"""Base entity classes for Domo objects with inheritance hierarchy and lineage support.

This module provides the foundational classes for all Domo entities including datasets,
cards, pages, users, and groups. It implements a hierarchical structure with support
for entity relationships, lineage tracking, and federation.

Classes:
    DomoEntity: Base entity with core functionality
    DomoEntity_w_Lineage: Entity with lineage tracking capabilities
    DomoManager: Base class for entity managers
    DomoSubEntity: Entity that belongs to a parent entity
"""

import abc
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import httpx

from ..auth.base import DomoAuth
from ..client.context import RouteContext
from ..utils.logging import get_colored_logger, log_call
from .base import DomoBase, DomoEnumMixin
from .exceptions import DomoError
from .relationships import DomoRelationshipController

logger = get_colored_logger()


class Access(DomoEnumMixin):
    """abc for the concept of managing access levels to Domo entities."""


@dataclass
class DomoEntity(DomoBase):
    """Base class for all Domo entities (datasets, cards, pages, users, etc.).

    Provides core functionality including authentication, unique identification,
    data conversion utilities, and relationship management. All concrete entity
    types should inherit from this class or one of its subclasses.

    Attributes:
        auth: Authentication object for API requests (hidden in repr)
        id: Unique identifier for the entity
        raw: Raw API response data for the entity (hidden in repr)
        Relations: Relationship controller for managing entity relationships

    Example:
        >>> entity = SomeDomoEntity(auth=auth, id="123", raw={})
        >>> entity.display_url()  # Implemented by subclass
        'https://mycompany.domo.com/...'
    """

    auth: DomoAuth = field(repr=False)
    id: str
    raw: dict = field(repr=False)  # api representation of the class

    Relations: DomoRelationshipController = field(repr=False, init=False, default=None)

    @property
    def _name(self) -> str:
        name = getattr(self, "name", None)

        if not name:
            raise NotImplementedError(
                "This property should be implemented by subclasses."
            )
        return name

    @property
    def entity_name(self) -> str:
        """Get the display name for this entity.

        Tries common name fields in order: name, title, display_name.
        Falls back to entity ID if no name is found.

        Subclasses can override this property to use entity-specific name fields.

        Returns:
            Display name for the entity, or entity ID as fallback
        """
        # Try common name fields in order of preference
        name = (
            getattr(self, "name", None)
            or getattr(self, "title", None)
            or getattr(self, "display_name", None)
        )
        return str(name) if name else self.id

    def __eq__(self, other) -> bool:
        """Check equality based on entity ID.

        Args:
            other: Object to compare with

        Returns:
            bool: True if both are DomoEntity instances with the same ID
        """
        if isinstance(other, DomoEntity):
            return self.id == other.id

        return False

    def __hash__(self) -> int:
        """Return hash based on entity ID.

        This allows entities to be used in sets and as dictionary keys.
        Two entities with the same ID will have the same hash.

        Returns:
            int: Hash of the entity ID
        """
        return hash(self.id)

    def to_dict(
        self, override_fn: Callable | None = None, return_snake_case: bool = False
    ) -> dict:
        """Convert all dataclass attributes to a dictionary in camelCase or snake_case.

        This method is useful for serializing entity data for API requests
        or data export operations.

        Only fields with repr=True are included, plus any properties listed in
        __serialize_properties__.

        Args:
            override_fn (Callable | None): Custom conversion function to override default behavior
            return_snake_case (bool): If True, return keys in snake_case. If False (default), return camelCase.

        Returns:
            dict: Dictionary with camelCase (default) or snake_case keys and corresponding attribute values

        Example:
            >>> entity.to_dict()
            {'id': '123', 'displayName': 'My Entity', 'displayUrl': '...', ...}
            >>> entity.to_dict(return_snake_case=True)
            {'id': '123', 'display_name': 'My Entity', 'display_url': '...', ...}
        """

        # Use parent's implementation which handles repr filtering and __serialize_properties__
        return super().to_dict(
            override_fn=override_fn, return_snake_case=return_snake_case
        )

    @property
    @abc.abstractmethod
    def entity_type(self) -> str:
        """Get the EntityType for this entity based on its class name.

        Must be implemented by subclasses to return the appropriate entity type.

        Returns:
            str: The entity type identifier (e.g., 'DATA_SOURCE', 'CARD', 'PAGE')
        """
        ...

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, auth: DomoAuth, obj: dict[str, Any]):
        """Create an entity instance from a dictionary representation.

        This method should be implemented by subclasses to handle the conversion
        from API response dictionaries to entity objects.

        Args:
            auth: Authentication object for API requests
            obj: Dictionary representation of the entity from the API

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    @classmethod
    @abc.abstractmethod
    async def get_by_id(
        cls,
        auth: DomoAuth,
        id: str,
        debug_num_stacks_to_drop=2,
        debug_api: bool = False,
        session: httpx.AsyncClient | None = None,
    ):
        """Fetch an entity by its unique identifier.

        This method should be implemented by subclasses to handle entity-specific
        retrieval logic from the Domo API.

        Args:
            auth (DomoAuth): Authentication object for API requests
            entity_id (str): Unique identifier of the entity to retrieve

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    @log_call(level_name="class", log_level="DEBUG", color="cyan")
    async def refresh(
        self,
        debug_num_stacks_to_drop=2,
        debug_api: bool = False,
        session: httpx.AsyncClient | None = None,
        **kwargs,
    ):
        """Refresh this instance from the API using its id and auth."""

        try:
            await logger.info(
                f"Refreshing {self.__class__.__name__} - {self.id} in {self.auth.domo_instance}..."
            )
            result = await type(self).get_entity_by_id(
                auth=self.auth,
                entity_id=self.id,
                debug_num_stacks_to_drop=debug_num_stacks_to_drop,
                debug_api=debug_api,
                session=session,
                **kwargs,
            )
        except DomoError as e:
            await logger.error(
                f"Failed to refresh {self.__class__.__name__} - {self.id} in {self.auth.domo_instance}: {e}"
            )
            raise

        # Spread attributes from result to self
        if isinstance(result, type(self)):
            self.__dict__.update(
                {k: v for k, v in result.__dict__.items() if v is not None}
            )
        return self

    @classmethod
    @abc.abstractmethod
    async def get_entity_by_id(
        cls,
        auth: DomoAuth,
        entity_id: str,
        debug_num_stacks_to_drop: int = 2,
        debug_api: bool = False,
        session: httpx.AsyncClient | None = None,
        **kwargs,
    ):
        """Fetch an entity by its ID

        This method should be implemented by subclasses to fetch the specific
        entity type while ensuring lineage tracking is properly initialized.

        Args:
            auth (DomoAuth): Authentication object for API requests
            entity_id (str): Unique identifier of the entity to retrieve
            debug_num_stacks_to_drop (int): Number of stack frames to drop for debug logging (default: 2)
            debug_api (bool): Enable API debug logging (default: False)
            session (httpx.AsyncClient | None): Optional HTTP client session
            **kwargs: Additional arguments passed to the underlying get_by_id method

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    @property
    @abc.abstractmethod
    def display_url(self) -> str:
        """Generate the URL to display this entity in the Domo interface.

        This method should return the direct URL to view the entity in Domo's
        web interface, allowing users to navigate directly to the entity.

        Returns:
            str: Complete URL to view the entity in Domo

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("This method should be implemented by subclasses.")


@dataclass
class DomoEntity_w_Lineage(DomoEntity):
    """Entity with lineage tracking capabilities.

    Extends DomoEntity to include lineage tracking functionality,
    enabling entities to track their relationships and dependencies
    within the Domo ecosystem.

    Attributes:
        Lineage: Lineage tracking object for dependency management (hidden in repr)
        Federation: Federation context for publish/subscribe state (hidden in repr)
        __skip_lineage_registration__: Class attribute to opt out of registration requirement.
            Set to True for abstract or intermediate base classes that should not be registered.
    """

    Lineage: Any | None = field(repr=False, init=False, default=None)
    Federation: Any | None = field(
        repr=False, init=False, default=None
    )  # DomoFederationContext

    @property
    def name(self) -> str:
        """Get the display name for this entity.
        
        All entities with lineage provide a name property for consistent
        identification in lineage diagrams and reports.
        
        Entities that use 'title' (DomoCard, DomoPage) should override this as:
            @property
            def name(self) -> str:
                return self.title or f"Untitled {self.entity_type}"
        
        Entities with a 'name' attribute (DomoDataset, DomoDataflow, DomoPublication)
        will use their dataclass field directly.
        
        Returns:
            Display name for the entity
            
        Raises:
            AttributeError: If entity doesn't have name, title, or override this property
        """
        # Check if there's a dataclass field named 'name'
        if hasattr(self, '__dataclass_fields__') and 'name' in self.__dataclass_fields__:
            # Access the actual field value through __dict__ to avoid infinite recursion
            return self.__dict__.get('name', f"Unnamed {self.entity_type}")
        
        # Check for 'title' attribute (common in Card and Page entities)
        if hasattr(self, 'title'):
            title = getattr(self, 'title', None)
            if title:
                return title
        
        # Fallback
        raise AttributeError(
            f"{self.__class__.__name__} must either have a 'name' dataclass field, "
            f"a 'title' attribute, or override the 'name' property"
        )

    def __post_init__(self):
        """Initialize lineage tracking after entity creation."""
        from ..classes.subentity.lineage import DomoLineage, get_lineage_type

        # Check if class is registered with lineage type registry (unless opted out)
        if not getattr(self.__class__, "__skip_lineage_registration__", False):
            try:
                get_lineage_type(self.__class__.__name__)
            except ValueError as e:
                # Enhance the error message with registration instructions
                original_msg = str(e)
                raise ValueError(
                    f"Class '{self.__class__.__name__}' must be registered with @register_lineage_type decorator. "
                    f"Add @register_lineage_type('{self.__class__.__name__}', lineage_type='<TYPE>') above the class definition. "
                    f"If this is an abstract base class, set __skip_lineage_registration__ = True to opt out. "
                    f"\nOriginal error: {original_msg}"
                ) from e

        # Using protected method until public interface is available
        self.Lineage = DomoLineage.from_parent(auth=self.auth, parent=self)

    def enable_federation_support(self):
        """Ensure this entity has an attached FederationContext helper.
        returns FederationContext instance.
        """
        if self.Federation is None:
            from ..classes.subentity.federation_context import FederationContext

            self.Federation = FederationContext(parent=self)
        return self.Federation

    @classmethod
    async def probe_is_published(
        cls,
        entity_id: str,
        subscriber_auth: DomoAuth,
        parent_auth: DomoAuth | None = None,
        parent_auth_retrieval_fn: Callable | None = None,
        session: httpx.AsyncClient | None = None,
        debug_api: bool = False,
        max_subscriptions_to_check: int | None = None,
        context: RouteContext | None = None,
    ):
        """Check if entity is published (federated) - works for all entity types.

        Uses lineage type registry to determine entity type automatically.

        Args:
            entity_id: Entity identifier to check
            subscriber_auth: Auth for subscriber instance
            parent_auth: Optional pre-existing publisher auth
            parent_auth_retrieval_fn: Callable to retrieve publisher auth
            session: Optional HTTP session for reuse
            debug_api: Enable debug logging
            max_subscriptions_to_check: Limit subscription checking
            context: Optional pre-built context

        Returns:
            FederationContext with subscription info if published

        Raises:
            ValueError: If class not registered with lineage type or missing auth
        """
        from ..classes.subentity.lineage import get_lineage_type
        from ..classes.subentity.federation_context import FederationContext

        # Dynamically determine entity type from lineage registry
        try:
            entity_type = get_lineage_type(cls.__name__)
        except ValueError as e:
            raise ValueError(
                f"Cannot determine entity type for {cls.__name__}. "
                f"Ensure class is registered with @register_lineage_type decorator."
            ) from e

        context = RouteContext.build_context(
            context=context, session=session, debug_api=debug_api
        )

        if not parent_auth_retrieval_fn and not parent_auth:
            raise ValueError(
                f"parent_auth_retrieval_fn is required to determine publish state for {entity_type}."
            )

        # If parent_auth is provided but not parent_auth_retrieval_fn, create a simple
        # retrieval function that returns the provided auth for any domain
        effective_retrieval_fn = parent_auth_retrieval_fn
        if parent_auth and not parent_auth_retrieval_fn:

            def effective_retrieval_fn(domain):
                return parent_auth

        await logger.debug(
            f"Probing if {entity_type} {entity_id} is published",
            extra={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "class_name": cls.__name__,
            },
        )

        probe = FederationContext.from_entity_id(
            auth=subscriber_auth,
            entity_id=str(entity_id),
            entity_type=entity_type,
        )

        is_published = await probe.check_if_published(
            retrieve_parent_auth_fn=effective_retrieval_fn,
            entity_type=entity_type,
            context=context,
            max_subscriptions_to_check=max_subscriptions_to_check,
        )

        await logger.debug(
            f"Probe result: {entity_type} {entity_id} is_published={is_published}",
            extra={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "is_published": is_published,
                "has_subscription": probe.subscription is not None,
            },
        )

        return probe

    def _initialize_schedule_from_raw(self):
        """Initialize Schedule from raw API data if schedule information is present.

        This helper method checks for schedule-related fields in the raw API response
        and creates a DomoSchedule instance if any are found. The DomoSchedule factory
        method automatically determines the appropriate schedule type (Simple, Cron,
        or Advanced).

        This method should be called from subclass __post_init__ after setting self.raw.

        Returns:
            DomoSchedule | None: Schedule instance if schedule data exists, None otherwise
        """
        from ..classes.subentity.schedule import DomoSchedule

        if self.raw and any(
            key in self.raw
            for key in [
                "scheduleExpression",
                "scheduleStartDate",
                "advancedScheduleJson",
            ]
        ):
            return DomoSchedule.from_dict(self.raw)

        return None


@dataclass
class DomoManager(DomoBase):
    """Base class for entity managers that handle collections of entities.

    Provides the foundation for manager classes that handle operations
    on collections of entities (e.g., DatasetManager, CardManager).

    Attributes:
        auth: Authentication object for API requests (hidden in repr)
    """

    auth: DomoAuth = field(repr=False)

    @abc.abstractmethod
    async def get(self, *args: Any, **kwargs: Any) -> list[DomoEntity]:
        """Retrieve entities based on provided criteria.

        Must be implemented by subclasses to handle entity-specific
        retrieval and filtering logic.

        Args:
            *args: Positional arguments for entity retrieval
            **kwargs: Keyword arguments for filtering and options

        Returns:
            list[DomoEntity]: List of entity instances retrieved

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("This method should be implemented by subclasses.")


@dataclass
class DomoSubEntity(DomoBase):
    """Base class for entities that belong to a parent entity.

    Handles entities that are sub-components of other entities,
    such as columns in a dataset or slides in a page. Automatically
    inherits authentication and parent references.

    Attributes:
        parent: Reference to the parent entity
        auth: Authentication object (inherited from parent, hidden in repr)
    """

    parent: DomoEntity = field(repr=False)

    @property
    def parent_id(self):
        return self.parent.id

    @property
    def auth(self):
        return self.parent.auth

    @classmethod
    def from_parent(cls, parent: DomoEntity):
        """Create a sub-entity instance from a parent entity.

        Args:
            parent (DomoEntity): The parent entity to derive from

        Returns:
            DomoSubEntity: New sub-entity instance with inherited properties
        """
        return cls(parent=parent)
