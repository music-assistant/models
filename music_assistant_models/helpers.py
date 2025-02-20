"""Generic Utility functions/helpers for the Music Assistant project."""

from __future__ import annotations

import asyncio
import base64
import re
from _collections_abc import dict_keys, dict_values
from asyncio import Task
from types import MethodType
from typing import Any
from unicodedata import combining, normalize
from uuid import UUID

from music_assistant_models.enums import MediaType

DO_NOT_SERIALIZE_TYPES = (MethodType, Task)


# global cache - we use this on a few places (as limited as possible)
# where we have no other options
_global_cache_lock = asyncio.Lock()
_global_cache: dict[str, Any] = {}


def get_global_cache_value(key: str, default: Any = None) -> Any:
    """Get a value from the global cache."""
    return _global_cache.get(key, default)


async def set_global_cache_values(values: dict[str, Any]) -> Any:
    """Set a value in the global cache (without locking)."""
    async with _global_cache_lock:
        for key, value in values.items():
            _set_global_cache_value(key, value)


def _set_global_cache_value(key: str, value: Any) -> Any:
    """Set a value in the global cache (without locking)."""
    _global_cache[key] = value


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


_LATIN = "ä  æ  ǽ  đ ð ƒ ħ ı ł ø ǿ ö  œ  ß  ŧ ü "  # noqa: RUF001
_ASCII = "ae ae ae d d f h i l o o oe oe ss t ue"
_OUTLIERS = str.maketrans(dict(zip(_LATIN.split(), _ASCII.split(), strict=False)))


def remove_diacritics(input_str: str) -> str:
    """Remove diacritics from string."""
    return "".join(
        c for c in normalize("NFD", input_str.lower().translate(_OUTLIERS)) if not combining(c)
    )


def create_sort_name(input_str: str) -> str:
    """Create (basic/simple) sort name/title from string."""
    input_str = remove_diacritics(input_str.lower().strip())
    while input_str.startswith(
        (",", ".", ":", "!", "?", "(", "[", "{", "<", ">", ")", "]", "}", "/", "`", "'", '"')
    ):
        input_str = input_str[1:]
    for item in ["the ", "de ", "les ", "dj ", "las ", "los ", "le ", "la ", "el ", "a ", "an "]:
        if input_str.startswith(item):
            input_str = input_str.replace(item, "", 1) + f", {item}"
            break
    return input_str.strip()


def is_valid_uuid(uuid_to_test: str) -> bool:
    """Check if uuid string is a valid UUID."""
    try:
        uuid_obj = UUID(uuid_to_test)
    except (ValueError, TypeError):
        return False
    return str(uuid_obj) == uuid_to_test


base62_length22_id_pattern = re.compile(r"^[a-zA-Z0-9]{22}$")


def valid_base62_length22(item_id: str) -> bool:
    """Validate Spotify style ID."""
    return bool(base62_length22_id_pattern.match(item_id))


def valid_id(provider: str, item_id: str) -> bool:
    """Validate Provider ID."""
    if provider == "spotify":
        return valid_base62_length22(item_id)
    return True


def create_uri(media_type: MediaType, provider_instance_id_or_domain: str, item_id: str) -> str:
    """Create Music Assistant URI from MediaItem values."""
    return f"{provider_instance_id_or_domain}://{media_type.value}/{item_id}"


def merge_lists(base: list[Any], new: list[Any]) -> list[Any]:
    """Merge 2 lists."""
    return [x for x in base if x not in new] + list(new)
