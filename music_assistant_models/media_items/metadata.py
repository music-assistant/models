"""Models for MediaItem Metadata."""

from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any

from mashumaro import DataClassDictMixin

from music_assistant_models.enums import ImageType, LinkType
from music_assistant_models.helpers import merge_lists
from music_assistant_models.unique_list import UniqueList

# ContextVar set by the Music Assistant server during outbound API serialization.
# When set, MediaItemImage.__post_serialize__ uses the resolver to fill `proxy_id`
# on the serialized dict, so clients can build the imageproxy URL by appending
# the id to their own connection's base URL — no need to construct the long
# legacy `/imageproxy?provider=…&path=…` form themselves. The resolver receives
# (provider, path) and must return an opaque, server-defined image id that is
# safe to embed directly as a single URL path segment (URL-safe, no `/`, `?`,
# `#`, or whitespace), so clients can build `<api_base>/imageproxy/<proxy_id>`
# without any extra escaping.
IMAGE_PROXY_ID_RESOLVER: ContextVar[Callable[[str, str], str] | None] = ContextVar(
    "image_proxy_id_resolver", default=None
)


@dataclass(frozen=True, kw_only=True)
class MediaItemLink(DataClassDictMixin):
    """Model for a link."""

    type: LinkType
    url: str

    def __hash__(self) -> int:
        """Return custom hash."""
        return hash(self.type)

    def __eq__(self, other: object) -> bool:
        """Check equality of two items."""
        if not isinstance(other, MediaItemLink):
            return False
        return self.url == other.url


@dataclass(frozen=True, kw_only=True)
class MediaItemImage(DataClassDictMixin):
    """Model for a image."""

    type: ImageType
    path: str
    provider: str  # provider lookup key (only use instance id for fileproviders)
    remotely_accessible: bool = False  # url that is accessible from anywhere
    # Opaque server-side imageproxy id. Populated only by the MA server during
    # outbound API serialization (via __post_serialize__ + IMAGE_PROXY_ID_RESOLVER).
    # Clients fetch the image at `<api_base>/imageproxy/<proxy_id>?size=...&fmt=...`.
    proxy_id: str | None = None

    def __hash__(self) -> int:
        """Return custom hash."""
        return hash((self.type.value, self.provider, self.path))

    def __eq__(self, other: object) -> bool:
        """Check equality of two items."""
        if not isinstance(other, MediaItemImage):
            return False
        return self.__hash__() == other.__hash__()

    def __post_serialize__(self, d: dict[str, Any]) -> dict[str, Any]:
        """Inject `proxy_id` when a resolver is set on the current context."""
        if self.remotely_accessible:
            return d
        # only inject when proxy_id was not already provided so that values
        # round-tripped via from_dict (or set explicitly by the caller) survive
        if d.get("proxy_id") is not None:
            return d
        resolver = IMAGE_PROXY_ID_RESOLVER.get()
        if resolver is not None:
            d["proxy_id"] = resolver(self.provider, self.path)
        return d


@dataclass(frozen=True, kw_only=True)
class MediaItemPalette(DataClassDictMixin):
    """Color palette derived from a MediaItem's artwork. Mirrors the Sendspin color@v1 spec."""

    background_dark: tuple[int, int, int] | None = None
    background_light: tuple[int, int, int] | None = None
    primary: tuple[int, int, int] | None = None
    accent: tuple[int, int, int] | None = None
    on_dark: tuple[int, int, int] | None = None
    on_light: tuple[int, int, int] | None = None


@dataclass(frozen=True, kw_only=True)
class MediaItemChapter(DataClassDictMixin):
    """Model for a MediaItem's chapter/bookmark."""

    position: int  # sort position/number
    name: str  # friendly name
    start: float  # start position in seconds
    end: float | None = None  # start position in seconds if known

    @property
    def duration(self) -> float:
        """Return duration of chapter."""
        return self.end - self.start if self.end else 0

    def __hash__(self) -> int:
        """Return custom hash."""
        return hash(self.position)


@dataclass(kw_only=True)
class MediaItemMetadata(DataClassDictMixin):
    """Model for a MediaItem's metadata."""

    description: str | None = None
    # ISO 639-1 language code for `description`
    description_language: str | None = None
    review: str | None = None
    explicit: bool | None = None
    # NOTE: images is a list of available images, sorted by preference
    images: UniqueList[MediaItemImage] | None = None
    grouping: str | None = None
    genres: set[str] | None = None
    mood: str | None = None
    style: str | None = None
    copyright: str | None = None
    lyrics: str | None = None  # tracks only
    lrc_lyrics: str | None = None  # tracks only
    label: str | None = None
    links: set[MediaItemLink] | None = None
    performers: set[str] | None = None
    preview: str | None = None
    popularity: int | None = None
    release_date: datetime | None = None
    languages: UniqueList[str] | None = None
    # chapters is a list of available chapters, sorted by position
    # most commonly used for audiobooks and podcast episodes
    chapters: list[MediaItemChapter] | None = None
    # last_refresh: timestamp the (full) metadata was last collected
    last_refresh: int | None = None

    def update(
        self,
        new_values: MediaItemMetadata,
    ) -> MediaItemMetadata:
        """Update metadata (in-place) with new values."""
        if not new_values:
            return self
        # description paired with description_language: overwrite on language change,
        # otherwise fill-the-gap (preserves higher-priority provider's bio)
        if new_values.description is not None:
            new_lang = new_values.description_language
            lang_changed = new_lang is not None and new_lang != self.description_language
            if lang_changed or self.description is None:
                self.description = new_values.description
                self.description_language = new_lang
        for fld in fields(self):
            if fld.name in ("description", "description_language"):
                continue
            new_val = getattr(new_values, fld.name)
            if new_val is None:
                continue
            cur_val = getattr(self, fld.name)
            if isinstance(cur_val, list) and isinstance(new_val, list):
                new_val = UniqueList(merge_lists(cur_val, new_val))
                setattr(self, fld.name, new_val)
            elif isinstance(cur_val, set) and isinstance(new_val, set | list | tuple):
                cur_val.update(new_val)
            # some fields are always allowed to be overwritten
            # (such as popularity and last_refresh)
            elif (
                new_val
                and fld.name
                in (
                    "popularity",
                    "last_refresh",
                )
            ) or cur_val is None:
                setattr(self, fld.name, new_val)
        return self

    def add_image(self, image: MediaItemImage) -> None:
        """Add an image to the list."""
        if not self.images:
            self.images = UniqueList()
        self.images.append(image)
