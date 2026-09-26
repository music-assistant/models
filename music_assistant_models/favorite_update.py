"""
Model(s) for FavoriteUpdate.

This data is sent with the FAVORITE_UPDATED event.
"""

from __future__ import annotations

from dataclasses import dataclass

from mashumaro import DataClassDictMixin

from .enums import MediaType


@dataclass(frozen=True)
class FavoriteUpdate(DataClassDictMixin):
    """Object describing one user's new favorite state on a library item."""

    uri: str
    media_type: MediaType
    item_id: str
    # True is a like, False a dislike, None means the user cleared their choice
    favorite: bool | None
    # the user whose state changed; a client only applies the update for its own user
    user_id: str
