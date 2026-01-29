from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._base import PostmanBase
from .postman_auth import PostmanAuth
from .postman_event import PostmanEvent
from .postman_request_body import PostmanRequest_Body
from .postman_request_header import PostmanRequest_Header
from .postman_response import PostmanResponse
from .postman_url import PostmanUrl
from .postman_variable import PostmanVariable


@dataclass
class PostmanRequest(PostmanBase):
    """Represents a single request in a Postman collection.

    A request typically represents a single API endpoint with its request
    and response details.

    Attributes:
        name (str): The name of the request
        method (str): The HTTP method (e.g., 'GET', 'POST', 'PUT')
        header (list[PostmanRequest_Header]): List of HTTP headers
        url (PostmanUrl): The request URL
        body (Optional[PostmanRequest_Body]): The request body, if any
        response (list[PostmanResponse]): List of example responses
        auth (Optional[PostmanAuth]): Authentication configuration
        event (Optional[list[PostmanEvent]]): Request-level events
        description (Optional[str]): Request description
        variable (Optional[list[PostmanVariable]]): Request-level variables
    """

    name: str
    method: str
    header: list[PostmanRequest_Header]
    url: PostmanUrl
    body: PostmanRequest_Body | None = None
    response: list[PostmanResponse] = field(default_factory=list)
    auth: PostmanAuth | None = None
    event: list[PostmanEvent] | None = None
    description: str | None = None
    variable: list[PostmanVariable] | None = None

    @classmethod
    def from_dict(cls, obj: dict[str, Any], **kwargs) -> PostmanRequest:
        """Create a PostmanRequest from item data.

        Args:
            obj (dict[str, Any]): Dictionary containing request data
            **kwargs: Additional keyword arguments (unused)

        Returns:
            PostmanRequest: A new request instance
        """
        request_data = obj["request"]

        # Handle responses
        responses = []
        if obj.get("response"):
            responses = [PostmanResponse.from_dict(r) for r in obj["response"]]

        # Handle events
        events = None
        if obj.get("event"):
            events = [PostmanEvent.from_dict(e) for e in obj["event"]]

        # Handle variables
        variables = None
        if obj.get("variable"):
            variables = [PostmanVariable.from_dict(v) for v in obj["variable"]]

        instance = cls(
            name=obj["name"],
            method=request_data["method"],
            header=[
                PostmanRequest_Header.from_dict(h)
                for h in request_data.get("header", [])
            ],
            url=PostmanUrl.from_dict(request_data["url"]),
            body=PostmanRequest_Body.from_dict(request_data.get("body")),
            response=responses,
            auth=PostmanAuth.from_dict(request_data.get("auth")),
            event=events,
            description=obj.get("description"),
            variable=variables,
        )
        object.__setattr__(instance, "_raw", obj)
        return instance

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation for validation."""
        request_data = {
            "method": self.method,
            "header": [h.to_dict() for h in self.header],
            "url": self.url.to_dict(),
        }

        if self.body:
            request_data["body"] = self.body.to_dict()
        if self.auth:
            request_data["auth"] = self.auth.to_dict()

        result = {"name": self.name, "request": request_data}

        if self.response:
            result["response"] = [r.to_dict() for r in self.response]
        if self.event:
            result["event"] = [e.to_dict() for e in self.event]
        if self.description:
            result["description"] = self.description
        if self.variable:
            result["variable"] = [v.to_dict() for v in self.variable]
        # _raw is excluded as per base class requirement
        return result
