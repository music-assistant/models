"""Utility functions for the music assistant models."""

from __future__ import annotations

import base64
from _collections_abc import dict_keys, dict_values
from asyncio import Task
from types import MethodType
from typing import Any
from uuid import UUID

DO_NOT_SERIALIZE_TYPES = (MethodType, Task)


def get_serializable_value(obj: Any, raise_unhandled: bool = False) -> Any:
    """Parse the value to its serializable equivalent."""
    if getattr(obj, "do_not_serialize", None):
        return None
    if (
        isinstance(obj, list | set | filter | tuple | dict_values | dict_keys | dict_values)
        or obj.__class__ == "dict_valueiterator"
    ):
        return [get_serializable_value(x) for x in obj]
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode("ascii")
    if isinstance(obj, DO_NOT_SERIALIZE_TYPES):
        return None
    if raise_unhandled:
        raise TypeError
    return obj


def create_sort_name(input_str: str) -> str:
    """Create (basic/simple) sort name/title from string."""
    input_str = input_str.lower().strip()
    for item in ["the ", "de ", "les ", "dj ", "las ", "los ", "le ", "la ", "el ", "a ", "an "]:
        if input_str.startswith(item):
            input_str = input_str.replace(item, "") + f", {item}"
    return input_str.strip()


def is_valid_uuid(uuid_to_test: str) -> bool:
    """Check if uuid string is a valid UUID."""
    try:
        uuid_obj = UUID(uuid_to_test)
    except (ValueError, TypeError):
        return False
    return str(uuid_obj) == uuid_to_test


def merge_dict(
    base_dict: dict[Any, Any],
    new_dict: dict[Any, Any],
    allow_overwite: bool = False,
) -> dict[Any, Any]:
    """Merge dict without overwriting existing values."""
    final_dict = base_dict.copy()
    for key, value in new_dict.items():
        if final_dict.get(key) and isinstance(value, dict):
            final_dict[key] = merge_dict(final_dict[key], value)
        if final_dict.get(key) and isinstance(value, tuple):
            final_dict[key] = merge_tuples(final_dict[key], value)
        if final_dict.get(key) and isinstance(value, list):
            final_dict[key] = merge_lists(final_dict[key], value)
        elif not final_dict.get(key) or allow_overwite:
            final_dict[key] = value
    return final_dict


def merge_tuples(base: tuple[Any, ...], new: tuple[Any, ...]) -> tuple[Any, ...]:
    """Merge 2 tuples."""
    return tuple(x for x in base if x not in new) + tuple(new)


def merge_lists(base: list[Any], new: list[Any]) -> list[Any]:
    """Merge 2 lists."""
    return [x for x in base if x not in new] + list(new)
