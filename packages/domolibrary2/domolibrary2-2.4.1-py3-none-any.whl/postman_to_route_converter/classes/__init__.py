"""Core Postman parsing library - generalized models and parsers."""

from __future__ import annotations

from .parsed_collection import ParsedPostmanCollection
from .parsed_request import ParsedPostmanRequest
from .postman import (
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
from .postman.exceptions import (
    CodeGenerationError,
    ConfigurationError,
    PostmanConversionError,
    PostmanParseError,
    RouteDiscoveryError,
    RouteMatchError,
    StagingError,
    ValidationError,
)

__all__ = [
    # Exceptions
    "PostmanConversionError",
    "PostmanParseError",
    "RouteDiscoveryError",
    "RouteMatchError",
    "CodeGenerationError",
    "StagingError",
    "ValidationError",
    "ConfigurationError",
    # Models
    "PostmanCollection",
    "PostmanFolder",
    "PostmanRequest",
    "PostmanRequest_Header",
    "PostmanQueryParam",
    "PostmanUrl",
    "PostmanVariable",
    "PostmanAuth",
    "PostmanScript",
    # Parsed classes
    "ParsedPostmanRequest",
    "ParsedPostmanCollection",
]
