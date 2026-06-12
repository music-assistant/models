"""Models and helpers for media items."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, cast

from mashumaro import DataClassDictMixin, field_options

from music_assistant_models.enums import AlbumType, ArtistType, ExternalID, ImageType, MediaType
from music_assistant_models.errors import InvalidDataError
from music_assistant_models.helpers import (
    create_sort_name,
    create_uri,
    get_global_cache_value,
    is_valid_uuid,
    remove_diacritics,
)
from music_assistant_models.translations import resolve_translation, translations_active
from music_assistant_models.unique_list import UniqueList

from .metadata import MediaItemImage, MediaItemMetadata
from .provider_mapping import ProviderMapping


@dataclass(kw_only=True)
class _MediaItemBase(DataClassDictMixin):
    """Base representation of a Media Item or ItemMapping item object."""

    item_id: str
    provider: str  # provider instance id or provider domain
    # name: the (English) display name; always set. For localizable items also set a
    # translation_key, which overrides `name` for the connection locale at serialization.
    name: str
    version: str = ""
    # sort_name will be auto generated if omitted
    sort_name: str | None = None
    # uri is auto generated, do not override unless really needed
    uri: str | None = None
    external_ids: set[tuple[ExternalID, str]] = field(default_factory=set)
    # is_playable: if the item is playable (can be used in play_media command)
    is_playable: bool = True
    # translation_key: optional key to localize `name` (e.g. for "Your Mixes"); resolved to the
    # connection locale at serialization, overriding the in-code `name`.
    translation_key: str | None = None
    # translation_params: optional positional arguments for {0}/{1} placeholders in the
    # translated string (e.g. "Liked Songs {0}").
    translation_params: list[str] | None = None
    media_type: MediaType = MediaType.UNKNOWN

    def __post_init__(self) -> None:
        """Call after init."""
        if self.uri is None:
            self.uri = create_uri(self.media_type, self.provider, self.item_id)
        if self.sort_name is None:
            self.sort_name = create_sort_name(self.name)

    def _translation_base(self) -> str | None:
        """Return the translation key base for this item's translation_key (None if unset)."""
        if self.translation_key is None:
            return None
        key = self.translation_key
        return key if key.startswith(("provider.", "core.", "common.")) else f"media.{key}"

    def __post_serialize__(self, d: dict[str, Any]) -> dict[str, Any]:
        """Localize the display name (and subtitle) when a translation resolver is set."""
        self._resolve_translation(d)
        return d

    def _resolve_translation(self, d: dict[str, Any]) -> None:
        """
        Replace name/subtitle in the serialized dict with localized strings.

        When a `translation_key` is set and a resolver is active, name/subtitle are localized for
        the connection locale; otherwise the in-code values are preserved. On localized API output
        the internal translation_key/translation_params are stripped; they are retained in plain
        to_dict() calls used for internal round-tripping (caching, item mappings).
        """
        base = self._translation_base()
        if base is not None:
            for field_name in ("name", "subtitle"):
                if field_name not in d:
                    continue
                localized = resolve_translation(
                    f"{base}.{field_name}", owner=self.provider, params=self.translation_params
                )
                if localized is not None:
                    d[field_name] = localized
        if translations_active():
            d.pop("translation_key", None)
            d.pop("translation_params", None)

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
    date_added: datetime | None = None  # when item was added to library/collection

    def __hash__(self) -> int:
        """Return hash of MediaItem."""
        return super().__hash__()

    @property
    def available(self) -> bool:
        """Return (calculated) availability."""
        if not (available_providers := get_global_cache_value("available_providers")):
            # this is probably the client
            return any(x.available for x in self.provider_mappings)
        if TYPE_CHECKING:
            available_providers = cast("set[str]", available_providers)
        for x in self.provider_mappings:
            if x.available and x.provider_instance in available_providers:
                return True
        return False

    @property
    def image(self) -> MediaItemImage | None:
        """Return (first/random) image/thumb from metadata (if any)."""
        if self.metadata is None or self.metadata.images is None:
            return None
        return next((x for x in self.metadata.images if x.type == ImageType.THUMB), None)


@dataclass(kw_only=True)
class Genre(MediaItem):
    """Model for a Genre."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    media_type: MediaType = MediaType.GENRE
    genre_aliases: set[str] | None = None

    def __post_init__(self) -> None:
        """Call after init."""
        super().__post_init__()
        if self.translation_key is None:
            normalized_name = remove_diacritics(self.name.strip()).lower()
            normalized_name = normalized_name.replace("&", "_and_")
            normalized_name = normalized_name.replace(" ", "_").replace("-", "_")
            normalized_name = re.sub(r"[^a-z0-9_]", "", normalized_name)
            self.translation_key = normalized_name


@dataclass(kw_only=True)
class ItemMapping(_MediaItemBase):
    """Representation of a minimized item object."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    available: bool = True
    image: MediaItemImage | None = None
    year: int | None = None

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
    artist_type: ArtistType = ArtistType.SINGER


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
    last_played: int = 0  # only available for library/database items
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
    # When True, the playlist is provider-driven and endless: tracks are yielded on demand
    # via the provider's get_dynamic_playlist_tracks method instead of being pre-loaded.
    # Examples: Apple Music Artist Stations, Deezer Flow.
    is_dynamic: bool = False

    # The playlist may support only a single, or a mix of multiple media types. Allowed entries:
    # MediaType.AUDIOBOOK, MediaType.PODCAST_EPISODE, MediaType.RADIO, MediaType.TRACK
    supported_mediatypes: set[MediaType] = field(default_factory=lambda: {MediaType.TRACK})

    def __post_init__(self) -> None:
        """Run some basic sanity checks after init."""
        super().__post_init__()
        _supported = {
            MediaType.AUDIOBOOK,
            MediaType.PODCAST_EPISODE,
            MediaType.RADIO,
            MediaType.TRACK,
        }
        if len(self.supported_mediatypes.difference(_supported)) > 0:
            raise TypeError(f"Playlists are only supported for {_supported}.")


