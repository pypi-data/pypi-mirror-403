"""Generalized Postman collection parsing library.

This library provides tools to parse Postman JSON collections into structured
Python models. It is framework-agnostic and can be used with any Python project.

Example usage:
    ```python
    from postman import parse_postman_collection, ParsedPostmanCollection

    # Parse a Postman collection
    parsed = parse_postman_collection("collection.json")

    # Access parsed requests
    for request in parsed.requests:
        print(f"{request.method} {request.url}")
    ```
"""

from __future__ import annotations

from .models import (
    ParsedPostmanCollection,
    ParsedPostmanRequest,
    PostmanAuth,
    PostmanCollection,
    PostmanFolder,
    PostmanQueryParam,
    PostmanRequest,
    PostmanRequest_Header,
    PostmanScript,
    PostmanUrl,
    PostmanVariable,
)
from .parsing import parse_postman_collection

__all__ = [
    # Main parsing function
    "parse_postman_collection",
    # Parsed models
    "ParsedPostmanCollection",
    "ParsedPostmanRequest",
    # Postman models
    "PostmanCollection",
    "PostmanFolder",
    "PostmanRequest",
    "PostmanRequest_Header",
    "PostmanQueryParam",
    "PostmanUrl",
    "PostmanVariable",
    "PostmanAuth",
    "PostmanScript",
]
