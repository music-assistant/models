"""Models for MediaItem Metadata."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime

from mashumaro import DataClassDictMixin

from music_assistant_models.enums import ImageType, LinkType
from music_assistant_models.helpers import merge_lists
from music_assistant_models.unique_list import UniqueList


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

    def __hash__(self) -> int:
        """Return custom hash."""
        return hash((self.type.value, self.provider, self.path))

    def __eq__(self, other: object) -> bool:
        """Check equality of two items."""
        if not isinstance(other, MediaItemImage):
            return False
        return self.__hash__() == other.__hash__()


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
    review: str | None = None
    explicit: bool | None = None
    # NOTE: images is a list of available images, sorted by preference
    images: UniqueList[MediaItemImage] | None = None
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
        for fld in fields(self):
            new_val = getattr(new_values, fld.name)
            if new_val is None:
                continue
            cur_val = getattr(self, fld.name)
            if isinstance(cur_val, list) and isinstance(new_val, list):
                new_val = UniqueList(merge_lists(cur_val, new_val))
                setattr(self, fld.name, new_val)
            elif isinstance(cur_val, set) and isinstance(new_val, set | list | tuple):
                cur_val.update(new_val)
            elif new_val and fld.name in (
                "popularity",
                "last_refresh",
                "cache_checksum",
            ):
                # some fields are always allowed to be overwritten
                # (such as checksum and last_refresh)
                setattr(self, fld.name, new_val)
            elif cur_val is None:
                setattr(self, fld.name, new_val)
        return self

    def add_image(self, image: MediaItemImage) -> None:
        """Add an image to the list."""
        if not self.images:
            self.images = UniqueList()
        self.images.append(image)
