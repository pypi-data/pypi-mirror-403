from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._base import PostmanBase


@dataclass
class PostmanRequest_Header(PostmanBase):
    """Represents an HTTP header in a request or response.

    Attributes:
        key (str): The name of the header (e.g., 'content-type', 'authorization')
        value (str): The value of the header
        disabled (bool): Whether the header is disabled
        description (str): Header description
        type (str): Type of header (e.g., 'text')
    """

    key: str
    value: str
    disabled: bool = False
    description: str | None = None
    type: str | None = None

    @classmethod
    def from_dict(cls, obj: dict[str, Any], **kwargs) -> PostmanRequest_Header:
        """Create a PostmanRequest_Header from header data.

        Args:
            obj (dict[str, Any]): Dictionary containing header key and value
            **kwargs: Additional keyword arguments (unused)

        Returns:
            PostmanRequest_Header: A new header instance
        """
        instance = cls(
            key=obj["key"].lower(),
            value=obj["value"],
            disabled=obj.get("disabled", False),
            description=obj.get("description"),
            type=obj.get("type"),
        )
        object.__setattr__(instance, "_raw", obj)
        return instance

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {"key": self.key, "value": self.value}
        if self.disabled:
            result["disabled"] = self.disabled
        if self.description:
            result["description"] = self.description
        if self.type:
            result["type"] = self.type
        # _raw is excluded as per base class requirement
        return result
