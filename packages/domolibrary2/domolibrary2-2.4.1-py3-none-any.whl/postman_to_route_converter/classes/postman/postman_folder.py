from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._base import PostmanBase
from .postman_auth import PostmanAuth
from .postman_event import PostmanEvent
from .postman_request import PostmanRequest
from .postman_variable import PostmanVariable


@dataclass
class PostmanFolder(PostmanBase):
    """Represents a folder in a Postman collection that can contain other items.

    Attributes:
        name (str): Name of the folder
        item (list[Union['PostmanFolder', 'PostmanRequest']]): Items in the folder
        description (Optional[str]): Folder description
        auth (Optional[PostmanAuth]): Folder-level authentication
        event (Optional[list[PostmanEvent]]): Folder-level events
        variable (Optional[list[PostmanVariable]]): Folder-level variables
    """

    name: str
    item: list[PostmanFolder | PostmanRequest] = field(default_factory=list)
    description: str | None = None
    auth: PostmanAuth | None = None
    event: list[PostmanEvent] | None = None
    variable: list[PostmanVariable] | None = None

    @classmethod
    def from_dict(cls, obj: dict[str, Any], **kwargs) -> PostmanFolder:
        """Create a PostmanFolder from folder data."""
        items = []
        for item_data in obj.get("item", []):
            if "request" in item_data:
                items.append(PostmanRequest.from_dict(item_data))
            else:
                items.append(PostmanFolder.from_dict(item_data))

        events = None
        if obj.get("event"):
            events = [PostmanEvent.from_dict(e) for e in obj["event"]]

        variables = None
        if obj.get("variable"):
            variables = [PostmanVariable.from_dict(v) for v in obj["variable"]]

        instance = cls(
            name=obj["name"],
            item=items,
            description=obj.get("description"),
            auth=PostmanAuth.from_dict(obj.get("auth")),
            event=events,
            variable=variables,
        )
        object.__setattr__(instance, "_raw", obj)
        return instance

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {"name": self.name, "item": [item.to_dict() for item in self.item]}

        if self.description:
            result["description"] = self.description
        if self.auth:
            result["auth"] = self.auth.to_dict()
        if self.event:
            result["event"] = [e.to_dict() for e in self.event]
        if self.variable:
            result["variable"] = [v.to_dict() for v in self.variable]
        # _raw is excluded as per base class requirement
        return result

    def get_all_requests(self) -> list[PostmanRequest]:
        """Recursively get all requests from this folder and subfolders."""
        requests = []
        for item in self.item:
            if isinstance(item, PostmanRequest):
                requests.append(item)
            elif isinstance(item, PostmanFolder):
                requests.extend(item.get_all_requests())
        return requests
