"""Model(s) for Player."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from mashumaro import DataClassDictMixin

from .constants import EXTRA_ATTRIBUTES_TYPES, PLAYER_CONTROL_NONE
from .enums import IdentifierType, MediaType, PlaybackState, PlayerFeature, PlayerType
from .unique_list import UniqueList


@dataclass
class OutputProtocol(DataClassDictMixin):
    """
    Represents an output protocol for a player.

    This provides a unified view of all ways to play audio to a device:
    - Native output (if player supports PLAY_MEDIA)
    - Protocol outputs (AirPlay, Chromecast, DLNA, etc.)
    """

    output_protocol_id: str  # Unique ID: "native" or protocol player_id
    name: str  # Display name: "Native (Sonos)" or "AirPlay"
    protocol_domain: str  # e.g., "airplay", "dlna"

    is_native: bool = False  # True if this is the player's native output
    priority: int = 100  # Lower = more preferred (native = 0 if supported)
    available: bool = True  # Whether this output protocol is currently available


@dataclass
class DeviceInfo(DataClassDictMixin):
    """
    Model for a player's device info.

    Contains device metadata and connection identifiers.
    """

    model: str = "Unknown model"
    manufacturer: str = "Unknown Manufacturer"
    software_version: str | None = None
    model_id: str | None = None
    manufacturer_id: str | None = None

    # Identifiers for device identification and protocol player linking
    # Maps IdentifierType to value (e.g., MAC_ADDRESS -> "AA:BB:CC:DD:EE:FF")
    identifiers: dict[IdentifierType, str] = field(default_factory=dict)

    @property
    def ip_address(self) -> str | None:
        """Get IP address from identifiers."""
        return self.identifiers.get(IdentifierType.IP_ADDRESS)

    @ip_address.setter
    def ip_address(self, value: str | None) -> None:
        """Set IP address in identifiers."""
        if not value:
            self.identifiers.pop(IdentifierType.IP_ADDRESS, None)
        else:
            self.identifiers[IdentifierType.IP_ADDRESS] = value

    @property
    def mac_address(self) -> str | None:
        """Get MAC address from identifiers."""
        return self.identifiers.get(IdentifierType.MAC_ADDRESS)

    @mac_address.setter
    def mac_address(self, value: str | None) -> None:
        """Set MAC address in identifiers."""
        if not value:
            self.identifiers.pop(IdentifierType.MAC_ADDRESS, None)
        else:
            # Normalize MAC address to uppercase with colons
            value = value.upper().replace("-", ":")
            self.identifiers[IdentifierType.MAC_ADDRESS] = value

    def add_identifier(
        self,
        identifier_type: IdentifierType,
        value: str | None,
    ) -> None:
        """Add or update an identifier.

        :param identifier_type: The type of identifier (MAC_ADDRESS, UUID, etc.).
        :param value: The identifier value. If None or empty, removes the identifier.
        """
        if not value:
            self.identifiers.pop(identifier_type, None)
            return
        # Normalize MAC address to uppercase with colons
        if identifier_type == IdentifierType.MAC_ADDRESS:
            value = value.upper().replace("-", ":")
        self.identifiers[identifier_type] = value


@dataclass(kw_only=True)
class PlayerMedia(DataClassDictMixin):
    """Metadata of Media loading/loaded into a player."""

    uri: str  # uri or other identifier of the loaded media - mandatory!
    media_type: MediaType = MediaType.UNKNOWN
    title: str | None = None  # optional
    artist: str | None = None  # optional
    album: str | None = None  # optional
    image_url: str | None = None  # optional
    duration: int | None = None  # optional
    source_id: str | None = None  # optional (ID of the source, may be a queue id)
    queue_item_id: str | None = None  # only present for requests from queue controller
    custom_data: dict[str, Any] | None = None  # optional - must be serializable

    # optional - elapsed playback time of the currently playing media
    elapsed_time: int | None = None
    elapsed_time_last_updated: float | None = None  # UTC timestamp

    @property
    def corrected_elapsed_time(self) -> float | None:
        """Return the corrected/realtime elapsed time (while playing)."""
        if self.elapsed_time is None or self.elapsed_time_last_updated is None:
            return None
        return self.elapsed_time + (time.time() - self.elapsed_time_last_updated)


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
class PlayerSoundMode(DataClassDictMixin):
    """Model for a player sound mode."""

    id: str
    name: str
    # passive: this sound mode can not be selected/activated by MA/the user
    passive: bool = False

    translation_key: str | None = None

    def __hash__(self) -> int:
        """Return custom hash."""
        return hash(self.id)

    def __post_init__(self) -> None:
        """Run some basic sanity checks after init."""
        if self.translation_key is None:
            self.translation_key = f"player_sound_mode.{self.id}"


class PlayerOptionType(StrEnum):
    """Enum for the type of a Player Option."""

    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"


PlayerOptionValueType = bool | float | int | str

PlayerOptionTypeMap: dict[PlayerOptionType, type[PlayerOptionValueType]] = {
    PlayerOptionType.BOOLEAN: bool,
    PlayerOptionType.STRING: str,
    PlayerOptionType.INTEGER: int,
    PlayerOptionType.FLOAT: float,
}


@dataclass
class PlayerOptionEntry(DataClassDictMixin):
    """A single choice."""

    key: str
    name: str
    type: PlayerOptionType

    value: PlayerOptionValueType

    def __hash__(self) -> int:
        """Return custom hash."""
        return hash(self.key)


@dataclass(kw_only=True)
class PlayerOption(DataClassDictMixin):
    """
    Model for a PlayerOption.

    The PlayerOption must also have the current state of itself.
    """

    key: str
    name: str
    type: PlayerOptionType

    # translation_key: optional translation key for this PlayerOption
    # (defaults to player_options.{id})
    translation_key: str | None = None
    # translation_params: optional parameters for the translation key
    translation_params: list[str] | None = None

    # current value of the option, see PlayerOptionValueType for serialization order.
    value: PlayerOptionValueType
    read_only: bool = False  # can the user adjust the option?

    # optional min/max value range for int/float (writeable) values
    min_value: float | int | None = None
    max_value: float | int | None = None
    step: float | int | None = None

    options: list[PlayerOptionEntry] | None = None

    def __hash__(self) -> int:
        """Return custom hash."""
        return hash(self.key)

    def __post_init__(self) -> None:
        """Run some basic sanity checks after init."""
        if self.translation_key is None:
            self.translation_key = f"player_options.{self.key}"

        # Basic type checks
        if not isinstance(self.value, PlayerOptionTypeMap[self.type]):
            raise TypeError(
                f"Value {self.value} must be of type {PlayerOptionTypeMap[self.type]} "
                "if type is {self.type}"
            )


@dataclass
class Player(DataClassDictMixin):
    """Representation of (the state of) a player within Music Assistant."""

    player_id: str
    provider: str  # instance_id of the player provider
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

    # static_group_members: List of player group member id's that can not be ungrouped.
    static_group_members: UniqueList[str] = field(default_factory=UniqueList)

    # can_group_with: return set of player_id's this player can group/sync with
    # can also be instance id of an entire provider if all players can group with each other
    can_group_with: set[str] = field(default_factory=set)

    # synced_to: player_id of the player this player is currently synced to
    # also referred to as "sync leader"
    synced_to: str | None = None

    # return active sound mode for this player
    active_sound_mode: str | None = None

    # sound_mode_list: return list of available (native) sound modes for this player
    sound_mode_list: UniqueList[PlayerSoundMode] = field(default_factory=UniqueList)

    # options: return list of available (native) player options for this player
    options: UniqueList[PlayerOption] = field(default_factory=UniqueList)

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

    # hide_in_ui: if the player should be hidden in the UI
    hide_in_ui: bool = False

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

    # output_protocols: all available output methods for this player
    # Includes native output (if PLAY_MEDIA supported) + protocol outputs
    # This is the public API - computed from internal linked_protocols
    output_protocols: list[OutputProtocol] = field(default_factory=list)

    # active_output_protocol: which output protocol is currently being used for playback
    # Can be "native" or a protocol player_id
    # None means no playback in progress or native playback without explicit selection
    active_output_protocol: str | None = None

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
        # add alias for device_info.mac_address for backwards compatibility
        if "device_info" in d and "identifiers" in d["device_info"]:
            d["device_info"]["mac_address"] = d["device_info"]["identifiers"].get(
                IdentifierType.MAC_ADDRESS.value
            )
        # add alias for device_info.ip_address for backwards compatibility
        if "device_info" in d and "identifiers" in d["device_info"]:
            d["device_info"]["ip_address"] = d["device_info"]["identifiers"].get(
                IdentifierType.IP_ADDRESS.value
            )
        # add alias for hide_in_ui for backwards compatibility
        if d.get("hide_in_ui") is True:
            d["hide_player_in_ui"] = ["always"]
        else:
            d["hide_player_in_ui"] = [
                "when_unavailable",
                "when_synced",
                "when_group_active",
            ]
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
