from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

from ...auth import DomoAuth
from ...base import DomoEntity_w_Lineage
from ...client.context import RouteContext
from ...routes import dataflow as dataflow_routes
from ...utils import chunk_execution as dmce
from ..DomoJupyter import Jupyter as dmdj
from ..subentity import lineage as dmdl
from ..subentity.lineage import register_lineage_type
from .definition import DomoDataflow_Definition
from .history import DomoDataflow_History

__all__ = [
    "DomoDataflow",
    "DomoDataflows",
]


@register_lineage_type("DomoDataflow", lineage_type="DATAFLOW")
@dataclass
class DomoDataflow(DomoEntity_w_Lineage):
    id: str
    auth: DomoAuth = field(repr=False)

    name: str | None = None
    owner: str | None = None
    description: str | None = None
    tags: list[str] | None = None

    version_id: int | None = None
    version_number: int | None = None
    versions: list[dict[str, Any]] | None = None  # list of DomoDataflow Versions

    jupyter_workspace_config: dict | None = None

    # Managers
    Definition: DomoDataflow_Definition | None = None  # manager for dataflow definition
    History: DomoDataflow_History | None = None  # manager for dataflow history
    JupyterWorkspace: dmdj.DomoJupyterWorkspace | None = None

    @property
    def entity_type(self):
        return "DATAFLOW"

    @property
    def entity_name(self) -> str:
        """Get the display name for this dataflow.

        Dataflows use the 'name' field as their display name.

        Returns:
            Dataflow name, or dataflow ID as fallback
        """
        return str(self.name) if self.name else self.id

    def __post_init__(self):
        # Create Definition manager which includes Actions and TriggerSettings
        actions_list = self.raw.get("actions") if self.raw else None
        trigger_settings = self.raw.get("triggerSettings") if self.raw else None

        self.Definition = DomoDataflow_Definition.from_parent(
            parent=self,
            actions=actions_list,
            trigger_settings=trigger_settings,
        )

        self.History = DomoDataflow_History(dataflow_id=self.id, auth=self.auth)

        self.Lineage = dmdl.DomoLineage.from_parent(auth=self.auth, parent=self)

    @classmethod
    def from_dict(cls, auth, obj, version_id=None, version_number=None):
        domo_dataflow = cls(
            auth=auth,
            id=obj.get("id"),
            raw=obj,
            name=obj.get("name"),
            description=obj.get("description"),
            owner=obj.get("owner") or obj.get("responsibleUserId"),
            tags=obj.get("tags"),
            version_id=version_id,
            version_number=version_number,
        )

        return domo_dataflow

    @property
    def display_url(self):
        return f"https://{self.auth.domo_instance}.domo.com/datacenter/dataflows/{self.id}/details"

    @classmethod
    async def get_by_id(
        cls,
        auth: DomoAuth,
        dataflow_id: str,
        debug_num_stacks_to_drop: int = 2,
        debug_api: bool = False,
        session: httpx.AsyncClient | None = None,
        return_raw: bool = False,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ):
        context = RouteContext.build_context(
            context=context,
            session=session,
            debug_api=debug_api,
            debug_num_stacks_to_drop=debug_num_stacks_to_drop,
            **context_kwargs,
        )

        res = await dataflow_routes.get_dataflow_by_id(
            auth=auth,
            dataflow_id=dataflow_id,
            context=context,
        )

        if return_raw:
            return res

        if not res.is_success:
            return None

        return cls.from_dict(auth=auth, obj=res.response)

    @classmethod
    async def get_entity_by_id(
        cls,
        auth: DomoAuth,
        entity_id: str,
        debug_num_stacks_to_drop: int = 2,
        debug_api: bool = False,
        session: httpx.AsyncClient | None = None,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ):
        return await cls.get_by_id(
            auth=auth,
            dataflow_id=entity_id,
            return_raw=False,
            debug_num_stacks_to_drop=debug_num_stacks_to_drop,
            debug_api=debug_api,
            session=session,
            context=context,
            **context_kwargs,
        )

    async def get_jupyter_config(
        self,
        return_raw: bool = False,
        debug_api: bool = False,
        debug_num_stacks_to_drop: int = 2,
        session: httpx.AsyncClient | None = None,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ):
        context = RouteContext.build_context(
            context=context,
            session=session,
            debug_api=debug_api,
            debug_num_stacks_to_drop=debug_num_stacks_to_drop,
            **context_kwargs,
        )

        res = await dataflow_routes.search_dataflows_to_jupyter_workspaces(
            auth=self.auth,
            dataflow_id=self.id,
            context=context,
            return_raw=return_raw,
        )

        if return_raw:
            return res

        self.jupyter_workspace = await dmdj.DomoJupyterWorkspace.get_by_id(
            auth=self.auth, workspace_id=res.response["workspaceId"]
        )

        self.jupyter_workspace_config = res.response
        if self.jupyter_workspace and self.jupyter_workspace_config:
            self.jupyter_workspace_config["workspace_name"] = (
                self.jupyter_workspace.name
            )

        return self.jupyter_workspace

    async def execute(
        self,
        debug_api: bool = False,
        debug_num_stacks_to_drop: int = 2,
        *,
        context: RouteContext | None = None,
    ):
        context = RouteContext.build_context(
            context=context,
            debug_api=debug_api,
            debug_num_stacks_to_drop=debug_num_stacks_to_drop,
        )

        return await dataflow_routes.execute_dataflow(
            auth=self.auth,
            dataflow_id=self.id,
            context=context,
        )

    @classmethod
    async def get_by_version_id(
        cls,
        auth: DomoAuth,
        dataflow_id: str,
        version_id: int,
        debug_api: bool = False,
        debug_num_stacks_to_drop: int = 2,
        session: httpx.AsyncClient | None = None,
        return_raw: bool = False,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ):
        context = RouteContext.build_context(
            context=context,
            session=session,
            debug_api=debug_api,
            debug_num_stacks_to_drop=debug_num_stacks_to_drop,
            **context_kwargs,
        )

        res = await dataflow_routes.get_dataflow_by_id_and_version(
            auth=auth,
            dataflow_id=dataflow_id,
            version_id=version_id,
            context=context,
        )

        if return_raw:
            return res

        domo_dataflow = cls.from_dict(
            auth=auth,
            obj=res.response["dataFlow"],
            version_id=res.response["id"],
            version_number=res.response["versionNumber"],
        )

        return domo_dataflow

    async def get_versions(
        self,
        debug_api: bool = False,
        debug_num_stacks_to_drop: int = 2,
        session: httpx.AsyncClient | None = None,
        return_raw: bool = False,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ):
        context = RouteContext.build_context(
            context=context,
            session=session,
            debug_api=debug_api,
            debug_num_stacks_to_drop=debug_num_stacks_to_drop,
            **context_kwargs,
        )

        res = await dataflow_routes.get_dataflow_versions(
            auth=self.auth,
            dataflow_id=self.id,
            context=context,
        )

        if return_raw:
            return res

        version_ids = [df_obj["id"] for df_obj in res.response]

        self.versions = await dmce.gather_with_concurrency(
            *[
                DomoDataflow.get_by_version_id(
                    dataflow_id=self.id,
                    version_id=version_id,
                    auth=self.auth,
                    session=session,
                    debug_api=debug_api,
                    debug_num_stacks_to_drop=debug_num_stacks_to_drop,
                    context=context,
                )
                for version_id in version_ids
            ],
            n=10,
        )

        return self.versions


@dataclass
class DomoDataflows:
    auth: DomoAuth = field(repr=False)
    dataflows: list[DomoDataflow] | None = None

    async def get(
        self,
        return_raw: bool = False,
        debug_api: bool = False,
        session: httpx.AsyncClient | None = None,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ):
        context = RouteContext.build_context(
            session=session,
            debug_api=debug_api,
            parent_class=self.__class__.__name__,
            **context_kwargs,
        )

        res = await dataflow_routes.get_dataflows(
            auth=self.auth,
            context=context,
        )

        if return_raw:
            return res

        return await dmce.gather_with_concurrency(
            *[
                DomoDataflow.get_by_id(
                    auth=self.auth, dataflow_id=obj["id"], context=context
                )
                for obj in res.response
            ],
            n=10,
        )
