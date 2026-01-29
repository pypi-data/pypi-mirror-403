"""
DomoDataflow Definition Manager

This module provides the DomoDataflow_Definition manager class for handling
dataflow definitions including actions, triggers, GUI layout, and versioning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from .core import DomoDataflow

from ...auth import DomoAuth
from ...client.context import RouteContext
from ...routes import dataflow as dataflow_routes
from ..subentity.trigger import DomoTriggerSettings
from .action import DomoDataflow_Actions, create_action_from_dict

__all__ = ["DomoDataflow_Definition"]


@dataclass
class DomoDataflow_Definition:
    """Manager class for dataflow definition.

    This class wraps the complete dataflow definition including actions,
    triggers, GUI layout, and version information.

    Attributes:
        auth: DomoAuth instance from parent dataflow
        dataflow: Reference to parent DomoDataflow
        dataflow_id: ID of the parent dataflow
        Actions: Manager for dataflow actions
        TriggerSettings: Manager for trigger configuration
        version_id: Current version ID
        version_number: Current version number
        gui: GUI canvas layout configuration
        procedures: List of procedures (legacy)
        raw: Raw definition data from API

    Example:
        >>> dataflow = await DomoDataflow.get_by_id(auth=auth, dataflow_id=123)
        >>> await dataflow.Definition.get()
        >>> print(f"Actions: {len(dataflow.Definition.Actions.actions)}")
        >>> print(f"Version: {dataflow.Definition.version_number}")
    """

    auth: DomoAuth = field(repr=False)
    dataflow: DomoDataflow = field(repr=False)
    dataflow_id: str

    # Sub-managers
    Actions: DomoDataflow_Actions = field(repr=False)
    TriggerSettings: DomoTriggerSettings | None = None

    # Definition attributes
    version_id: int | None = None
    version_number: int | None = None
    gui: dict | None = None
    procedures: list | None = None
    raw: dict | None = field(default=None, repr=False)

    @classmethod
    def from_parent(
        cls,
        parent: DomoDataflow,
        actions: list | None = None,
        trigger_settings: dict | None = None,
    ) -> DomoDataflow_Definition:
        """Create a Definition manager from a parent dataflow.

        Args:
            parent: Parent DomoDataflow instance
            actions: Optional initial list of actions
            trigger_settings: Optional trigger settings dict

        Returns:
            DomoDataflow_Definition instance
        """
        # Create Actions manager
        actions_manager = DomoDataflow_Actions.from_parent(
            parent=parent, actions=actions
        )

        # Create TriggerSettings if provided
        trigger_mgr = None
        if trigger_settings:
            trigger_mgr = DomoTriggerSettings.from_parent(
                parent=parent, obj=trigger_settings
            )

        return cls(
            auth=parent.auth,
            dataflow=parent,
            dataflow_id=parent.id,
            Actions=actions_manager,
            TriggerSettings=trigger_mgr,
            version_id=parent.version_id,
            version_number=parent.version_number,
            gui=parent.raw.get("gui") if parent.raw else None,
            procedures=parent.raw.get("procedures") if parent.raw else None,
            raw=parent.raw,
        )

    async def get(
        self,
        debug_api: bool = False,
        return_raw: bool = False,
        session: httpx.AsyncClient | None = None,
        context: RouteContext | None = None,
        **context_kwargs,
    ):
        """Fetch and refresh the dataflow definition.

        This method fetches the latest dataflow definition from the API
        and updates all definition components (actions, triggers, GUI, etc.).

        Args:
            debug_api: Enable debug logging for API calls
            return_raw: Return raw API response instead of updating
            session: Optional httpx client session
            context: Optional RouteContext for the request
            **context_kwargs: Additional context parameters

        Returns:
            Self if return_raw=False, ResponseGetData if return_raw=True

        Example:
            >>> await dataflow.Definition.get()
            >>> print(f"Loaded {len(dataflow.Definition.Actions.actions)} actions")
        """
        context = RouteContext.build_context(
            session=session, debug_api=debug_api, **context_kwargs
        )

        res = await dataflow_routes.get_dataflow_by_id(
            auth=self.auth,
            dataflow_id=self.dataflow_id,
            context=context,
        )

        if return_raw:
            return res

        if not res.is_success:
            return self

        # Update raw data
        self.raw = res.response
        self.dataflow.raw = res.response

        # Update version info
        self.version_id = res.response.get("versionId")
        self.version_number = res.response.get("versionNumber")
        self.dataflow.version_id = self.version_id
        self.dataflow.version_number = self.version_number

        # Update GUI and procedures
        self.gui = res.response.get("gui")
        self.procedures = res.response.get("procedures")

        # Update parent dataflow attributes
        self.dataflow.name = res.response.get("name")
        self.dataflow.description = res.response.get("description")
        self.dataflow.owner = res.response.get("owner")

        # Re-parse actions from the new definition
        if self.raw and self.raw.get("actions"):
            self.Actions.actions = [
                create_action_from_dict(action_dict, all_actions=[])
                for action_dict in self.raw["actions"]
            ]

        # Update trigger settings if present
        if self.raw.get("triggerSettings"):
            self.TriggerSettings = DomoTriggerSettings.from_parent(
                parent=self.dataflow, obj=self.raw["triggerSettings"]
            )

        return self

    async def update(
        self,
        new_definition: dict,
        debug_api: bool = False,
        debug_num_stacks_to_drop: int = 2,
        session: httpx.AsyncClient | None = None,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ):
        """Update the dataflow definition.

        This method updates the dataflow definition on the server and
        then refreshes the local state.

        Args:
            new_definition: New definition dictionary
            debug_api: Enable debug logging for API calls
            debug_num_stacks_to_drop: Stack frames to drop in debug logging
            session: Optional httpx client session
            context: Optional RouteContext for the request
            **context_kwargs: Additional context parameters

        Returns:
            Self with updated definition

        Example:
            >>> new_def = {"name": "Updated Name", "actions": [...]}
            >>> await dataflow.Definition.update(new_def)
        """
        context = RouteContext.build_context(
            context=context,
            session=session,
            debug_api=debug_api,
            debug_num_stacks_to_drop=debug_num_stacks_to_drop,
            **context_kwargs,
        )

        await dataflow_routes.update_dataflow_definition(
            auth=self.auth,
            dataflow_id=self.dataflow_id,
            dataflow_definition=new_definition,
            context=context,
        )

        return await self.get(return_raw=False, session=session, debug_api=debug_api)
