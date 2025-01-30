"""Model(s) for a PlayerControl."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import Any

from mashumaro import DataClassDictMixin, field_options, pass_through

AsyncCallback = Callable[[], Coroutine[Any, Any, None]]


@dataclass
class PlayerControl(DataClassDictMixin):
    """Model for a player PlayerControl (to override power/volume control)."""

    # id: unique id for this control
    id: str

    # provider: # instance_id of the provider providing this control
    provider: str

    # name: human readable name of the control
    name: str

    # supports_power_on: whether the control supports turning on/off
    supports_power: bool = False
    # supports_volume: whether the control supports volume control
    supports_volume: bool = False
    # supports_mute: whether the control supports muting
    supports_mute: bool = False

    # power_state: current power state of the control (on/off) - if provided by this control
    power_state: bool = False
    # volume_level: current volume_level of the control (0...100) - if provided by this control
    volume_level: int = 0
    # volume_muted: current mute state of the control (muted/unmuted) - if provided by this control
    volume_muted: bool = False  # current mute state of the control (muted/unmuted)

    #############################################################################
    # the fields below will only be used server-side and not sent to the client #
    #############################################################################

    # power_on: callback to turn the control on - if supported by this control
    power_on: AsyncCallback | None = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    # power_off: callback to turn the control on - if supported by this control
    power_off: AsyncCallback | None = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    # volume_set: callback to set the volume level
    volume_set: Callable[[int], Coroutine[Any, Any, None]] | None = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    # mute_set: callback to set the mute state
    mute_set: Callable[[bool], Coroutine[Any, Any, None]] | None = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
