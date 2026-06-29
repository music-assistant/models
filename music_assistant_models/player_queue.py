"""Model(s) for PlayerQueue."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from mashumaro import DataClassDictMixin, field_options, pass_through

from .constants import EXTRA_ATTRIBUTES_TYPES
from .enums import PlaybackState, RepeatMode
from .media_items import ItemMapping, MediaItemType, media_from_dict
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
    crossfade_enabled: bool = False
    autoplay_enabled: bool = False
    # smart_fades_active: whether the queue's effective crossfade is currently smart crossfade
    # (i.e. crossfade is on, smart is preferred, and smart fades are available). Derived at runtime
    # by the server, read-only and not persisted; lets clients show a smart-fades indicator.
    smart_fades_active: bool = False
    # smart_shuffle_active: True when smart shuffle is in effect (enabled and shuffle on, or
    # radio mode active). Derived at runtime by the server, read-only and not persisted; lets
    # clients show the indicator and disable the plain shuffle toggle.
    smart_shuffle_active: bool = False

    # current_index: index that is active (e.g. being played) by the player
    current_index: int | None = None
    # index_in_buffer: index that has been preloaded/buffered by the player
    index_in_buffer: int | None = None

    elapsed_time: float = 0
    elapsed_time_last_updated: float = field(default_factory=time.time)
    # playback_speed in effect at elapsed_time_last_updated
    # Used to calculate the corrected elapsed time to advance the wallcloack delta in media-time
    playback_speed: float = 1.0
    state: PlaybackState = PlaybackState.IDLE
    current_item: QueueItem | None = None
    next_item: QueueItem | None = None
    # sources: the parent items the queue is playing from — regular media items and/or dynamic
    # playlists (radio playlists, provider stations). 
    # When `is_dynamic` the queue dynamically fills from these.
    sources: list[ItemMapping] = field(default_factory=list)

    flow_mode: bool = False
    resume_pos: int = 0
    # True when the queue is in dynamic mode (one or more dynamic sources); set by the server.
    # Implies autoplay and smart shuffle are active.
    is_dynamic: bool = False

    # extra_attributes: additional attributes for this player_queue to store/forward
    # additional data that is not part of the standard model
    # must be serializable types only
    extra_attributes: dict[str, EXTRA_ATTRIBUTES_TYPES] = field(default_factory=dict)

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
    userid: str | None = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Accept the legacy `dont_stop_the_music_enabled` / `radio_source` keys."""
        if "autoplay_enabled" not in d and "dont_stop_the_music_enabled" in d:
            d["autoplay_enabled"] = d["dont_stop_the_music_enabled"]
        if "sources" not in d and "radio_source" in d:
            d["sources"] = d["radio_source"]
        return d

    def __post_serialize__(self, d: dict[str, Any]) -> dict[str, Any]:
        """Mirror the deprecated `dont_stop_the_music_enabled` / `radio_source` keys."""
        d["dont_stop_the_music_enabled"] = d["autoplay_enabled"]
        # temporary back-compat: older clients still read the deprecated `radio_source`
        d["radio_source"] = d.get("sources", []) if self.is_dynamic else []
        return d

    @property
    def corrected_elapsed_time(self) -> float:
        """Return the corrected/realtime elapsed time."""
        if self.state == PlaybackState.PLAYING:
            return self.elapsed_time + (
                (time.time() - self.elapsed_time_last_updated) * self.playback_speed
            )
        return self.elapsed_time

    def to_cache(self) -> dict[str, Any]:
        """Return the dict that is suitable for storing into the cache db."""
        d = self.to_dict()
        d.pop("flow_mode", None)
        d.pop("current_item", None)
        d.pop("next_item", None)
        d.pop("index_in_buffer", None)
        # smart_fades_active is derived at runtime, never persisted (crossfade_enabled is)
        d.pop("smart_fades_active", None)
        # smart_shuffle_active is derived at runtime, never persisted
        d.pop("smart_shuffle_active", None)
        # enqueued_media_items needs to survive a restart
        # otherwise 'autoplay' will not work
        d["enqueued_media_items"] = [x.to_dict() for x in self.enqueued_media_items]
        d["userid"] = self.userid
        return d

    def from_cache(self, data: dict[str, Any]) -> PlayerQueue:
        """Update the PlayerQueue from the dict stored in the cache db."""
        self.enqueued_media_items = [
            item
            for x in data.get("enqueued_media_items", [])
            if isinstance(x, dict) and not isinstance(item := media_from_dict(x), ItemMapping)
        ]
        self.sources = [
            item
            for x in data.get("sources", data.get("radio_source", []))
            if isinstance(x, dict) and not isinstance(item := media_from_dict(x), ItemMapping)
        ]
        self.userid = data.get("userid")
        return self
