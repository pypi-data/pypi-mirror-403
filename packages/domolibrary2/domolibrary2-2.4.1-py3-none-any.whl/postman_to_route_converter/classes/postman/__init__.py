"""Parse Postman collections into structured models."""

from __future__ import annotations

from ..url_extractor import URLPattern
from ._base import PostmanBase
from .postman_auth import PostmanAuth
from .postman_collection import PostmanCollection
from .postman_collection_info import PostmanCollectionInfo
from .postman_event import PostmanEvent
from .postman_folder import PostmanFolder
from .postman_query_param import PostmanQueryParam
from .postman_request import PostmanRequest
from .postman_request_body import PostmanRequest_Body
from .postman_request_header import PostmanRequest_Header
from .postman_response import PostmanResponse
from .postman_script import PostmanScript
from .postman_url import PostmanUrl
from .postman_variable import PostmanVariable

# Create convenience aliases for classmethods
extract_url_pattern = URLPattern.extract_url_pattern
normalize_url = URLPattern.normalize_url
extract_url_from_route_code = URLPattern.extract_url_from_route_code

__all__ = [
    # Base class
    "PostmanBase",
    # URL utilities
    "URLPattern",
    "extract_url_pattern",
    "normalize_url",
    "extract_url_from_route_code",
    # Models
    "PostmanAuth",
    "PostmanCollection",
    "PostmanCollectionInfo",
    "PostmanEvent",
    "PostmanFolder",
    "PostmanQueryParam",
    "PostmanRequest",
    "PostmanRequest_Body",
    "PostmanRequest_Header",
    "PostmanResponse",
    "PostmanScript",
    "PostmanUrl",
    "PostmanVariable",
]
