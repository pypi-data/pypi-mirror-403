from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._base import PostmanBase


@dataclass
class PostmanQueryParam(PostmanBase):
    """Represents a URL query parameter.

    Attributes:
        key (str): The parameter name
        value (str): The parameter value
        disabled (bool): Whether the parameter is disabled
        description (str): Parameter description
    """

    key: str
    value: str
    disabled: bool = False
    description: str | None = None

    @classmethod
    def from_dict(cls, obj: dict[str, Any], **kwargs) -> PostmanQueryParam:
        """Create a PostmanQueryParam from parameter data.

        Args:
            obj (dict[str, Any]): Dictionary containing parameter key and value
            **kwargs: Additional keyword arguments (unused)

        Returns:
            PostmanQueryParam: A new query parameter instance
        """
        instance = cls(
            key=obj["key"],
            value=obj["value"],
            disabled=obj.get("disabled", False),
            description=obj.get("description"),
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
        # _raw is excluded as per base class requirement
        return result
