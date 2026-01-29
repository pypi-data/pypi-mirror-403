"""Parsed Postman collection using composition pattern.

This module provides ParsedPostmanCollection which wraps a PostmanCollection
and provides parsed/interpreted attributes via property methods.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .parsed_request import ParsedPostmanRequest
from .postman.postman_collection import PostmanCollection
from .postman.postman_folder import PostmanFolder
from .postman.postman_request import PostmanRequest


@dataclass
class ParsedPostmanCollection:
    """Parsed Postman collection with structured metadata using composition.

    This class wraps a PostmanCollection instance and provides parsed/interpreted
    attributes via property methods. It lazily parses requests on first access.

    Attributes:
        collection: The composed PostmanCollection instance
        base_url: Extracted base URL (can be set during initialization)
        folder_structure: Folder hierarchy mapping folder paths to request names
        _parsed_requests: Cached list of parsed requests (lazy-loaded)
    """

    collection: PostmanCollection
    base_url: str = ""
    folder_structure: dict[str, list[str]] = field(default_factory=dict)
    _parsed_requests: list[ParsedPostmanRequest] | None = None

    def __post_init__(self) -> None:
        """Initialize folder structure after object creation."""
        if not self.base_url:
            self.base_url = self.extract_base_url(self.collection)
        self.folder_structure = self.build_folder_structure(self.collection)

    @property
    def variables(self) -> dict[str, str]:
        """Extract variables from collection."""
        if not self.collection.variable:
            return {}
        return {var.key: var.value for var in self.collection.variable}

    @property
    def requests(self) -> list[ParsedPostmanRequest]:
        """Get all parsed requests in the collection (lazy-loaded)."""
        if self._parsed_requests is None:
            self._parsed_requests = self.parse_all_requests(self.collection)
        return self._parsed_requests

    @classmethod
    def extract_base_url(cls, collection: PostmanCollection) -> str:
        """Extract base URL from collection variables.

        Args:
            collection: PostmanCollection instance

        Returns:
            Base URL string or empty string if not found
        """
        for var in collection.variable or []:
            if var.key == "baseUrl" or var.key == "instance":
                return var.value or ""
        return ""

    @classmethod
    def build_folder_structure(
        cls, collection: PostmanCollection
    ) -> dict[str, list[str]]:
        """Build folder structure by traversing collection items.

        Args:
            collection: PostmanCollection instance

        Returns:
            Dictionary mapping folder paths to lists of request names
        """
        folder_structure: dict[str, list[str]] = {}
        cls.traverse_items(collection.item, "", folder_structure)
        return folder_structure

    @classmethod
    def traverse_items(
        cls,
        items: list[PostmanRequest | PostmanFolder],
        parent_path: str,
        folder_structure: dict[str, list[str]],
    ) -> None:
        """Recursively traverse collection items to build folder structure.

        Args:
            items: List of collection items (requests or folders)
            parent_path: Current parent folder path
            folder_structure: Dictionary to populate with folder structure
        """
        for item in items:
            if isinstance(item, PostmanRequest):
                # Track request in folder structure
                if parent_path:
                    if parent_path not in folder_structure:
                        folder_structure[parent_path] = []
                    folder_structure[parent_path].append(item.name)
            elif isinstance(item, PostmanFolder):
                # Process folder
                folder_name = item.name
                new_folder_path = (
                    f"{parent_path}/{folder_name}" if parent_path else folder_name
                )
                if item.item:
                    cls.traverse_items(item.item, new_folder_path, folder_structure)

    @classmethod
    def parse_all_requests(
        cls, collection: PostmanCollection
    ) -> list[ParsedPostmanRequest]:
        """Parse all requests in the collection.

        Args:
            collection: PostmanCollection instance

        Returns:
            List of ParsedPostmanRequest instances
        """
        parsed_requests: list[ParsedPostmanRequest] = []
        cls.parse_items(collection.item, "", parsed_requests)
        return parsed_requests

    @classmethod
    def parse_items(
        cls,
        items: list[PostmanRequest | PostmanFolder],
        folder_path: str,
        parsed_requests: list[ParsedPostmanRequest],
    ) -> None:
        """Recursively parse collection items into ParsedPostmanRequest instances.

        Args:
            items: List of collection items (requests or folders)
            folder_path: Current folder path
            parsed_requests: List to append parsed requests to
        """
        for item in items:
            if isinstance(item, PostmanRequest):
                # Create parsed request with folder path
                parsed_request = ParsedPostmanRequest(
                    request=item, folder_path=folder_path
                )
                parsed_requests.append(parsed_request)
            elif isinstance(item, PostmanFolder):
                # Process folder
                folder_name = item.name
                new_folder_path = (
                    f"{folder_path}/{folder_name}" if folder_path else folder_name
                )
                if item.item:
                    cls.parse_items(item.item, new_folder_path, parsed_requests)

    def get_requests_by_folder(self, folder_path: str) -> list[ParsedPostmanRequest]:
        """Get all requests in a specific folder."""
        return [req for req in self.requests if req.folder_path == folder_path]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "collection_name": self.collection.info.name,
            "total_requests": len(self.requests),
            "folder_structure": self.folder_structure,
            "variables": self.variables,
            "base_url": self.base_url,
            "requests": [req.to_dict() for req in self.requests],
        }
