"""Model(s) for dashboard casting to display devices."""

from __future__ import annotations

from dataclasses import dataclass

from mashumaro import DataClassDictMixin


@dataclass
class DashboardDevice(DataClassDictMixin):
    """Model for a display device capable of showing a MA dashboard."""

    # device_id: provider-scoped unique id of the display device
    device_id: str

    # provider_instance: instance_id of the provider that can drive this device
    provider_instance: str

    # name: human readable name of the display device
    name: str

    # player_id: set when this display device is also registered as a MA player
    player_id: str | None = None
