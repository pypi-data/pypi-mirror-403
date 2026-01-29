"""Utilities for detecting federated entities.

This module provides shared detection logic for determining whether
Domo entities (datasets, cards, etc.) are federated across instances.
"""

from __future__ import annotations

from typing import Any


def is_federated_dataset(obj: dict[str, Any]) -> bool:
    """Determine if a dataset JSON represents a federated (proxy) dataset.

    This heuristic checks multiple indicators in the API response to detect
    federation status. A dataset is considered federated if it has any
    federation-related metadata fields or if its type strings contain "FEDERAT".

    Args:
        obj: Dataset metadata dictionary from API response

    Returns:
        True if the dataset is federated, False otherwise

    Example:
        >>> raw = {"dataProviderType": "federated", "displayType": "federated"}
        >>> is_federated_dataset(raw)
        True
        >>> is_federated_dataset({"dataProviderType": "webform"})
        False
    """
    dpt = obj.get("dataProviderType", "").upper()
    disp = obj.get("displayType", "").upper()

    has_hint = any(
        [
            bool(obj.get("federation")),
            bool(obj.get("federationData")),
            bool(obj.get("federatedDatasetId")),
            bool(obj.get("publisherDomain")),
            obj.get("isFederated") is True,
        ]
    )

    has_federate = any(["FEDERAT" in dpt, "FEDERAT" in disp])
    return has_hint or has_federate
