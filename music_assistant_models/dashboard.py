"""Model(s) for dashboards shown on display devices and (api) clients."""

from __future__ import annotations

from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin

from .enums import DashboardType


@dataclass
class DashboardDevice(DataClassDictMixin):
    """Model for a registered dashboard endpoint capable of showing a MA dashboard."""

    # unique id chosen by the registering client (e.g. a device uuid)
    dashboard_id: str
    name: str
    supported_types: set[DashboardType] = field(default_factory=set)
    # set when this dashboard endpoint is also registered as a MA player
    player_id: str | None = None


@dataclass
class DashboardSession(DataClassDictMixin):
    """Model for an active dashboard session on a registered dashboard endpoint."""

    dashboard_id: str
    name: str
    dashboard: DashboardType
    # set for dashboards scoped to a single player (e.g. now playing)
    player_id: str | None = None
