"""Common/shared (serializable) Models (dataclassses) for Music Assistant."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, TypeGuard

from mashumaro import DataClassDictMixin

from music_assistant_models.enums import MediaType
from music_assistant_models.errors import InvalidDataError
from music_assistant_models.unique_list import UniqueList

from .audio_format import AudioFormat
from .media_item import (
    Album,
    Artist,
    Audiobook,
    BrowseFolder,
    Chapter,
    Episode,
    ItemMapping,
    MediaItem,
    Playlist,
    PlaylistTrack,
    Podcast,
    Radio,
    Track,
)
from .metadata import MediaItemImage, MediaItemLink, MediaItemMetadata
from .provider_mapping import ProviderMapping

__all__ = [
    "Album",
    "Audiobook",
    "Artist",
    "AudioFormat",
    "BrowseFolder",
    "Chapter",
    "ItemMapping",
    "Episode",
    "MediaItem",
    "MediaItemMetadata",
    "ProviderMapping",
    "Metadata",
    "MetadataProvider",
    "MetadataProviderType",
    "MetadataProviderStatus",
    "MediaItemLink",
    "MediaItemImage",
    "MediaItemMetadata",
    "Playlist",
    "PlaylistTrack",
    "Podcast",
    "Track",
    "Radio",
    "UniqueList",
]

MediaItemType = (
    Artist
    | Album
    | PlaylistTrack
    | Track
    | Radio
    | Playlist
    | Audiobook
    | Chapter
    | Podcast
    | Episode
    | BrowseFolder
)


@dataclass(kw_only=True)
class SearchResults(DataClassDictMixin):
    """Model for results from a search query."""

    artists: Sequence[Artist | ItemMapping] = field(default_factory=list)
    albums: Sequence[Album | ItemMapping] = field(default_factory=list)
    tracks: Sequence[Track | ItemMapping] = field(default_factory=list)
    playlists: Sequence[Playlist | ItemMapping] = field(default_factory=list)
    radio: Sequence[Radio | ItemMapping] = field(default_factory=list)
    audiobooks: Sequence[Audiobook | ItemMapping] = field(default_factory=list)
    podcasts: Sequence[Podcast | ItemMapping] = field(default_factory=list)


def media_from_dict(media_item: dict[str, Any]) -> MediaItemType | ItemMapping:
    """Return MediaItem from dict."""
    if "provider_mappings" not in media_item:
        return ItemMapping.from_dict(media_item)
    if media_item["media_type"] == "artist":
        return Artist.from_dict(media_item)
    if media_item["media_type"] == "album":
        return Album.from_dict(media_item)
    if media_item["media_type"] == "track":
        return Track.from_dict(media_item)
    if media_item["media_type"] == "playlist":
        return Playlist.from_dict(media_item)
    if media_item["media_type"] == "radio":
        return Radio.from_dict(media_item)
    if media_item["media_type"] == "audiobook":
        return Audiobook.from_dict(media_item)
    if media_item["media_type"] == "chapter":
        return Chapter.from_dict(media_item)
    if media_item["media_type"] == "podcast":
        return Podcast.from_dict(media_item)
    if media_item["media_type"] == "episode":
        return Episode.from_dict(media_item)
    raise InvalidDataError("Unknown media type")


def is_track(val: MediaItem) -> TypeGuard[Track]:
    """Return true if this MediaItem is a track."""
    return val.media_type == MediaType.TRACK
