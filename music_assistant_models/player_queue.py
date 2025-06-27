"""Model(s) for PlayerQueue."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Self

from mashumaro import DataClassDictMixin, field_options, pass_through

from .enums import PlaybackState, RepeatMode
from .media_items import MediaItemType, media_from_dict
from .queue_item import QueueItem


@dataclass
class PlayLogEntry:
    """Representation of a PlayLogEntry within Music Assistant."""

    queue_item_id: str
    duration: int | None = None
    seconds_streamed: float | None = None


@dataclass
class PlayerQueue(DataClassDictMixin):
    """Representation of (the state of) a PlayerQueue within Music Assistant."""

    queue_id: str
    active: bool
    display_name: str
    available: bool
    items: int
    shuffle_enabled: bool = False
    repeat_mode: RepeatMode = RepeatMode.OFF
    dont_stop_the_music_enabled: bool = False

    # current_index: index that is active (e.g. being played) by the player
    current_index: int | None = None
    # index_in_buffer: index that has been preloaded/buffered by the player
    index_in_buffer: int | None = None

    elapsed_time: float = 0
    elapsed_time_last_updated: float = field(default_factory=time.time)
    state: PlaybackState = PlaybackState.IDLE
    current_item: QueueItem | None = None
    next_item: QueueItem | None = None
    radio_source: list[MediaItemType] = field(default_factory=list)

    flow_mode: bool = False
    resume_pos: int = 0

    #############################################################################
    # the fields below will only be used server-side and not sent to the client #
    #############################################################################

    enqueued_media_items: list[MediaItemType] = field(
        default_factory=list,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    flow_mode_stream_log: list[PlayLogEntry] = field(
        default_factory=list,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    next_item_id_enqueued: str | None = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    session_id: str | None = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    items_last_updated: float = field(
        default_factory=time.time,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )

    @property
    def corrected_elapsed_time(self) -> float:
        """Return the corrected/realtime elapsed time."""
        return self.elapsed_time + (time.time() - self.elapsed_time_last_updated)

    def to_cache(self) -> dict[str, Any]:
        """Return the dict that is suitable for storing into the cache db."""
        d = self.to_dict()
        d.pop("flow_mode", None)
        d.pop("current_item", None)
        d.pop("next_item", None)
        d.pop("index_in_buffer", None)
        # enqueued_media_items needs to survive a restart
        # otherwise 'dont stop the music' will not work
        d["enqueued_media_items"] = [x.to_dict() for x in self.enqueued_media_items]
        return d

    @classmethod
    def from_cache(cls, d: dict[Any, Any]) -> Self:
        """Restore a PlayerQueue from a cache dict."""
        if "enqueued_media_items" in d:
            d["enqueued_media_items"] = [media_from_dict(x) for x in d["enqueued_media_items"]]
        return cls.from_dict(d)
