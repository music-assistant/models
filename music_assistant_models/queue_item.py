"""Model a QueueItem."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Self
from uuid import uuid4

from mashumaro import DataClassDictMixin

from .enums import MediaType
from .media_items import (
    ItemMapping,
    MediaItemImage,
    PlayableMediaItemType,
    UniqueList,
    is_track,
    media_from_dict,
)
from .streamdetails import StreamDetails


@dataclass
class QueueItem(DataClassDictMixin):
    """Representation of a queue item."""

    queue_id: str
    queue_item_id: str
    name: str
    duration: int | None
    sort_index: int = 0
    streamdetails: StreamDetails | None = None
    media_item: PlayableMediaItemType | None = None
    image: MediaItemImage | None = None
    index: int = 0
    # the available flag can be used to mark items that are not available/playable anymore
    available: bool = True
    # guest priority queue: track who added this item for priority ordering
    added_by_user_id: str | None = None
    added_by_user_role: str | None = (
        None  # stored as string for serialization (e.g., "guest", "admin")
    )
    added_at: float | None = None  # unix timestamp when item was added
    queue_option: str | None = None  # how item was added (e.g., "next", "add", "play")

    def __post_init__(self) -> None:
        """Set default values."""
        if not self.name and self.streamdetails and self.streamdetails.stream_title:
            self.name = self.streamdetails.stream_title
        if not self.name:
            self.name = self.uri

    @property
    def uri(self) -> str:
        """Return uri for this QueueItem (for logging purposes)."""
        if self.media_item and self.media_item.uri:
            return self.media_item.uri
        return self.queue_item_id

    @property
    def media_type(self) -> MediaType:
        """Return MediaType for this QueueItem (for convenience purposes)."""
        if self.media_item:
            return self.media_item.media_type
        if self.streamdetails:
            return self.streamdetails.media_type
        return MediaType.UNKNOWN

    @classmethod
    def from_media_item(
        cls,
        queue_id: str,
        media_item: PlayableMediaItemType,
        user_id: str | None = None,
        user_role: str | None = None,
        queue_option: str | None = None,
    ) -> QueueItem:
        """Construct QueueItem from track/radio item.

        :param queue_id: The ID of the queue this item belongs to.
        :param media_item: The media item (track, radio, etc.) to create a queue item from.
        :param user_id: Optional user ID of who added this item (for guest priority queue).
        :param user_role: Optional user role string (e.g., "guest", "admin") for priority ordering.
        :param queue_option: Optional queue option string (e.g., "next", "add").
        """
        if is_track(media_item) and hasattr(media_item, "artists"):
            artists = "/".join(x.name for x in media_item.artists)
            name = f"{artists} - {media_item.name}"
            if media_item.version:
                name = f"{name} ({media_item.version})"
            # save a lot of data/bandwidth by simplifying nested objects
            media_item.artists = UniqueList([ItemMapping.from_item(x) for x in media_item.artists])
            if media_item.album:
                media_item.album = ItemMapping.from_item(media_item.album)
        else:
            name = media_item.name
        return cls(
            queue_id=queue_id,
            queue_item_id=uuid4().hex,
            name=name,
            duration=media_item.duration,
            media_item=media_item,
            image=get_image(media_item),
            added_by_user_id=user_id,
            added_by_user_role=user_role,
            added_at=time.time(),
            queue_option=queue_option,
        )

    def to_cache(self) -> dict[str, Any]:
        """Return the dict that is suitable for storing into the cache db."""
        base = self.to_dict()
        base.pop("streamdetails", None)
        return base

    @classmethod
    def from_cache(cls, d: dict[Any, Any]) -> Self:
        """Restore a QueueItem from a cache dict.

        Note: We manually deserialize media_item because mashumaro doesn't correctly
        deserialize union types - it picks the first type in the union (Track)
        regardless of the actual media_type field value.
        """
        d.pop("streamdetails", None)
        # Extract and manually deserialize media_item with correct type discrimination
        media_item_dict = d.pop("media_item", None)
        result = cls.from_dict(d)
        if media_item_dict and isinstance(media_item_dict, dict):
            result.media_item = media_from_dict(media_item_dict)  # type: ignore[assignment]
        return result


def get_image(media_item: PlayableMediaItemType | None) -> MediaItemImage | None:
    """Find the Image for the MediaItem."""
    if not media_item:
        return None
    if media_item.image:
        return media_item.image
    if media_item.media_type == MediaType.TRACK and (album := getattr(media_item, "album", None)):
        return get_image(album)
    if media_item.media_type == MediaType.PODCAST_EPISODE and (
        podcast := getattr(media_item, "podcast", None)
    ):
        return get_image(podcast)
    return None
