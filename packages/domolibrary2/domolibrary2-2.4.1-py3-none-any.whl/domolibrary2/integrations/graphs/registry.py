"""Converter registry for graph export formats."""

from __future__ import annotations

__all__ = ["register_converter", "get_converter", "list_converters"]

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import GraphConverter

_CONVERTER_REGISTRY: dict[str, type[GraphConverter]] = {}


def register_converter(format_name: str):
    """Register a graph converter for a specific format.

    Usage:
        @register_converter("mermaid")
        class MermaidConverter(GraphConverter):
            ...

    Args:
        format_name: Unique identifier for the format (e.g., "mermaid", "neo4j")

    Returns:
        Decorator function
    """

    def decorator(cls: type[GraphConverter]) -> type[GraphConverter]:
        _CONVERTER_REGISTRY[format_name] = cls
        return cls

    return decorator


def get_converter(format_name: str) -> type[GraphConverter]:
    """Get converter class by format name.

    Args:
        format_name: Format identifier

    Returns:
        Converter class

    Raises:
        KeyError: If format not registered
    """
    if format_name not in _CONVERTER_REGISTRY:
        raise KeyError(
            f"Unknown converter format '{format_name}'. "
            f"Available formats: {list(_CONVERTER_REGISTRY.keys())}"
        )
    return _CONVERTER_REGISTRY[format_name]


def list_converters() -> list[str]:
    """List all registered converter formats.

    Returns:
        List of format names
    """
    return list(_CONVERTER_REGISTRY.keys())
