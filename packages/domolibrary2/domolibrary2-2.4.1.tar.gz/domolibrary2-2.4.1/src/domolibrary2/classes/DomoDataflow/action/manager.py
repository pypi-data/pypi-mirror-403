"""
DomoDataflow Actions Manager

This module provides the DomoDataflow_Actions manager class for handling
dataflow actions with computed properties for analysis and filtering.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from ..core import DomoDataflow

from ....auth import DomoAuth
from ....client.context import RouteContext
from .base import (
    DomoDataflow_Action_Base,
    create_action_from_dict,
)

__all__ = ["DomoDataflow_Actions"]


@dataclass
class DomoDataflow_Actions:
    """Manager class for dataflow actions.

    This class wraps the actions list from a dataflow and provides
    computed properties for filtering and analysis.

    Attributes:
        auth: DomoAuth instance from parent dataflow
        dataflow: Reference to parent DomoDataflow
        dataflow_id: ID of the parent dataflow
        actions: List of action objects

    Example:
        >>> dataflow = await DomoDataflow.get_by_id(auth=auth, dataflow_id=123)
        >>> await dataflow.Actions.get()
        >>> print(f"Has data science tiles: {dataflow.Actions.has_datascience_tiles}")
        >>> print(f"Input datasets: {dataflow.Actions.input_datasets}")
    """

    auth: DomoAuth = field(repr=False)
    dataflow: DomoDataflow = field(repr=False)
    dataflow_id: str
    actions: list[DomoDataflow_Action_Base] = field(default_factory=list)

    @classmethod
    def from_parent(
        cls, parent: DomoDataflow, actions: list[DomoDataflow_Action_Base] | None = None
    ) -> DomoDataflow_Actions:
        """Create an Actions manager from a parent dataflow.

        Args:
            parent: Parent DomoDataflow instance
            actions: Optional initial list of actions

        Returns:
            DomoDataflow_Actions instance
        """
        return cls(
            auth=parent.auth,
            dataflow=parent,
            dataflow_id=parent.id,
            actions=actions or [],
        )

    async def get(
        self,
        session: httpx.AsyncClient | None = None,
        debug_api: bool = False,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> list[DomoDataflow_Action_Base]:
        """Get actions from the dataflow definition.

        This method fetches the latest dataflow definition and populates
        the actions list.

        Args:
            session: Optional httpx client session
            debug_api: Enable debug logging for API calls
            context: Optional RouteContext for the request
            **context_kwargs: Additional context parameters

        Returns:
            List of action objects

        Example:
            >>> actions = await dataflow.Actions.get()
            >>> for action in actions:
            ...     print(f"{action.name}: {action.action_type}")
        """
        # Get the dataflow definition (this populates dataflow.raw)
        # Use the parent dataflow's Definition manager get method

        # If this Actions manager is part of a Definition, use its get method
        # Otherwise, call the definition's get directly
        if hasattr(self.dataflow, "Definition") and self.dataflow.Definition:
            await self.dataflow.Definition.get(
                context=context,
                session=session,  # type: ignore
                debug_api=debug_api,
            )
        else:
            # Fallback: directly fetch and update raw
            from ....routes import dataflow as dataflow_routes

            res = await dataflow_routes.get_dataflow_by_id(
                auth=self.auth,
                dataflow_id=self.dataflow_id,
                context=context,
            )
            if res.is_success:
                self.dataflow.raw = res.response

        # Parse actions from the raw definition
        if self.dataflow.raw and self.dataflow.raw.get("actions"):
            self.actions = [
                create_action_from_dict(action_dict, all_actions=self.actions)
                for action_dict in self.dataflow.raw["actions"]
            ]

        return self.actions

    @property
    def has_datascience_tiles(self) -> bool:
        """Check if the dataflow has any data science tiles.

        Returns:
            True if any action is a data science tile, False otherwise

        Example:
            >>> if dataflow.Actions.has_datascience_tiles:
            ...     print("This dataflow uses data science operations")
        """
        return any(action.is_datascience_tile for action in self.actions)

    @property
    def datascience_tiles(self) -> list[DomoDataflow_Action_Base]:
        """Get list of data science actions.

        Returns:
            Filtered list of data science actions

        Example:
            >>> ds_tiles = dataflow.Actions.datascience_tiles
            >>> print(f"Found {len(ds_tiles)} data science tiles")
        """
        return [action for action in self.actions if action.is_datascience_tile]

    @property
    def tile_type_counts(self) -> dict[str, int]:
        """Get count of actions by tile type.

        Returns:
            Dictionary mapping tile_type to count

        Example:
            >>> counts = dataflow.Actions.tile_type_counts
            >>> for tile_type, count in counts.items():
            ...     print(f"{tile_type}: {count}")
        """
        return dict(
            Counter(action.tile_type for action in self.actions if action.tile_type)
        )

    @property
    def action_type_counts(self) -> dict[str, int]:
        """Get count of actions by action type.

        Returns:
            Dictionary mapping action_type to count

        Example:
            >>> counts = dataflow.Actions.action_type_counts
            >>> for action_type, count in counts.items():
            ...     print(f"{action_type}: {count}")
        """
        return dict(Counter(action.action_type for action in self.actions))

    @property
    def input_datasets(self) -> list[dict[str, Any]]:
        """Get list of input datasets (LoadFromVault actions).

        Returns:
            List of dicts with 'id' and 'name' keys for each input dataset

        Example:
            >>> for ds in dataflow.Actions.input_datasets:
            ...     print(f"Input: {ds['name']} ({ds['id']})")
        """
        inputs = []
        for action in self.actions:
            if action.action_type == "LoadFromVault":
                # Try to get dataset ID from various possible fields
                dataset_id = None
                if hasattr(action, "data_source_id"):
                    dataset_id = action.data_source_id  # type: ignore
                elif action.raw:
                    dataset_id = action.raw.get("dataSourceId")

                if dataset_id:
                    inputs.append(
                        {
                            "id": dataset_id,
                            "name": action.name or "Unknown Dataset",
                        }
                    )

        return inputs

    @property
    def output_datasets(self) -> list[dict[str, Any]]:
        """Get list of output datasets (PublishToVault/WriteToVault actions).

        Returns:
            List of dicts with 'id' and 'name' keys for each output dataset

        Example:
            >>> for ds in dataflow.Actions.output_datasets:
            ...     print(f"Output: {ds['name']} ({ds['id']})")
        """
        outputs = []
        for action in self.actions:
            if action.action_type in [
                "PublishToVault",
                "WriteToVault",
                "OutputDataset",
            ]:
                # Try to get dataset ID from various possible fields
                dataset_id = None

                # Check settings first
                if action.settings:
                    dataset_id = action.settings.get(
                        "datasetId"
                    ) or action.settings.get("outputDatasetId")

                # Check raw data
                if not dataset_id and action.raw:
                    # Check dataSource.guid
                    datasource = action.raw.get("dataSource", {})
                    dataset_id = datasource.get("guid")

                if dataset_id:
                    outputs.append(
                        {
                            "id": dataset_id,
                            "name": action.name or "Unknown Output Dataset",
                        }
                    )

        return outputs

    @property
    def disabled_actions(self) -> list[DomoDataflow_Action_Base]:
        """Get list of disabled actions.

        Returns:
            Filtered list of disabled actions

        Example:
            >>> disabled = dataflow.Actions.disabled_actions
            >>> print(f"Found {len(disabled)} disabled actions")
        """
        return [action for action in self.actions if action.disabled]

    def get_action_by_id(self, action_id: str) -> DomoDataflow_Action_Base | None:
        """Get an action by its ID.

        Args:
            action_id: ID of the action to find

        Returns:
            The action object, or None if not found

        Example:
            >>> action = dataflow.Actions.get_action_by_id("abc123")
            >>> if action:
            ...     print(f"Found action: {action.name}")
        """
        for action in self.actions:
            if action.id == action_id:
                return action
        return None

    def get_actions_by_type(self, action_type: str) -> list[DomoDataflow_Action_Base]:
        """Get all actions of a specific type.

        Args:
            action_type: The action type to filter by (e.g., "Filter", "GroupBy")

        Returns:
            List of actions matching the type

        Example:
            >>> filters = dataflow.Actions.get_actions_by_type("Filter")
            >>> print(f"Found {len(filters)} filter actions")
        """
        return [action for action in self.actions if action.action_type == action_type]

    def get_script_content(self, action_id: str) -> str | None:
        """Extract script content from Python, R, or SQL script tiles.

        Args:
            action_id: ID of the action to extract script from

        Returns:
            Script content as string, or None if not a script tile or script not found

        Example:
            >>> script = dataflow.Actions.get_script_content("abc123")
            >>> if script:
            ...     print(script)
        """
        action = self.get_action_by_id(action_id)
        if not action:
            return None

        # Check for direct script field
        if hasattr(action, "script") and action.script:  # type: ignore
            return action.script  # type: ignore

        # Check settings
        if action.settings:
            script = (
                action.settings.get("script")
                or action.settings.get("code")
                or action.settings.get("pythonScript")
                or action.settings.get("rScript")
                or action.settings.get("sql")
                or action.settings.get("query")
                or action.settings.get("sqlScript")
            )
            if script:
                return script

        # Check raw data
        if action.raw:
            return action.raw.get("script")

        return None
