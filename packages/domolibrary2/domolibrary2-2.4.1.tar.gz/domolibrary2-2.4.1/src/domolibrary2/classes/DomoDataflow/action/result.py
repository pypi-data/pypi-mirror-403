"""
DomoDataflow Action Result

This module provides the DomoDataflow_ActionResult class for execution history.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

from ....utils import convert as ct

__all__ = ["DomoDataflow_ActionResult"]


@dataclass
class DomoDataflow_ActionResult:
    """Result of an action execution from dataflow history."""

    id: str
    type: str = None
    name: str = None
    is_success: bool = None
    rows_processed: int = None
    begin_time: dt.datetime = None
    end_time: dt.datetime = None
    duration_in_sec: int = None

    def __post_init__(self):
        if self.begin_time and self.end_time:
            self.duration_in_sec = (self.end_time - self.begin_time).total_seconds()

    @classmethod
    def from_dict(cls, obj: dict[str, Any]):
        return cls(
            id=obj.get("actionId"),
            type=obj.get("type"),
            is_success=obj.get("wasSuccessful"),
            begin_time=ct.convert_epoch_millisecond_to_datetime(
                obj.get("beginTime", None)
            ),
            end_time=ct.convert_epoch_millisecond_to_datetime(obj.get("endTime", None)),
            rows_processed=obj.get("rowsProcessed", None),
        )
