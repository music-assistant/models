"""
Model(s) for MediaItemPlaybackProgressReport.

This data is sent with the MEDIA_ITEM_PLAYED event.
"""

from __future__ import annotations

from dataclasses import dataclass

from mashumaro import DataClassDictMixin

from .enums import MediaType


@dataclass(frozen=True)
class MediaItemPlaybackProgressReport(DataClassDictMixin):
    """Object to submit in a progress report during/after media playback."""

    # mandatory fields
    uri: str
    media_type: MediaType
    name: str
    duration: int
    seconds_played: int
    fully_played: bool
    is_playing: bool

    # optional fields
    mbid: str | None = None
    artist: str | None = None  # This is a concatenated string of all artist names
    artists: list[str] | None = None  # This is a list of the artist names
    artist_mbids: list[str] | None = None
    album: str | None = None
    album_mbid: str | None = None
    album_artist: str | None = None
    album_artist_mbids: list[str] | None = None
    image_url: str | None = None
    version: str | None = None
    userid: str | None = None  # the user(id) that initiated the playback
