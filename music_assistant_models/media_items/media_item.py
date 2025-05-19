"""Models and helpers for media items."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

from mashumaro import DataClassDictMixin

from music_assistant_models.enums import AlbumType, ExternalID, ImageType, MediaType
from music_assistant_models.errors import InvalidDataError
from music_assistant_models.helpers import (
    create_sort_name,
    create_uri,
    get_global_cache_value,
    is_valid_uuid,
)
from music_assistant_models.unique_list import UniqueList

from .metadata import MediaItemImage, MediaItemMetadata
from .provider_mapping import ProviderMapping


@dataclass(kw_only=True)
class _MediaItemBase(DataClassDictMixin):
    """Base representation of a Media Item or ItemMapping item object."""

    item_id: str
    provider: str  # provider instance id or provider domain
    name: str
    version: str = ""
    # sort_name will be auto generated if omitted
    sort_name: str | None = None
    # uri is auto generated, do not override unless really needed
    uri: str | None = None
    external_ids: set[tuple[ExternalID, str]] = field(default_factory=set)
    # is_playable: if the item is playable (can be used in play_media command)
    is_playable: bool = True
    # translation_key:
    # an optional translation key identifier for the frontend (to use instead of name)
    translation_key: str | None = None
    media_type: MediaType = MediaType.UNKNOWN

    def __post_init__(self) -> None:
        """Call after init."""
        if self.uri is None:
            self.uri = create_uri(self.media_type, self.provider, self.item_id)
        if self.sort_name is None:
            self.sort_name = create_sort_name(self.name)

    def get_external_id(self, external_id_type: ExternalID) -> str | None:
        """Get (the first instance) of given External ID or None if not found."""
        for ext_id in self.external_ids:
            if ext_id[0] != external_id_type:
                continue
            return ext_id[1]
        return None

    def add_external_id(self, external_id_type: ExternalID, value: str) -> None:
        """Add ExternalID."""
        if external_id_type.is_musicbrainz and not is_valid_uuid(value):
            msg = f"Invalid MusicBrainz identifier: {value}"
            raise InvalidDataError(msg)
        if external_id_type.is_unique and (
            existing := next((x for x in self.external_ids if x[0] == external_id_type), None)
        ):
            self.external_ids.remove(existing)
        self.external_ids.add((external_id_type, value))

    @property
    def mbid(self) -> str | None:
        """Return MusicBrainz ID."""
        if self.media_type == MediaType.ARTIST:
            return self.get_external_id(ExternalID.MB_ARTIST)
        if self.media_type == MediaType.ALBUM:
            return self.get_external_id(ExternalID.MB_ALBUM)
        if self.media_type == MediaType.TRACK:
            return self.get_external_id(ExternalID.MB_RECORDING)
        return None

    @mbid.setter
    def mbid(self, value: str) -> None:
        """Set MusicBrainz External ID."""
        if self.media_type == MediaType.ARTIST:
            self.add_external_id(ExternalID.MB_ARTIST, value)
        elif self.media_type == MediaType.ALBUM:
            self.add_external_id(ExternalID.MB_ALBUM, value)
        elif self.media_type == MediaType.TRACK:
            # NOTE: for tracks we use the recording id to
            # differentiate a unique recording
            # and not the track id (as that is just the reference
            #  of the recording on a specific album)
            self.add_external_id(ExternalID.MB_RECORDING, value)
            return

    def __hash__(self) -> int:
        """Return custom hash."""
        return hash(self.uri)

    def __eq__(self, other: object) -> bool:
        """Check equality of two items."""
        if not isinstance(other, MediaItem | ItemMapping):
            return False
        return self.uri == other.uri


@dataclass(kw_only=True)
class MediaItem(_MediaItemBase):
    """Base representation of a media item."""

    __eq__ = _MediaItemBase.__eq__

    provider_mappings: set[ProviderMapping]
    # optional fields below
    metadata: MediaItemMetadata = field(default_factory=MediaItemMetadata)
    favorite: bool = False
    position: int | None = None  # required for playlist tracks, optional for all other

    def __hash__(self) -> int:
        """Return hash of MediaItem."""
        return super().__hash__()

    @property
    def available(self) -> bool:
        """Return (calculated) availability."""
        if not (available_providers := get_global_cache_value("unique_providers")):
            # this is probably the client
            return any(x.available for x in self.provider_mappings)
        if TYPE_CHECKING:
            available_providers = cast("set[str]", available_providers)
        for x in self.provider_mappings:
            if available_providers.intersection({x.provider_domain, x.provider_instance}):
                return True
        return False

    @property
    def image(self) -> MediaItemImage | None:
        """Return (first/random) image/thumb from metadata (if any)."""
        if self.metadata is None or self.metadata.images is None:
            return None
        return next((x for x in self.metadata.images if x.type == ImageType.THUMB), None)


@dataclass(kw_only=True)
class ItemMapping(_MediaItemBase):
    """Representation of a minimized item object."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    available: bool = True
    image: MediaItemImage | None = None

    @classmethod
    def from_item(cls, item: MediaItem | ItemMapping) -> ItemMapping:
        """Create ItemMapping object from regular item."""
        if isinstance(item, ItemMapping):
            return item
        thumb_image = None
        if item.metadata and item.metadata.images:
            for img in item.metadata.images:
                if img.type != ImageType.THUMB:
                    continue
                thumb_image = img
                break
        return cls.from_dict(
            {**item.to_dict(), "image": thumb_image.to_dict() if thumb_image else None}
        )


