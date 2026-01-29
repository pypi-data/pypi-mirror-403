"""Parsed Postman request using composition pattern.

This module provides ParsedPostmanRequest which wraps a PostmanRequest
and provides parsed/interpreted attributes via property methods.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from .postman.postman_auth import PostmanAuth
from .postman.postman_request import PostmanRequest


@dataclass
class ParsedPostmanRequest:
    """Parsed Postman request with extracted metadata using composition.

    This class wraps a PostmanRequest instance and provides parsed/interpreted
    attributes via property methods that extract information from the underlying
    request object.

    Attributes:
        request: The composed PostmanRequest instance
        folder_path: Metadata about folder location (not from request)
        api_exploration_result: Optional API exploration data
        inferred_parameters: Optional inferred parameter types
        inferred_return_type: Optional inferred return type
    """

    request: PostmanRequest
    folder_path: str = ""
    api_exploration_result: Any | None = None
    inferred_parameters: list[Any] = field(default_factory=list)
    inferred_return_type: str = ""

    @property
    def name(self) -> str:
        """Get request name."""
        return self.request.name

    @property
    def method(self) -> str:
        """Get HTTP method."""
        return self.request.method or "GET"

    @property
    def url_pattern(self) -> str:
        """Get normalized URL pattern."""
        url_data = self.request.url.to_dict()
        return self.build_url_pattern(url_data)

    @property
    def path_variables(self) -> list[str]:
        """Extract path variables from URL."""
        path = self.request.url.path or []
        return self.extract_path_variables(path)

    @property
    def query_params(self) -> list[str]:
        """Extract query parameter names."""
        query = self.request.url.query or []
        if not query:
            return []
        # Handle PostmanQueryParam objects
        if hasattr(query[0], "to_dict"):
            query_dicts = [q.to_dict() for q in query]
        else:
            query_dicts = query
        return self.extract_query_params(query_dicts)

    @property
    def parsed_headers(self) -> dict[str, str]:
        """Convert header list to normalized dictionary."""
        header_list = self.request.header or []
        if not header_list:
            return {}
        # Convert PostmanRequest_Header objects to dicts
        header_dicts = [
            h.to_dict() if hasattr(h, "to_dict") else h for h in header_list
        ]
        return self.extract_headers(header_dicts)

    @property
    def body_schema(self) -> dict[str, Any] | None:
        """Parse request body into schema dictionary."""
        body_obj = self.request.body
        if not body_obj:
            return None
        if hasattr(body_obj, "to_dict"):
            body_data = body_obj.to_dict()
        elif isinstance(body_obj, dict):
            body_data = body_obj
        else:
            body_data = None
        return self.extract_body_schema(body_data)

    @property
    def auth(self) -> PostmanAuth | None:
        """Get authentication configuration for this request.

        Returns the request-level auth if present, otherwise None.
        In Postman, auth can be inherited from folder or collection level,
        but this property only returns request-level auth.

        Returns:
            PostmanAuth instance or None if no request-level auth configured
        """
        return self.request.auth

    @classmethod
    def extract_auth(cls, request: PostmanRequest) -> PostmanAuth | None:
        """Extract authentication configuration from a PostmanRequest.

        Args:
            request: PostmanRequest instance to extract auth from

        Returns:
            PostmanAuth instance or None if no auth configured
        """
        return request.auth

    @classmethod
    def build_url_pattern(cls, url_data: dict[str, Any]) -> str:
        """Build normalized URL pattern from Postman URL data.

        Postman format: {{baseUrl}}/data/v1/accounts
        where baseUrl = {{instanceUrl}}/api = https://{{instance}}.domo.com/api

        domolibrary format: https://{auth.domo_instance}.domo.com/api/data/v1/accounts

        We normalize both to: /api/data/v1/accounts for matching.

        Args:
            url_data: Dictionary containing URL components from PostmanRequest

        Returns:
            Normalized URL pattern string
        """
        raw_url = url_data.get("raw", "")
        if raw_url:
            # Handle Postman {{baseUrl}} variable
            # baseUrl = {{instanceUrl}}/api, so {{baseUrl}}/path becomes /api/path
            if "{{baseUrl}}" in raw_url:
                # Replace {{baseUrl}} with /api to align with domolibrary format
                raw_url = raw_url.replace("{{baseUrl}}", "/api")
            elif "{{instanceUrl}}" in raw_url:
                # instanceUrl = https://{{instance}}.domo.com, add /api if not present
                raw_url = raw_url.replace("{{instanceUrl}}", "")
                if not raw_url.startswith("/api"):
                    raw_url = "/api" + raw_url

            # Remove protocol and host if present (handle full URLs)
            if "://" in raw_url:
                # Extract just the path part after .domo.com
                parts = raw_url.split("://", 1)
                if len(parts) > 1:
                    # Find .domo.com and extract path after it
                    domo_part = parts[1]
                    if ".domo.com" in domo_part:
                        path_part = "/" + "/".join(
                            domo_part.split(".domo.com", 1)[1].split("/")[1:]
                        )
                        raw_url = path_part
                    else:
                        # Fallback: extract path after host
                        path_part = "/" + "/".join(domo_part.split("/")[1:])
                        raw_url = path_part

            # Normalize remaining Postman variables: {{var}} -> {var}, :var -> {var}
            raw_url = raw_url.replace("{{instance}}", "")
            raw_url = raw_url.replace("{{", "{").replace("}}", "}")
            # Convert :variable to {variable}
            raw_url = re.sub(r":(\w+)", r"{\1}", raw_url)

            # Ensure /api prefix for consistency with domolibrary format
            # (domolibrary always includes /api in the path)
            if not raw_url.startswith("/"):
                raw_url = "/" + raw_url

            # Clean up double slashes
            raw_url = re.sub(r"/+", "/", raw_url)
            return raw_url

        # Build from components (fallback when raw URL not available)
        protocol = url_data.get("protocol", "https")
        host = url_data.get("host", [])
        path = url_data.get("path", [])
        query = url_data.get("query", [])

        if isinstance(host, list):
            host_str = ".".join(host)
        else:
            host_str = str(host)

        # Build path, converting :variable to {variable}
        path_parts = []
        for p in path:
            p_str = str(p)
            # Convert :variable to {variable}
            if p_str.startswith(":"):
                path_parts.append("{" + p_str[1:] + "}")
            else:
                path_parts.append(p_str)

        path_str = "/" + "/".join(path_parts)

        # If host contains {{baseUrl}}, add /api prefix
        # Postman baseUrl = {{instanceUrl}}/api, so paths should include /api
        if "{{baseUrl}}" in str(host) or "baseUrl" in str(host).lower():
            if not path_str.startswith("/api"):
                path_str = "/api" + path_str

        if query:
            query_str = "?" + "&".join(
                f"{q.get('key', '')}={q.get('value', '')}" for q in query
            )
        else:
            query_str = ""

        full_url = f"{path_str}{query_str}"

        # Clean up double slashes
        full_url = re.sub(r"/+", "/", full_url)
        return full_url

    @classmethod
    def extract_path_variables(cls, url_path: list[str]) -> list[str]:
        """Extract path variables from URL path segments.

        Args:
            url_path: List of URL path segments

        Returns:
            List of extracted variable names
        """
        variables = []
        for segment in url_path:
            if segment.startswith(":") or (
                segment.startswith("{{") and segment.endswith("}}")
            ):
                var_name = segment.lstrip(":").strip("{}")
                variables.append(var_name)
        return variables

    @classmethod
    def extract_query_params(cls, url_query: list[dict[str, Any]]) -> list[str]:
        """Extract query parameter names.

        Args:
            url_query: List of query parameter dictionaries

        Returns:
            List of query parameter keys
        """
        return [param.get("key", "") for param in url_query if param.get("key")]

    @classmethod
    def extract_headers(cls, request_headers: list[dict[str, Any]]) -> dict[str, str]:
        """Extract headers from request.

        Args:
            request_headers: List of header dictionaries

        Returns:
            Dictionary mapping lowercase header keys to values
        """
        headers = {}
        for header in request_headers:
            key = header.get("key", "")
            value = header.get("value", "")
            if key:
                headers[key.lower()] = value
        return headers

    @classmethod
    def extract_body_schema(
        cls, request_body: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Extract body schema from request.

        Args:
            request_body: Dictionary containing request body data

        Returns:
            Parsed body schema dictionary or None
        """
        if not request_body:
            return None

        mode = request_body.get("mode", "")
        if mode == "raw":
            raw = request_body.get("raw", "")
            if raw:
                try:
                    return json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    return {"raw": raw}
        elif mode == "formdata" or mode == "urlencoded":
            return {"mode": mode, "data": request_body.get(mode, [])}

        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "method": self.method,
            "url_pattern": self.url_pattern,
            "path_variables": self.path_variables,
            "query_params": self.query_params,
            "headers": self.headers,
            "body_schema": self.body_schema,
            "folder_path": self.folder_path,
        }
