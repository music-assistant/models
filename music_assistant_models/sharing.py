"""Public website links and metadata returned by item sharing."""

from __future__ import annotations

from dataclasses import dataclass, field

from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass(kw_only=True)
class ItemShareLink(DataClassORJSONMixin):
    """A server-approved provider website destination, independent of playback URLs."""

    provider_domain: str
    provider_instance: str
    url: str


@dataclass(kw_only=True)
class ItemShareInfo(DataClassORJSONMixin):
    """An item title with public destinations or human-readable fallback text."""

    title: str
    text: str | None = None
    links: list[ItemShareLink] = field(default_factory=list)
