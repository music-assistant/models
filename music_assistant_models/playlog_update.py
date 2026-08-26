"""
Model(s) for PlaylogUpdate.

This data is sent with the PLAYLOG_UPDATED event.
"""

from __future__ import annotations

from dataclasses import dataclass

from mashumaro import DataClassDictMixin

from .enums import MediaType


@dataclass(frozen=True)
class PlaylogUpdate(DataClassDictMixin):
    """Object describing the new playlog state of a media item."""

    uri: str
    media_type: MediaType
    fully_played: bool
    seconds_played: int
    # the user the playlog change applies to; None when it applies to all users
    userid: str | None = None
