from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any

from ...auth import DomoAuth
from ...client.context import RouteContext
from ...routes import dataflow as dataflow_routes
from ...utils import (
    chunk_execution as ce,
    convert as ct,
)

__all__ = ["DomoDataflow_History_Execution", "DomoDataflow_History"]

from .action import DomoDataflow_ActionResult


@dataclass
class DomoDataflow_History_Execution:
    auth: DomoAuth = field(repr=False)
    id: str
    dataflow_id: str
    dataflow_execution_id: str
    dataflow_version: str

    is_failed: bool
    state: str
    activation_type: str
    data_processor: str
    telemetry: dict
    execution_stats: dict

    begin_time: dt.datetime | None = None
    last_updated: dt.datetime | None = None
    end_time: dt.datetime | None = None

    action_results: list[DomoDataflow_ActionResult] | None = None

    @staticmethod
    def _process_results(action_results: list[dict]) -> list[DomoDataflow_ActionResult]:
        return [
            DomoDataflow_ActionResult.from_dict(action_obj)
            for action_obj in action_results
        ]

    @classmethod
    def from_dict(cls, de_obj: dict, auth: DomoAuth) -> DomoDataflow_History_Execution:
        action_results = de_obj.get("actionResults") and cls._process_results(
            de_obj.get("actionResults", [])
        )

        return cls(
            auth=auth,
            id=de_obj["id"],
            dataflow_id=de_obj["onboardFlowId"],
            dataflow_execution_id=de_obj["dapDataFlowExecutionId"],
            dataflow_version=de_obj["dataFlowVersion"],
            begin_time=de_obj.get("beginTime")
            and ct.convert_epoch_millisecond_to_datetime(de_obj.get("beginTime")),
            end_time=de_obj.get("endTime")
            and ct.convert_epoch_millisecond_to_datetime(de_obj.get("endTime")),
            last_updated=de_obj.get("lastUpdated")
            and ct.convert_epoch_millisecond_to_datetime(de_obj["lastUpdated"]),
            is_failed=de_obj["failed"],
            state=de_obj["state"],
            activation_type=de_obj["activationType"],
            data_processor=de_obj["dataProcessor"],
            telemetry=de_obj.get("telemetry", {}),
            execution_stats={
                "total_bytes_written": de_obj.get("totalBytesWritten", 0),
                "total_rows_read": de_obj.get("totalRowsRead", 0),
                "total_bytes_read": de_obj.get("totalBytesRead", 0),
                "mean_download_rate_kbps": de_obj.get("meanDownloadRateKbps", 0),
                "total_rows_written": de_obj.get("totalRowsWritten", 0),
            },
            action_results=action_results,
        )

    @classmethod
    async def get_by_id(
        cls,
        auth: DomoAuth,
        dataflow_id: int,
        execution_id: int,
        return_raw: bool = False,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> DomoDataflow_History_Execution:
        """retrieves details about a dataflow execution including actions"""

        base_context = RouteContext.build_context(
            parent_class=cls.__name__,
            **context_kwargs,
        )
        context = RouteContext.build_context(context=context or base_context)

        res = await dataflow_routes.get_dataflow_execution_by_id(
            auth=auth,
            dataflow_id=dataflow_id,
            execution_id=execution_id,
            context=context,
        )

        if return_raw:
            return res

        return cls.from_dict(auth=auth, de_obj=res.response)

    async def get_actions(
        self,
        return_raw: bool = False,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> list[DomoDataflow_ActionResult]:
        """retrieves details execution action results"""

        base_context = RouteContext.build_context(
            parent_class=self.__class__.__name__,
            **context_kwargs,
        )
        context = RouteContext.build_context(context=context or base_context)

        res = await dataflow_routes.get_dataflow_execution_by_id(
            auth=self.auth,
            dataflow_id=self.dataflow_id,
            execution_id=self.id,
            context=context,
        )

        if return_raw:
            return res

        self.action_results = self._process_results(
            res.response.get("actionResults", [])
        )

        return self.action_results


@dataclass
class DomoDataflow_History:
    auth: DomoAuth = field(repr=False)
    dataflow_id: str = field(repr=False)

    dataflow: Any = field(repr=False, default=None)

    execution_history: list[DomoDataflow_History_Execution] | None = None

    async def get_execution_history(
        self,
        auth: DomoAuth | None = None,
        maximum: int = 10,  # maximum number of execution histories to retrieve
        return_raw: bool = False,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> list[DomoDataflow_History_Execution]:
        """retrieves metadata about execution history.
        includes details like execution status.
        """

        auth = auth or self.auth or self.dataflow.auth

        base_context = RouteContext.build_context(
            parent_class=self.__class__.__name__,
            **context_kwargs,
        )
        context = RouteContext.build_context(context=context or base_context)

        res = await dataflow_routes.get_dataflow_execution_history(
            auth=auth,
            dataflow_id=self.dataflow_id,
            maximum=maximum,
            context=context,
        )

        if return_raw:
            return res

        execution_history = [
            DomoDataflow_History_Execution.from_dict(df_obj, auth)
            for df_obj in res.response
        ]

        await ce.gather_with_concurrency(
            *[
                domo_execution.get_actions(context=context)
                for domo_execution in execution_history
            ],
            n=20,
        )

        self.execution_history = execution_history

        return self.execution_history
