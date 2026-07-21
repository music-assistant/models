"""Model(s) for dashboard casting to display devices."""

from __future__ import annotations

from dataclasses import dataclass

from mashumaro import DataClassDictMixin

from .enums import DashboardType


@dataclass
class DashboardDevice(DataClassDictMixin):
    """Model for a display device capable of showing a MA dashboard."""

    # provider-scoped unique id
    device_id: str
    provider_instance: str
    name: str
    # set when this display device is also registered as a MA player
    player_id: str | None = None


@dataclass
class DashboardSession(DataClassDictMixin):
    """Model for an active dashboard cast session on a display device."""

    # provider-scoped unique id
    device_id: str
    provider_instance: str
    name: str
    dashboard: DashboardType
    # set for dashboards scoped to a single player (e.g. now playing)
    player_id: str | None = None
