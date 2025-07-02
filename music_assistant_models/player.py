"""Model(s) for Player."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from mashumaro import DataClassDictMixin

from .constants import PLAYER_CONTROL_NONE
from .enums import HidePlayerOption, MediaType, PlaybackState, PlayerFeature, PlayerType
from .unique_list import UniqueList

EXTRA_ATTRIBUTES_TYPES = str | int | float | bool | None


@dataclass
class DeviceInfo(DataClassDictMixin):
    """Model for a player's deviceinfo."""

    model: str = "Unknown model"
    manufacturer: str = "Unknown Manufacturer"
    software_version: str | None = None
    model_id: str | None = None
    manufacturer_id: str | None = None
    ip_address: str | None = None
    mac_address: str | None = None


@dataclass
class PlayerMedia(DataClassDictMixin):
    """Metadata of Media loading/loaded into a player."""

    uri: str  # uri or other identifier of the loaded media
    media_type: MediaType = MediaType.UNKNOWN
    title: str | None = None  # optional
    artist: str | None = None  # optional
    album: str | None = None  # optional
    image_url: str | None = None  # optional
    duration: int | None = None  # optional
    queue_id: str | None = None  # only present for requests from queue controller
    queue_item_id: str | None = None  # only present for requests from queue controller
    custom_data: dict[str, Any] | None = None  # optional


@dataclass
class PlayerSource(DataClassDictMixin):
    """Model for a player source."""

    id: str
    name: str
    # passive: this source can not be selected/activated by MA/the user
    passive: bool = False
    # can_play_pause: this source can be paused and resumed
    can_play_pause: bool = False
    # can_seek: this source can be seeked
    can_seek: bool = False
    # can_next_previous: this source can be skipped to next/previous item
    can_next_previous: bool = False

    def __hash__(self) -> int:
        """Return custom hash."""
        return hash(self.id)


@dataclass
class Player(DataClassDictMixin):
    """Representation of (the state of) a player within Music Assistant."""

    player_id: str
    provider: str  # instance_id/lookup_key of the player provider
    type: PlayerType
    name: str
    available: bool
    device_info: DeviceInfo
    supported_features: set[PlayerFeature] = field(default_factory=set)
    playback_state: PlaybackState = PlaybackState.IDLE
    elapsed_time: float | None = None
    elapsed_time_last_updated: float | None = None
    powered: bool | None = None
    volume_level: int | None = None
    volume_muted: bool | None = None

    # group_members: List of player group member id's or synced child`s.
    # - If this player is a dedicated group player,
    #   returns all child id's of the players in the group.
    # - If this is a syncgroup of players from the same platform (e.g. sonos),
    #   this will return the id's of players synced to this player,
    #   and this will include the player's own id (as first item in the list).
    group_members: UniqueList[str] = field(default_factory=UniqueList)

    # can_group_with: return set of player_id's this player can group/sync with
    # can also be instance id of an entire provider if all players can group with each other
    can_group_with: set[str] = field(default_factory=set)

    # synced_to: player_id of the player this player is currently synced to
    # also referred to as "sync leader"
    synced_to: str | None = None

    # active_source: return active source (id) for this player
    # this can be a player native source id as defined in 'source list'
    # or a Music Assistant queue id, if Music Assistant is the active source.
    # When set to known, the player provider has no accurate information about the source.
    # In that case, the player manager will try to find out the active source.
    active_source: str | None = None

    # source_list: return list of available (native) sources for this player
    source_list: UniqueList[PlayerSource] = field(default_factory=UniqueList)

    # active_group: return player_id of the active group for this player (if any)
    # if the player is grouped and a group is active,
    # this should be set to the group's player_id by the group player implementation.
    active_group: str | None = None

    # current_media: return current active/loaded item on the player
    # this may be a MA queue item, url, uri or some provider specific string
    # includes metadata if supported by the provider/player
    current_media: PlayerMedia | None = None

    # enabled: if the player is enabled
    # a disabled player is hidden in the UI and updates will not be processed
    # nor will it be added to the HA integration
    enabled: bool = True

    # hide_player_in_ui: if the player should be hidden in the UI
    # if set to ALWAYS, the player will be hidden in the UI
    # if set to AUTO, the player will be hidden in the UI if it's not playing
    # if set to NEVER, the player will never be hidden in the UI
    hide_player_in_ui: set[HidePlayerOption] = field(
        default_factory=lambda: {
            HidePlayerOption.WHEN_GROUP_ACTIVE,
            HidePlayerOption.WHEN_UNAVAILABLE,
            HidePlayerOption.WHEN_SYNCED,
        }
    )

    # expose_to_ha: if the player should be exposed to Home Assistant
    # if set to False, the player will not be added to the HA integration
    expose_to_ha: bool = True

    # icon: material design icon for this player
    icon: str = "mdi-speaker"

    # group_volume: if the player is a player group or syncgroup master,
    # this will return the average volume of all child players
    # if not a group player, this is just the player's volume
    group_volume: int = 100

    # extra_attributes: additional (player specific) attributes for this player
    extra_attributes: dict[str, EXTRA_ATTRIBUTES_TYPES] = field(default_factory=dict)

    # power_control: the power control attached to this player (set by config)
    power_control: str = PLAYER_CONTROL_NONE

    # volume_control: the volume control attached to this player (set by config)
    volume_control: str = PLAYER_CONTROL_NONE

    # mute_control: the volume control attached to this player (set by config)
    mute_control: str = PLAYER_CONTROL_NONE

    #############################################################################
    # helper methods and properties                                             #
    #############################################################################

    @property
    def corrected_elapsed_time(self) -> float | None:
        """Return the corrected/realtime elapsed time."""
        if self.elapsed_time is None or self.elapsed_time_last_updated is None:
            return None
        if self.playback_state == PlaybackState.PLAYING:
            return self.elapsed_time + (time.time() - self.elapsed_time_last_updated)
        return self.elapsed_time

    @property
    def current_item_id(self) -> str | None:
        """Return current_item_id from current_media (if exists)."""
        if self.current_media:
            return self.current_media.queue_item_id or self.current_media.uri
        return None

    @classmethod
    def __post_serialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Adjust dict object after it has been serialized."""
        # TEMP 2025-03-15: convert power to boolean for backwards compatibility
        # Remove this once the HA integration is updated to handle this
        if d["powered"] is None and d["power_control"] == PLAYER_CONTROL_NONE:
            d["powered"] = True
        # add alias for display_name for backwards compatibility
        d["display_name"] = d["name"]
        # add alias for state for backwards compatibility
        d["state"] = d["playback_state"]
        # add alias for group_childs for backwards compatibility
        d["group_childs"] = d["group_members"]
        # add alias for extra_data for backwards compatibility
        d["extra_data"] = d["extra_attributes"]
        return d

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Adjust object before it will be deserialized."""
        # add alias for playback_state for backwards compatibility
        if "playback_state" not in d and "state" in d:
            d["playback_state"] = d["state"]
        # add alias for name for backwards compatibility
        if "name" not in d and "display_name" in d:
            d["name"] = d["display_name"]
        # add alias for group_members for backwards compatibility
        if "group_members" not in d and "group_childs" in d:
            d["group_members"] = d["group_childs"]
        # add alias for extra_attributes for backwards compatibility
        if "extra_attributes" not in d and "extra_data" in d:
            d["extra_attributes"] = d["extra_data"]
        return d
