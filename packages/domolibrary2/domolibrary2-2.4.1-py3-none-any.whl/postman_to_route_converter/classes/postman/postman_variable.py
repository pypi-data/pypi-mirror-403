from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._base import PostmanBase


@dataclass
class PostmanVariable(PostmanBase):
    """Represents a Postman variable.

    Attributes:
        key (str): The variable name
        value (str): The variable value
        type (str): The variable type (e.g., 'string', 'boolean')
    """

    key: str
    value: str = ""
    type: str = "string"

    @classmethod
    def from_dict(cls, obj: dict[str, Any], **kwargs) -> PostmanVariable:
        """Create a PostmanVariable from variable data."""
        instance = cls(
            key=obj["key"],
            value=obj.get("value", ""),
            type=obj.get("type", "string"),
        )
        object.__setattr__(instance, "_raw", obj)
        return instance

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {"key": self.key, "value": self.value}
        if self.type != "string":
            result["type"] = self.type
        # _raw is excluded as per base class requirement
        return result
