from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._base import PostmanBase


@dataclass
class PostmanAuth(PostmanBase):
    """Represents Postman authentication configuration.

    Attributes:
        type (str): Authentication type (e.g., 'bearer', 'basic', 'apikey')
        bearer (list[Dict]): Bearer token configuration
        basic (list[Dict]): Basic auth configuration
        apikey (list[Dict]): API key configuration
    """

    type: str | None = None
    bearer: list[dict[str, Any]] | None = None
    basic: list[dict[str, Any]] | None = None
    apikey: list[dict[str, Any]] | None = None

    @classmethod
    def from_dict(cls, obj: dict[str, Any] | None, **kwargs) -> PostmanAuth | None:
        """Create a PostmanAuth from auth data."""
        if not obj:
            return None

        instance = cls(
            type=obj.get("type"),
            bearer=obj.get("bearer"),
            basic=obj.get("basic"),
            apikey=obj.get("apikey"),
        )
        object.__setattr__(instance, "_raw", obj)
        return instance

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {}
        if self.type:
            result["type"] = self.type
        if self.bearer:
            result["bearer"] = self.bearer
        if self.basic:
            result["basic"] = self.basic
        if self.apikey:
            result["apikey"] = self.apikey
        # _raw is excluded as per base class requirement
        return result
