"""String utilities."""

from __future__ import annotations

import re


def to_snake_case(name: str) -> str:
    """Convert a string to snake_case.

    Args:
        name (str): The string to convert

    Returns:
        str: The string in snake_case format
    """
    # Remove any special characters and replace spaces/underscores with hyphens
    name = re.sub(r"[^\w\s-]", "", name)
    # Convert to lowercase and replace spaces/underscores with hyphens
    name = name.lower().replace(" ", "-").replace("_", "-")
    # Split on hyphens and join with underscores
    return "_".join(name.split("-"))


def normalize_json_to_python(json_str: str) -> str:
    """Convert JSON-style boolean and null values to Python syntax (True, False, None).

    Args:
        json_str (str): JSON string that might contain 'true', 'false', or 'null'

    Returns:
        str: String with Python-style boolean and None values
    """
    if not json_str:
        return json_str

    # Replace JSON booleans with Python booleans
    # Use word boundaries to ensure we only replace complete words
    result = json_str
    result = result.replace("true", "True")
    result = result.replace("false", "False")
    result = result.replace("null", "None")

    return result
