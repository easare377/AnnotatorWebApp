"""Helpers shared by polygon-generation backends."""

from typing import Any


def convert_to_jsonable(value: Any) -> Any:
    """Recursively convert request objects into JSON-compatible values."""
    if isinstance(value, dict):
        return {
            key: convert_to_jsonable(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [convert_to_jsonable(item) for item in value]
    if hasattr(value, "__dict__"):
        return convert_to_jsonable(vars(value))
    return value
