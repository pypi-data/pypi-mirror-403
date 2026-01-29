"""
DomoDataflow Action Base Classes and Registry

This module provides the registration pattern for Magic ETL v2 action types.
Each action type can be registered via the @register_action_type decorator,
allowing for graceful handling of unknown action types while providing
typed access to known ones.

Usage:
    # Get the appropriate action class for a type
    action_class = get_action_class("LoadFromVault")
    action = action_class.from_dict(raw_action_dict)

    # Or use the factory function
    action = create_action_from_dict(raw_action_dict)
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any

from ....utils import (
    DictDot as util_dd,
)

__all__ = [
    # Registry functions
    "register_action_type",
    "get_action_class",
    "get_action_category",
    "create_action_from_dict",
    "get_registered_action_types",
    "get_unregistered_action_types",
    # Base classes
    "DomoDataflow_Action_Base",
    "DomoDataflow_Action_Unknown",
    # Constants
    "DATA_SCIENCE_ACTION_TYPES",
]


# Note: Standard logging is NOT used in domolibrary2 - dc_logger is async.
# For sync contexts (like __post_init__), use warnings.warn() instead.


# ============================================================================
# Registry and Decorator
# ============================================================================

# Registry to store action type classes
_ACTION_TYPE_REGISTRY: dict[str, type[DomoDataflow_Action_Base]] = {}

# Registry to store action type categories (TileType)
_ACTION_CATEGORY_REGISTRY: dict[str, str] = {}

# Track encountered but unregistered types (for discovery)
_UNREGISTERED_TYPES: set[str] = set()

# Action types that are classified as data science tiles
# These are tiles typically used for data transformation, analysis, and ML operations
DATA_SCIENCE_ACTION_TYPES: set[str] = {
    "MLInferenceAction",
    "UserDefinedAction",
    "PythonEngineAction",
    "GroupBy",
    "WindowAction",
    "NumericCalculator",
    "DateCalculator",
    "Unique",
    "Rank",
    "DynamicBucket",
    "Aggregate",
    "MergeJoin",
    "SplitJoin",
    "UnionAll",
}


def register_action_type(action_type: str, category: str | None = None):
    """Decorator to register a DomoDataflow_Action_Base subclass.

    Args:
        action_type: The action type identifier (e.g., 'LoadFromVault', 'Filter')
        category: The tile category/type (e.g., 'filter', 'aggregate', 'pivot').
                  Defaults to the module folder name where the action is defined.

    Example:
        @register_action_type('Filter', category='filter')
        @dataclass
        class DomoDataflow_Action_Filter(DomoDataflow_Action_Base):
            filter_list: list[dict] = None
    """

    def decorator(
        cls: type[DomoDataflow_Action_Base],
    ) -> type[DomoDataflow_Action_Base]:
        _ACTION_TYPE_REGISTRY[action_type] = cls

        # Store category if provided, otherwise use None (will default to module name)
        if category:
            _ACTION_CATEGORY_REGISTRY[action_type] = category

        return cls

    return decorator


def get_action_class(action_type: str) -> type[DomoDataflow_Action_Base]:
    """Get the registered action class for a given type.

    If the type is not registered, returns DomoDataflow_Action_Unknown
    and tracks it for discovery purposes.

    Args:
        action_type: The action type string (e.g., "LoadFromVault")

    Returns:
        The registered action class, or DomoDataflow_Action_Unknown
    """
    cls = _ACTION_TYPE_REGISTRY.get(action_type)
    if cls is None:
        _UNREGISTERED_TYPES.add(action_type)
        # Note: Using warnings.warn() because this is a sync function.
        # dc_logger is async and cannot be used in sync contexts.
        return DomoDataflow_Action_Unknown
    return cls


def get_action_category(action_type: str) -> str | None:
    """Get the registered category (TileType) for a given action type.

    Args:
        action_type: The action type string (e.g., "LoadFromVault")

    Returns:
        The category string (e.g., 'filter', 'aggregate') or None if not registered
    """
    return _ACTION_CATEGORY_REGISTRY.get(action_type)


def create_action_from_dict(
    obj: dict[str, Any], all_actions: list[DomoDataflow_Action_Base] | None = None
) -> DomoDataflow_Action_Base:
    """Factory function to create the appropriate action instance from a dict.

    This is the recommended way to create action instances from API responses.
    It automatically selects the appropriate class based on the 'type' field.

    Args:
        obj: Raw action dict from the API
        all_actions: Optional list of already-created actions for dependency resolution

    Returns:
        Appropriate DomoDataflow_Action_* instance

    Example:
        >>> for raw_action in dataflow.raw['procedures'][0]['actions']:
        ...     action = create_action_from_dict(raw_action)
        ...     print(f"{action.action_type}: {action.name}")
    """
    action_type = obj.get("type", "Unknown")
    cls = get_action_class(action_type)
    return cls.from_dict(obj, all_actions=all_actions)


def get_registered_action_types() -> list[str]:
    """Get list of all registered action types."""
    return sorted(_ACTION_TYPE_REGISTRY.keys())


def get_unregistered_action_types() -> set[str]:
    """Get set of action types that were encountered but not registered.

    Useful for discovering new action types that need to be implemented.
    """
    return _UNREGISTERED_TYPES.copy()


# ============================================================================
# Base Action Classes
# ============================================================================


@dataclass
class DomoDataflow_Action_Base:
    """Base class for all dataflow action types.

    All specific action types should inherit from this class and use
    the @register_action_type decorator.

    Common fields present in all action types:
        - id: Unique identifier for the action
        - action_type: The type string (e.g., "LoadFromVault")
        - tile_type: The category/type of tile (e.g., 'filter', 'aggregate', 'pivot')
        - name: Display name of the action (tile name)
        - depends_on: List of action IDs this action depends on
        - disabled: Whether the action is disabled
        - gui: GUI positioning data
        - settings: Action-specific settings
        - raw: Original API response dict
    """

    id: str
    action_type: str = None
    tile_type: str | None = None
    name: str = None
    depends_on: list[str] = None
    disabled: bool = False
    gui: dict = field(default=None, repr=False)
    settings: dict = field(default=None, repr=False)
    raw: dict = field(default=None, repr=False)

    # For dependency graph traversal
    parent_actions: list[DomoDataflow_Action_Base] = field(default=None, repr=False)

    @classmethod
    def from_dict(
        cls,
        obj: dict[str, Any],
        all_actions: list[DomoDataflow_Action_Base] | None = None,
    ) -> DomoDataflow_Action_Base:
        """Create an action instance from an API response dict.

        Subclasses can override _extract_fields() to handle type-specific fields.
        """
        dd = obj if isinstance(obj, util_dd.DictDot) else util_dd.DictDot(obj)

        # Determine tile_type (category)
        action_type = dd.type
        tile_type = get_action_category(action_type)
        if tile_type is None and cls.__module__:
            # Default to module name if not explicitly registered
            # e.g., 'domolibrary2.classes.DomoDataflow.action.filter' -> 'filter'
            module_parts = cls.__module__.split(".")
            if len(module_parts) > 0:
                tile_type = module_parts[-1]

        # Extract common fields
        instance = cls(
            id=dd.id,
            action_type=action_type,
            tile_type=tile_type,
            name=dd.name or dd.targetTableName or dd.tableName,
            depends_on=dd.dependsOn or [],
            disabled=dd.disabled or False,
            gui=dd.gui,
            settings=dd.settings,
            raw=obj,
        )

        # Let subclasses extract type-specific fields
        instance._extract_fields(dd)

        # Resolve parent actions if provided
        if all_actions:
            instance.get_parents(all_actions)

        return instance

    def _extract_fields(self, dd: util_dd.DictDot) -> None:
        """Extract type-specific fields from the dict. Override in subclasses."""
        pass

    @property
    def is_datascience_tile(self) -> bool:
        """Check if this action is a data science tile.

        Returns True if the action type is in DATA_SCIENCE_ACTION_TYPES
        or if the tile category is 'data_science'.

        Returns:
            True if this is a data science tile, False otherwise
        """
        return (
            self.action_type in DATA_SCIENCE_ACTION_TYPES
            or self.tile_type == "data_science"
        )

    def get_parents(
        self, domo_actions: list[DomoDataflow_Action_Base]
    ) -> list[DomoDataflow_Action_Base] | None:
        """Resolve parent actions from the depends_on IDs."""
        if self.depends_on and len(self.depends_on) > 0:
            self.parent_actions = [
                parent_action
                for depends_id in self.depends_on
                for parent_action in domo_actions
                if parent_action.id == depends_id
            ]

            if self.parent_actions:
                for parent in self.parent_actions:
                    if parent.depends_on:
                        parent.get_parents(domo_actions)

        return self.parent_actions


@dataclass
class DomoDataflow_Action_Unknown(DomoDataflow_Action_Base):
    """Fallback action class for unregistered action types.

    This class is used when an action type is encountered that hasn't been
    registered. All fields from the API response are preserved in the 'raw'
    attribute.
    """

    def __post_init__(self):
        if self.action_type:
            # Note: Using warnings.warn() because __post_init__ is sync.
            # dc_logger is async and cannot be used in sync contexts.
            warnings.warn(
                f"Unknown action type '{self.action_type}' encountered. "
                f"Consider registering it with @register_action_type('{self.action_type}')",
                stacklevel=2,
            )
