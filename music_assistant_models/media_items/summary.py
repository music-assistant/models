"""
Summary (slim) variants of the media item models, used for listings.

These are drop-in subclasses of the regular media item models — same wire shape, same
``media_type`` discriminator, deserializable with the regular classes — but carry only the
fields a list view renders: identity, name(s), artist/album mappings, a single (thumb) image
and a handful of per-type scalars. All unset (None) fields are omitted from the serialized
output, provider mappings are empty and ``available`` is a plain (pre-computed) field instead
of a derived property.

The Music Assistant server returns these from the ``library_items`` API commands when the
``summary`` flag is set; full items (with provider mappings, complete metadata, etc.) remain
available through the regular ``get`` commands.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mashumaro.config import BaseConfig
from mashumaro.dialect import Dialect

from music_assistant_models.unique_list import UniqueList

from .media_item import (
    Album,
    Artist,
    Audiobook,
    Genre,
    ItemMapping,
    Playlist,
    Podcast,
    Radio,
    Track,
)
from .metadata import MediaItemMetadata
from .provider_mapping import ProviderMapping


class _OmitNoneDialect(Dialect):
    omit_none = True


@dataclass(kw_only=True, eq=False)
class MediaItemMetadataSummary(MediaItemMetadata):
    """Metadata of a summary item, with None-valued fields omitted from serialized output."""

    class Config(BaseConfig):
        """Mashumaro serialization config."""

        dialect = _OmitNoneDialect


@dataclass(kw_only=True, eq=False)
class ItemMappingSummary(ItemMapping):
    """ItemMapping of a summary item, with None-valued fields omitted from serialized output."""

    class Config(BaseConfig):
        """Mashumaro serialization config."""

        dialect = _OmitNoneDialect


class SummaryDialect(Dialect):
    """
    Serialization dialect for summary items.

    Omits None-valued fields and (de)serializes nested metadata as its summary variant.
    """

    omit_none = True
    serialization_strategy = {  # noqa: RUF012
        MediaItemMetadata: {
            "serialize": lambda v: v.to_dict(),
            "deserialize": MediaItemMetadataSummary.from_dict,
        },
    }


@dataclass(kw_only=True, eq=False)
class _SummaryBase:
    """
    Mixin that turns a regular media item subclass into its summary variant.

    Serialization omits None-valued fields, ``available`` is a plain field (filled by the
    server from the — not serialized — provider mappings) and metadata is reduced to the
    slim summary variant.
    """

    class Config(BaseConfig):
        """Mashumaro serialization config."""

        dialect = SummaryDialect

    provider_mappings: set[ProviderMapping] = field(default_factory=set)
    available: bool = True
    metadata: MediaItemMetadata = field(default_factory=MediaItemMetadataSummary)


@dataclass(kw_only=True, eq=False)
class ArtistSummary(_SummaryBase, Artist):
    """Summary variant of Artist, used for listings."""


@dataclass(kw_only=True, eq=False)
class AlbumSummary(_SummaryBase, Album):
    """Summary variant of Album, used for listings."""

    artists: UniqueList[ItemMappingSummary] = field(  # type: ignore[assignment]
        default_factory=UniqueList
    )


@dataclass(kw_only=True, eq=False)
class TrackSummary(_SummaryBase, Track):
    """Summary variant of Track, used for listings."""

    artists: UniqueList[ItemMappingSummary] = field(  # type: ignore[assignment]
        default_factory=UniqueList
    )
    album: ItemMappingSummary | None = None


@dataclass(kw_only=True, eq=False)
class PlaylistSummary(_SummaryBase, Playlist):
    """Summary variant of Playlist, used for listings."""


@dataclass(kw_only=True, eq=False)
class RadioSummary(_SummaryBase, Radio):
    """Summary variant of Radio, used for listings."""


@dataclass(kw_only=True, eq=False)
class AudiobookSummary(_SummaryBase, Audiobook):
    """Summary variant of Audiobook, used for listings."""


@dataclass(kw_only=True, eq=False)
class PodcastSummary(_SummaryBase, Podcast):
    """Summary variant of Podcast, used for listings."""


@dataclass(kw_only=True, eq=False)
class GenreSummary(_SummaryBase, Genre):
    """Summary variant of Genre, used for listings."""


MediaItemSummaryType = (
    ArtistSummary
    | AlbumSummary
    | TrackSummary
    | PlaylistSummary
    | RadioSummary
    | AudiobookSummary
    | PodcastSummary
    | GenreSummary
)
