"""Parsing module for Postman collections.

This module provides the main entry point for parsing Postman collections
into structured models.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import ParsedPostmanCollection, PostmanCollection, PostmanParseError

__all__ = ["parse_postman_collection"]


def parse_postman_collection(
    collection_path: str | Path,
    base_url: str | None = None,
) -> ParsedPostmanCollection:
    """Parse a Postman collection JSON file into a structured format.

    Args:
        collection_path: Path to Postman collection JSON file
        base_url: Optional base URL to use (if not provided, extracted from collection variables)

    Returns:
        ParsedPostmanCollection with extracted metadata

    Raises:
        PostmanParseError: If collection file cannot be read or parsed
        FileNotFoundError: If collection file doesn't exist
    """
    path = Path(collection_path)
    if not path.exists():
        raise FileNotFoundError(f"Collection file not found: {collection_path}")

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise PostmanParseError(f"Invalid JSON in collection file: {e}") from e
    except Exception as e:
        raise PostmanParseError(f"Error reading collection file: {e}") from e

    # Parse using PostmanCollection model
    try:
        collection = PostmanCollection.from_dict(data)
    except Exception as e:
        raise PostmanParseError(
            f"Error parsing Postman collection structure: {e}"
        ) from e

    # Extract base URL from variables if not provided
    if not base_url:
        for var in collection.variable or []:
            if var.key == "baseUrl" or var.key == "instance":
                base_url = var.value or ""
                break

    # Create parsed collection
    parsed = ParsedPostmanCollection(
        collection=collection,
        base_url=base_url or "",
    )

    return parsed
