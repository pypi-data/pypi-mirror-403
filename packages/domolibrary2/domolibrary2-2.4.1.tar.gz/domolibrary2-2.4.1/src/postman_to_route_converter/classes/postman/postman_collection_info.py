from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._base import PostmanBase


@dataclass
class PostmanCollectionInfo(PostmanBase):
    """Contains metadata about the Postman collection.

    Attributes:
        _postman_id (str): Unique identifier for the collection
        name (str): Name of the collection
        schema (str): The schema version used by the collection
        _exporter_id (str): ID of the exporter that created the collection
        _collection_link (str): Link to the collection in Postman
        description (str): Collection description
    """

    _postman_id: str
    name: str
    schema: str
    _exporter_id: str | None = None
    _collection_link: str | None = None
    description: str | None = None

    @classmethod
    def from_dict(cls, obj: dict[str, Any], **kwargs) -> PostmanCollectionInfo:
        """Create a PostmanCollectionInfo from info data.

        Args:
            obj (dict[str, Any]): Dictionary containing collection info
            **kwargs: Additional keyword arguments (unused)

        Returns:
            PostmanCollectionInfo: A new info instance
        """
        instance = cls(
            _postman_id=obj["_postman_id"],
            name=obj["name"],
            schema=obj["schema"],
            _exporter_id=obj.get("_exporter_id"),
            _collection_link=obj.get("_collection_link"),
            description=obj.get("description"),
        )
        object.__setattr__(instance, "_raw", obj)
        return instance

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "_postman_id": self._postman_id,
            "name": self.name,
            "schema": self.schema,
        }

        if self._exporter_id:
            result["_exporter_id"] = self._exporter_id
        if self._collection_link:
            result["_collection_link"] = self._collection_link
        if self.description:
            result["description"] = self.description
        # _raw is excluded as per base class requirement
        return result