@dataclass(kw_only=True)
class Radio(MediaItem):
    """Model for a radio station."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    media_type: MediaType = MediaType.RADIO
    duration: int | None = None

    def __post_serialize__(self, d: dict[str, Any]) -> dict[str, Any]:
        """Adjust dict object after it has been serialized."""
        self._resolve_translation(d)
        # TEMP 2025-03-14: convert None duration to fake number for backwards compatibility
        d["duration"] = 0 if d["duration"] is None else d["duration"]
        return d


@dataclass(kw_only=True)
class Audiobook(MediaItem):
    """Model for an Audiobook."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    publisher: str | None = None
    authors: UniqueList[str | Artist] = field(default_factory=UniqueList)
    narrators: UniqueList[str | Artist] = field(default_factory=UniqueList)
    duration: int = 0
    # resume point info
    # set to None if unknown/unsupported by provider
    # which will let MA fallback to an internal resume point
    fully_played: bool | None = None
    resume_position_ms: int | None = None

    media_type: MediaType = MediaType.AUDIOBOOK

    @property
    def artist_str(self) -> str:
        """Return (combined) author string for audiobook."""
        return "/".join(a.name if isinstance(a, Artist) else a for a in self.authors)


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
class SoundEffect(MediaItem):
    """Model for a Sound Effect."""

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    duration: int = 0
    media_type: MediaType = MediaType.SOUND_EFFECT


@dataclass(kw_only=True)
class AudioSource(MediaItem):
    """
    Model for a live audio source provided by a plugin.

    Examples include an AirPlay receiver, Spotify Connect device,
    DLNA renderer, VBAN receiver, or a hardware bridge favorite.

    Conceptually behaves like a live media item (similar to Radio):
    enqueued as a single queue item, streamed continuously, with
    optional metadata updates pushed by the owning plugin.
    """

    __hash__ = _MediaItemBase.__hash__
    __eq__ = _MediaItemBase.__eq__

    media_type: MediaType = MediaType.AUDIO_SOURCE

    # a live source has no fixed duration; kept for QueueItem compatibility
    duration: int | None = None

    # capability flags drive which control buttons the UI shows
    # and which commands the player controller proxies to the plugin
    can_play_pause: bool = False
    can_seek: bool = False
    can_next_previous: bool = False

    # whether this source allows only a single concurrent consumer
    # True (default) = MA fans the single stream out via sync-group machinery
    # when multiple players target the same source
    # False = plugin is responsible for serving independent streams per consumer
    exclusive: bool = True

    # whether the plugin can initiate playback itself
    # (e.g. the Spotify app picking MA as a device)
    allow_external_trigger: bool = False

    # whether MA can initiate playback of this source on demand
    # (e.g. user selects the source from the UI / Live Inputs).
    # False = source is only reachable via external trigger (passive receivers
    # like a microphone or AirPlay-receiver target). The streams controller
    # filters user-initiated browse listings on this flag, and the owning
    # plugin's get_stream_details must raise (AudioError) when it cannot
    # actually acquire the upstream producer.
    can_initiate: bool = False


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


def _deserialize_recommendation_items(
    raw: list[dict[str, Any]],
) -> UniqueList[MediaItem | ItemMapping | BrowseFolder]:
    """Deserialize RecommendationFolder items using media_type discrimination."""
    media_type_class_map: dict[str, type[MediaItem]] = {
        MediaType.ARTIST: Artist,
        MediaType.ALBUM: Album,
        MediaType.TRACK: Track,
        MediaType.RADIO: Radio,
        MediaType.PLAYLIST: Playlist,
        MediaType.AUDIOBOOK: Audiobook,
        MediaType.PODCAST: Podcast,
        MediaType.PODCAST_EPISODE: PodcastEpisode,
        MediaType.GENRE: Genre,
        MediaType.AUDIO_SOURCE: AudioSource,
    }
    result: list[MediaItem | ItemMapping | BrowseFolder] = []
    for item in raw:
        if "provider_mappings" not in item:
            if item.get("media_type") in (MediaType.FOLDER, "folder"):
                result.append(BrowseFolder.from_dict(item))
            else:
                result.append(ItemMapping.from_dict(item))
        elif cls := media_type_class_map.get(item.get("media_type", "")):
            result.append(cls.from_dict(item))
        else:
            result.append(ItemMapping.from_dict(item))
    return UniqueList(result)


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
        default_factory=UniqueList,
        metadata=field_options(deserialize=_deserialize_recommendation_items),
    )
    subtitle: str | None = None  # optional subtitle for the recommendation


# some type aliases
# NOTE: BrowseFolder is not part of the MediaItemType alias, as it lacks
# provider mappings, i.e. we do not map a provider item to a BrowseFolder.
MediaItemType = (
    Artist
    | Album
    | Track
    | Radio
    | Playlist
    | Audiobook
    | Podcast
    | PodcastEpisode
    | Genre
    | AudioSource
)
PlayableMediaItemType = Track | Radio | Audiobook | PodcastEpisode | AudioSource
