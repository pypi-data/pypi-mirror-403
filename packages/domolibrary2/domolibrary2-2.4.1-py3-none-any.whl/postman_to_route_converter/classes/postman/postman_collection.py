from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from ._base import PostmanBase
from .postman_auth import PostmanAuth
from .postman_collection_info import PostmanCollectionInfo
from .postman_event import PostmanEvent
from .postman_folder import PostmanFolder
from .postman_request import PostmanRequest
from .postman_variable import PostmanVariable


@dataclass
class PostmanCollection(PostmanBase):
    """Represents a complete Postman collection.

    This is the root class that contains all the information about
    a Postman collection, including its metadata, folders, requests,
    variables, events, and authentication configuration.

    Attributes:
        info (PostmanCollectionInfo): Collection metadata
        item (list[Union[PostmanRequest, PostmanFolder]]): Collection items (requests and folders)
        auth (Optional[PostmanAuth]): Collection-level authentication
        event (Optional[list[PostmanEvent]]): Collection-level events
        variable (Optional[list[PostmanVariable]]): Collection-level variables
        requests (list[PostmanRequest]): Flat list of all requests (computed property)
    """

    info: PostmanCollectionInfo
    item: list[PostmanRequest | PostmanFolder] = field(default_factory=list)
    auth: PostmanAuth | None = None
    event: list[PostmanEvent] | None = None
    variable: list[PostmanVariable] | None = None

    @property
    def requests(self) -> list[PostmanRequest]:
        """Get a flat list of all requests in the collection."""
        requests = []

        def extract_requests(items):
            for item in items:
                if isinstance(item, PostmanRequest):
                    requests.append(item)
                elif isinstance(item, PostmanFolder):
                    extract_requests(item.item)

        extract_requests(self.item)
        return requests

    @classmethod
    def from_dict(cls, obj: dict[str, Any], **kwargs) -> PostmanCollection:
        """Creates a PostmanCollection object from a JSON dictionary.

        This helper function converts a JSON representation of a Postman
        collection into a structured Python object with proper typing.

        Args:
            obj (dict[str, Any]): The JSON data as a Python dictionary
            **kwargs: Additional keyword arguments (unused)

        Returns:
            PostmanCollection: A structured representation of the collection
        """
        info = PostmanCollectionInfo.from_dict(obj["info"])

        # Process items (can be requests or folders)
        items = []
        for item_data in obj.get("item", []):
            if "request" in item_data:
                # It's a request
                items.append(PostmanRequest.from_dict(item_data))
            else:
                # It's a folder
                items.append(PostmanFolder.from_dict(item_data))

        # Handle collection-level auth
        auth = None
        if obj.get("auth"):
            auth = PostmanAuth.from_dict(obj["auth"])

        # Handle collection-level events
        events = None
        if obj.get("event"):
            events = [PostmanEvent.from_dict(e) for e in obj["event"]]

        # Handle collection-level variables
        variables = None
        if obj.get("variable"):
            variables = [PostmanVariable.from_dict(v) for v in obj["variable"]]

        instance = cls(
            info=info, item=items, auth=auth, event=events, variable=variables
        )
        object.__setattr__(instance, "_raw", obj)
        return instance

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation for validation."""
        result = {
            "info": self.info.to_dict(),
        }

        if self.item:
            result["item"] = [item.to_dict() for item in self.item]
        if self.auth:
            result["auth"] = self.auth.to_dict()
        if self.event:
            result["event"] = [e.to_dict() for e in self.event]
        if self.variable:
            result["variable"] = [v.to_dict() for v in self.variable]
        # _raw is excluded as per base class requirement
        return result

    @classmethod
    def from_file(cls, file_path: str) -> PostmanCollection:
        """Load a PostmanCollection from a JSON file.

        Args:
            file_path (str): Path to the Postman collection JSON file

        Returns:
            PostmanCollection: A structured representation of the collection

        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file isn't valid JSON
        """

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        return cls.from_dict(data)

    def list_all_headers(self) -> dict[str, list[str]]:
        """List all unique headers and their values from this collection.

        Returns:
            dict[str, list[str]]: Dictionary where keys are header names and values are lists of unique values
        """
        headers_dict = {}

        for request in self.requests:
            for header in request.header:
                if header.key not in headers_dict:
                    headers_dict[header.key] = set()
                headers_dict[header.key].add(header.value)

        # Convert sets to lists for better serialization
        return {key: list(values) for key, values in headers_dict.items()}

    def list_all_params(self) -> dict[str, list[str]]:
        """List all unique query parameters and their values from this collection.

        Returns:
            dict[str, list[str]]: Dictionary where keys are parameter names and values are lists of unique values
        """
        params_dict = {}

        for request in self.requests:
            if request.url.query:
                for param in request.url.query:
                    if param.key not in params_dict:
                        params_dict[param.key] = set()
                    params_dict[param.key].add(param.value)

        # Convert sets to lists for better serialization
        return {key: list(values) for key, values in params_dict.items()}
