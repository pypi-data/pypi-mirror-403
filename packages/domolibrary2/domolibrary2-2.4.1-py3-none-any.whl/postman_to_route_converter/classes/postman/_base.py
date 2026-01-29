from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class PostmanBase(ABC):
    """Abstract base class for all Postman model classes.

    Provides a common interface for converting between dict and model representations,
    with support for preserving the original raw data.
    """

    def __post_init__(self):
        """Initialize _raw if not already set."""
        if not hasattr(self, "_raw"):
            object.__setattr__(self, "_raw", {})

    @classmethod
    @abstractmethod
    def from_dict(cls, obj: dict[str, Any], **kwargs) -> PostmanBase:
        """Create an instance from a dictionary.

        Args:
            obj (dict[str, Any]): The dictionary to create the instance from
            **kwargs: Additional keyword arguments for subclasses

        Returns:
            PostmanBase: A new instance of the class
        """
        pass

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation, excluding the _raw property.

        Subclasses should override this method to implement custom serialization
        logic while ensuring _raw is excluded.

        Returns:
            dict[str, Any]: Dictionary representation of the instance
        """
        result = asdict(self)
        result.pop("_raw", None)
        return result
