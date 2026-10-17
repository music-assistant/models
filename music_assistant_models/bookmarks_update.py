"""
Model(s) for BookmarksUpdate.

This data is sent with the BOOKMARKS_UPDATED event.
"""

from __future__ import annotations

from dataclasses import dataclass

from mashumaro import DataClassDictMixin

from .enums import MediaType


@dataclass(frozen=True)
class BookmarksUpdate(DataClassDictMixin):
    """Object naming the copy whose bookmarks of one user changed."""

    media_type: MediaType
    provider_instance_id: str
    provider_item_id: str
    # the user whose bookmarks changed; a client only applies the update for its own user
    user_id: str
