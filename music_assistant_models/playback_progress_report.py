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

    uri: str
    media_type: MediaType
    name: str
    artist: str | None
    artist_mbids: list[str] | None
    album: str | None
    album_mbid: str | None
    image_url: str | None
    duration: int
    mbid: str | None
    seconds_played: int
    fully_played: bool
    is_playing: bool
