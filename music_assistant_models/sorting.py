"""Sort field definitions and metadata for library listings."""

from __future__ import annotations

from dataclasses import dataclass

from .enums import MediaType, SortDirection, SortField


@dataclass(frozen=True)
class SortFieldDefinition:
    """
    Definition and metadata for a sort field.

    Note: The actual SQL implementation for a field may vary by MediaType.
    For example, SortField.ARTIST_NAME uses different joins:
    - Tracks: JOIN track_artists → artists.search_name ASC, tracks.search_name ASC
    - Albums: JOIN album_artists → artists.search_name ASC, year DESC
    """

    field: SortField
    supports_direction: bool
    default_direction: SortDirection | None = None
    label_key: str | None = None


# Complete definitions for all sort fields
SORT_FIELD_DEFINITIONS: dict[SortField, SortFieldDefinition] = {
    SortField.NAME: SortFieldDefinition(
        field=SortField.NAME,
        supports_direction=True,
        default_direction=SortDirection.ASC,
        label_key="name",
    ),
    SortField.SORT_NAME: SortFieldDefinition(
        field=SortField.SORT_NAME,
        supports_direction=True,
        default_direction=SortDirection.ASC,
        label_key="sort_name",
    ),
    SortField.TIMESTAMP_ADDED: SortFieldDefinition(
        field=SortField.TIMESTAMP_ADDED,
        supports_direction=True,
        default_direction=SortDirection.DESC,
        label_key="timestamp_added",
    ),
    SortField.TIMESTAMP_MODIFIED: SortFieldDefinition(
        field=SortField.TIMESTAMP_MODIFIED,
        supports_direction=True,
        default_direction=SortDirection.DESC,
        label_key="timestamp_modified",
    ),
    SortField.LAST_PLAYED: SortFieldDefinition(
        field=SortField.LAST_PLAYED,
        supports_direction=True,
        default_direction=SortDirection.DESC,
        label_key="last_played",
    ),
    SortField.PLAY_COUNT: SortFieldDefinition(
        field=SortField.PLAY_COUNT,
        supports_direction=True,
        default_direction=SortDirection.DESC,
        label_key="play_count",
    ),
    SortField.DURATION: SortFieldDefinition(
        field=SortField.DURATION,
        supports_direction=True,
        default_direction=SortDirection.ASC,
        label_key="duration",
    ),
    SortField.YEAR: SortFieldDefinition(
        field=SortField.YEAR,
        supports_direction=True,
        default_direction=SortDirection.DESC,
        label_key="year",
    ),
    SortField.POSITION: SortFieldDefinition(
        field=SortField.POSITION,
        supports_direction=True,
        default_direction=SortDirection.ASC,
        label_key="position",
    ),
    SortField.ARTIST_NAME: SortFieldDefinition(
        field=SortField.ARTIST_NAME,
        supports_direction=True,
        default_direction=SortDirection.ASC,
        label_key="artist_name",
    ),
    SortField.RANDOM: SortFieldDefinition(
        field=SortField.RANDOM,
        supports_direction=False,
        default_direction=None,
        label_key="random",
    ),
    SortField.RANDOM_PLAY_COUNT: SortFieldDefinition(
        field=SortField.RANDOM_PLAY_COUNT,
        supports_direction=False,
        default_direction=None,
        label_key="random_weighted",
    ),
}


# Map media types to their available sort fields
MEDIA_TYPE_SORT_FIELDS: dict[MediaType, set[SortField]] = {
    MediaType.TRACK: {
        SortField.NAME,
        SortField.SORT_NAME,
        SortField.DURATION,
        SortField.TIMESTAMP_ADDED,
        SortField.TIMESTAMP_MODIFIED,
        SortField.LAST_PLAYED,
        SortField.PLAY_COUNT,
        SortField.ARTIST_NAME,
        SortField.POSITION,  # for playlist tracks
        SortField.RANDOM,
        SortField.RANDOM_PLAY_COUNT,
    },
    MediaType.ALBUM: {
        SortField.NAME,
        SortField.SORT_NAME,
        SortField.YEAR,
        SortField.TIMESTAMP_ADDED,
        SortField.TIMESTAMP_MODIFIED,
        SortField.LAST_PLAYED,
        SortField.PLAY_COUNT,
        SortField.ARTIST_NAME,
        SortField.RANDOM,
    },
    MediaType.ARTIST: {
        SortField.NAME,
        SortField.SORT_NAME,
        SortField.TIMESTAMP_ADDED,
        SortField.TIMESTAMP_MODIFIED,
        SortField.LAST_PLAYED,
        SortField.PLAY_COUNT,
        SortField.RANDOM,
    },
    MediaType.PLAYLIST: {
        SortField.NAME,
        SortField.SORT_NAME,
        SortField.TIMESTAMP_ADDED,
        SortField.TIMESTAMP_MODIFIED,
        SortField.LAST_PLAYED,
        SortField.PLAY_COUNT,
        SortField.RANDOM,
    },
    MediaType.RADIO: {
        SortField.NAME,
        SortField.SORT_NAME,
        SortField.TIMESTAMP_ADDED,
        SortField.TIMESTAMP_MODIFIED,
        SortField.LAST_PLAYED,
        SortField.PLAY_COUNT,
        SortField.RANDOM,
    },
    MediaType.AUDIOBOOK: {
        SortField.NAME,
        SortField.SORT_NAME,
        SortField.TIMESTAMP_ADDED,
        SortField.TIMESTAMP_MODIFIED,
        SortField.LAST_PLAYED,
        SortField.PLAY_COUNT,
        SortField.RANDOM,
    },
    MediaType.PODCAST: {
        SortField.NAME,
        SortField.SORT_NAME,
        SortField.TIMESTAMP_ADDED,
        SortField.TIMESTAMP_MODIFIED,
        SortField.LAST_PLAYED,
        SortField.PLAY_COUNT,
        SortField.RANDOM,
    },
    MediaType.GENRE: {
        SortField.NAME,
        SortField.SORT_NAME,
        SortField.TIMESTAMP_ADDED,
        SortField.PLAY_COUNT,
        SortField.RANDOM,
    },
}