@dataclass(kw_only=True)
class Artist(MediaItem):
    """Model for an artist."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    media_type: MediaType = MediaType.ARTIST


@dataclass(kw_only=True)
class Album(MediaItem):
    """Model for an album."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    media_type: MediaType = MediaType.ALBUM
    year: int | None = None
    artists: UniqueList[Artist | ItemMapping] = field(default_factory=UniqueList)
    album_type: AlbumType = AlbumType.UNKNOWN

    @property
    def artist_str(self) -> str:
        """Return (combined) artist string for track."""
        return "/".join(x.name for x in self.artists)


@dataclass(kw_only=True)
class Track(MediaItem):
    """Model for a track."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    media_type: MediaType = MediaType.TRACK
    duration: int = 0
    artists: UniqueList[Artist | ItemMapping] = field(default_factory=UniqueList)
    album: Album | ItemMapping | None = None  # required for album tracks
    disc_number: int = 0  # required for album tracks
    track_number: int = 0  # required for album tracks

    @property
    def image(self) -> MediaItemImage | None:
        """Return (first) image from metadata (prefer album)."""
        if isinstance(self.album, Album) and self.album.image:
            return self.album.image
        return super().image

    @property
    def artist_str(self) -> str:
        """Return (combined) artist string for track."""
        return "/".join(x.name for x in self.artists)


@dataclass(kw_only=True)
class Playlist(MediaItem):
    """Model for a playlist."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    media_type: MediaType = MediaType.PLAYLIST
    owner: str = ""
    is_editable: bool = False

    # cache_checksum: optional value to (in)validate cache
    # detect changes to the playlist tracks listing
    cache_checksum: str | None = None


@dataclass(kw_only=True)
class Radio(MediaItem):
    """Model for a radio station."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    media_type: MediaType = MediaType.RADIO
    duration: int | None = None

    def __post_serialize__(self, d: dict[str, Any]) -> dict[str, Any]:
        """Adjust dict object after it has been serialized."""
        # TEMP 2025-03-14: convert None duration to fake number for backwards compatibility
        d["duration"] = 0 if d["duration"] is None else d["duration"]
        return d


@dataclass(kw_only=True)
class Audiobook(MediaItem):
    """Model for an Audiobook."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    publisher: str | None = None
    authors: UniqueList[str] = field(default_factory=UniqueList)
    narrators: UniqueList[str] = field(default_factory=UniqueList)
    duration: int = 0
    # resume point info
    # set to None if unknown/unsupported by provider
    # which will let MA fallback to an internal resume point
    fully_played: bool | None = None
    resume_position_ms: int | None = None

    media_type: MediaType = MediaType.AUDIOBOOK


@dataclass(kw_only=True)
class Podcast(MediaItem):
    """Model for a Podcast."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    publisher: str | None = None
    total_episodes: int | None = None
    media_type: MediaType = MediaType.PODCAST


@dataclass(kw_only=True)
class PodcastEpisode(MediaItem):
    """Model for a Podcast Episode."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    position: int  # sort position / episode number (set to 0 if unknown)
    podcast: Podcast | ItemMapping
    duration: int = 0

    # resume point info
    # set to None if unknown/unsupported by provider
    # which will let MA fallback to an internal resume point
    fully_played: bool | None = None
    resume_position_ms: int | None = None

    media_type: MediaType = MediaType.PODCAST_EPISODE


@dataclass(kw_only=True)
class BrowseFolder(_MediaItemBase):
    """Representation of a Folder used in Browse (which contains media items)."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    # mediatype is always folder for browse folders
    # independent of the actual content mediatype(s)
    media_type: MediaType = MediaType.FOLDER

    # path: the path (in uri style) to/for this browse folder
    path: str = ""
    image: MediaItemImage | None = None
    is_playable: bool = False

    def __post_init__(self) -> None:
        """Call after init."""
        super().__post_init__()
        if not self.path:
            self.path = f"{self.provider}://{self.item_id}"


@dataclass(kw_only=True)
class RecommendationFolder(BrowseFolder):
    """Representation of a Recommendation folder."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    # mediatype is always folder for recommendation folders
    # independent of the actual content mediatype(s)
    media_type: MediaType = MediaType.FOLDER

    is_playable: bool = False
    icon: str | None = None  # optional material design icon name
    items: UniqueList[MediaItemType | ItemMapping | BrowseFolder] = field(
        default_factory=UniqueList
    )
    subtitle: str | None = None  # optional subtitle for the recommendation


# some type aliases
# NOTE: BrowseFolder is not part of the MediaItemType alias, as it lacks
# provider mappings, i.e. we do not map a provider item to a BrowseFolder.
MediaItemType = Artist | Album | Track | Radio | Playlist | Audiobook | Podcast | PodcastEpisode
PlayableMediaItemType = Track | Radio | Audiobook | PodcastEpisode
