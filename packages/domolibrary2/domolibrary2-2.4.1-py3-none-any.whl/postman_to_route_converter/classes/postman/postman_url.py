from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._base import PostmanBase
from .postman_query_param import PostmanQueryParam
from .postman_variable import PostmanVariable


@dataclass
class PostmanUrl(PostmanBase):
    """Represents a complete URL with all its components.

    Attributes:
        raw (str): The complete URL as a string
        protocol (str): The protocol (e.g., 'http', 'https')
        host (list[str]): The host components (e.g., ['api', 'example', 'com'])
        path (list[str]): The path components
        query (Optional[list[PostmanQueryParam]]): List of query parameters, if any
        variable (Optional[list[PostmanVariable]]): List of URL variables
    """

    raw: str
    protocol: str | None = None
    host: list[str] | None = None
    path: list[str] | None = None
    query: list[PostmanQueryParam] | None = None
    variable: list[PostmanVariable] | None = None

    @classmethod
    def from_dict(cls, obj: dict[str, Any], **kwargs) -> PostmanUrl:
        """Create a PostmanUrl from URL data.

        Args:
            obj (dict[str, Any]): Dictionary containing URL components
            **kwargs: Additional keyword arguments (unused)

        Returns:
            PostmanUrl: A new URL instance
        """
        instance = cls(
            raw=obj["raw"],
            protocol=obj.get("protocol"),
            host=obj.get("host"),
            path=obj.get("path"),
            query=(
                [PostmanQueryParam.from_dict(q) for q in obj.get("query", [])]
                if obj.get("query")
                else None
            ),
            variable=(
                [PostmanVariable.from_dict(v) for v in obj.get("variable", [])]
                if obj.get("variable")
                else None
            ),
        )
        object.__setattr__(instance, "_raw", obj)
        return instance

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {"raw": self.raw}
        if self.protocol:
            result["protocol"] = self.protocol
        if self.host:
            result["host"] = self.host
        if self.path:
            result["path"] = self.path
        if self.query:
            result["query"] = [q.to_dict() for q in self.query]
        if self.variable:
            result["variable"] = [v.to_dict() for v in self.variable]
        # _raw is excluded as per base class requirement
        return result
