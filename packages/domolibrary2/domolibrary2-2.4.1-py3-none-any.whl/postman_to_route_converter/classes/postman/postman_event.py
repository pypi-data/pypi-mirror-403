from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._base import PostmanBase
from .postman_script import PostmanScript


@dataclass
class PostmanEvent(PostmanBase):
    """Represents a Postman event (prerequest or test).

    Attributes:
        listen (str): Event type ('prerequest' or 'test')
        script (PostmanScript): The script to execute
    """

    listen: str
    script: PostmanScript

    @classmethod
    def from_dict(cls, obj: dict[str, Any], **kwargs) -> PostmanEvent:
        """Create a PostmanEvent from event data."""
        instance = cls(
            listen=obj["listen"],
            script=PostmanScript.from_dict(obj.get("script", {})),
        )
        object.__setattr__(instance, "_raw", obj)
        return instance

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        # _raw is excluded as per base class requirement
        return {"listen": self.listen, "script": self.script.to_dict()}
