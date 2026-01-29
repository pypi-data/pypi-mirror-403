from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._base import PostmanBase


@dataclass
class PostmanRequest_Body(PostmanBase):
    """Represents the body of an HTTP request.

    Attributes:
        mode (str): The mode of the body (e.g., 'raw', 'formdata', 'urlencoded')
        raw (str): The actual content of the body
        options (Dict): Body options (e.g., raw language settings)
        formdata (List): Form data fields
        urlencoded (List): URL encoded fields
    """

    mode: str
    raw: str | None = None
    options: dict[str, Any] | None = None
    formdata: list[dict[str, Any]] | None = None
    urlencoded: list[dict[str, Any]] | None = None

    @classmethod
    def from_dict(
        cls, obj: dict[str, Any] | None, **kwargs
    ) -> PostmanRequest_Body | None:
        """Create a PostmanRequest_Body from body data.

        Args:
            obj (Optional[dict[str, Any]]): Dictionary containing body data
            **kwargs: Additional keyword arguments (unused)

        Returns:
            Optional[PostmanRequest_Body]: A new body instance or None if no body data
        """
        if not obj:
            return None
        instance = cls(
            mode=obj["mode"],
            raw=obj.get("raw"),
            options=obj.get("options"),
            formdata=obj.get("formdata"),
            urlencoded=obj.get("urlencoded"),
        )
        object.__setattr__(instance, "_raw", obj)
        return instance

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {"mode": self.mode}
        if self.raw:
            result["raw"] = self.raw
        if self.options:
            result["options"] = self.options
        if self.formdata:
            result["formdata"] = self.formdata
        if self.urlencoded:
            result["urlencoded"] = self.urlencoded
        # _raw is excluded as per base class requirement
        return result
