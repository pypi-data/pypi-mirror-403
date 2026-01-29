from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._base import PostmanBase


@dataclass
class PostmanScript(PostmanBase):
    """Represents a Postman script (prerequest or test).

    Attributes:
        type (str): Script type (e.g., 'text/javascript')
        exec (list[str]): List of script lines
    """

    type: str = "text/javascript"
    exec: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, obj: dict[str, Any], **kwargs) -> PostmanScript:
        """Create a PostmanScript from script data."""
        instance = cls(
            type=obj.get("type", "text/javascript"),
            exec=obj.get("exec", []),
        )
        object.__setattr__(instance, "_raw", obj)
        return instance

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        # _raw is excluded as per base class requirement
        return {"type": self.type, "exec": self.exec}
