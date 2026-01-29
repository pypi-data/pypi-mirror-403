from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._base import PostmanBase
from .postman_request_header import PostmanRequest_Header


@dataclass
class PostmanResponse(PostmanBase):
    """Represents an HTTP response in a Postman collection.

    Attributes:
        name (str): Name of the response example
        originalRequest (Dict): The original request that generated this response
        status (str): HTTP status text (e.g., 'OK')
        code (int): HTTP status code (e.g., 200)
        header (list[PostmanRequest_Header]): Response headers
        cookie (List): Response cookies
        body (str): Response body content
        _postman_previewlanguage (str): Preview language (e.g., 'json', 'html')
    """

    name: str | None = None
    originalRequest: dict[str, Any] | None = None
    status: str | None = None
    code: int | None = None
    header: list[PostmanRequest_Header] | None = None
    cookie: list[dict[str, Any]] | None = None
    body: str | None = None
    _postman_previewlanguage: str | None = None

    @classmethod
    def from_dict(cls, obj: dict[str, Any], **kwargs) -> PostmanResponse:
        """Create a PostmanResponse from response data."""
        headers = None
        if obj.get("header"):
            headers = [PostmanRequest_Header.from_dict(h) for h in obj["header"]]

        instance = cls(
            name=obj.get("name"),
            originalRequest=obj.get("originalRequest"),
            status=obj.get("status"),
            code=obj.get("code"),
            header=headers,
            cookie=obj.get("cookie"),
            body=obj.get("body"),
            _postman_previewlanguage=obj.get("_postman_previewlanguage"),
        )
        object.__setattr__(instance, "_raw", obj)
        return instance

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {}
        if self.name:
            result["name"] = self.name
        if self.originalRequest:
            result["originalRequest"] = self.originalRequest
        if self.status:
            result["status"] = self.status
        if self.code:
            result["code"] = self.code
        if self.header:
            result["header"] = [h.to_dict() for h in self.header]
        if self.cookie:
            result["cookie"] = self.cookie
        if self.body:
            result["body"] = self.body
        if self._postman_previewlanguage:
            result["_postman_previewlanguage"] = self._postman_previewlanguage
        # _raw is excluded as per base class requirement
        return result
