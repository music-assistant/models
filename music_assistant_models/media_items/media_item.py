"""Models and helpers for media items."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast

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
            available_providers = cast(set[str], available_providers)
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
    version: str = ""
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
    version: str = ""
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
class PlaylistTrack(Track):
    """
    Model for a track on a playlist.

    Same as regular Track but with explicit and required definition of position.
    """

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    position: int


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
    duration: int = 172800


@dataclass(kw_only=True)
class Audiobook(MediaItem):
    """Model for an Audiobook."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    publisher: str
    total_chapters: int
    authors: UniqueList[str] = field(default_factory=UniqueList)
    narrators: UniqueList[str] = field(default_factory=UniqueList)
    media_type: MediaType = MediaType.AUDIOBOOK


@dataclass(kw_only=True)
class Chapter(MediaItem):
    """Model for an Audiobook Chapter."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    position: int  # sort position / chapter number
    audiobook: Audiobook | ItemMapping
    duration: int = 0
    # resume point info
    fully_played: bool = False
    resume_position_ms: int = 0
    media_type: MediaType = MediaType.CHAPTER


@dataclass(kw_only=True)
class Podcast(MediaItem):
    """Model for a Podcast."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    publisher: str
    total_episodes: int
    media_type: MediaType = MediaType.PODCAST


@dataclass(kw_only=True)
class Episode(MediaItem):
    """Model for a Podcast Episode."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    position: int  # sort position / episode number
    name: str
    podcast: Podcast | ItemMapping
    duration: int = 0

    fully_played: bool = False
    resume_position_ms: int = 0

    media_type: MediaType = MediaType.EPISODE


@dataclass(kw_only=True)
class BrowseFolder(MediaItem):
    """Representation of a Folder used in Browse (which contains media items)."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    media_type: MediaType = MediaType.FOLDER
    # path: the path (in uri style) to/for this browse folder
    path: str = ""
    # label: a labelid that needs to be translated by the frontend
    label: str = ""
    provider_mappings: set[ProviderMapping] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Call after init."""
        super().__post_init__()
        if not self.path:
            self.path = f"{self.provider}://{self.item_id}"
        if not self.provider_mappings:
            self.provider_mappings.add(
                ProviderMapping(
                    item_id=self.item_id,
                    provider_domain=self.provider,
                    provider_instance=self.provider,
                )
            )
