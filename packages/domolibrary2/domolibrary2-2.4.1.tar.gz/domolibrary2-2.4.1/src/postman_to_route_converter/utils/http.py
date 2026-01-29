"""HTTP utilities."""

from __future__ import annotations

from typing import Any

import requests


def gd_requests(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
    body: str | dict[str, Any] | None = None,
    debug_api: bool = False,
) -> requests.Response:
    """Wrapper around requests.request that handles authentication and common parameters.

    Args:
        method (str): HTTP method (GET, POST, etc.)
        url (str): The URL to make the request to
        headers (Optional[dict[str, str]]): Request headers
        params (Optional[dict[str, str]]): Query parameters
        body (Optional[Union[str, dict[str, Any]]]): Request body
        debug_api (bool): Whether to print debug information

    Returns:
        requests.Response: The response from the request
    """
    # Prepare request data
    data = body if isinstance(body, str) else None
    json_data = body if isinstance(body, dict) else None

    if debug_api:
        print(f"🚀 Making {method} request to {url}")
        print(f"Headers: {headers}")
        print(f"Params: {params}")
        print(f"Data: {data}")
        print(f"JSON: {json_data}")

    return requests.request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        data=data,
        json=json_data,
    )
