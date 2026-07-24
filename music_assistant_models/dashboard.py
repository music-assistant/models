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
    # provider domain this endpoint belongs to; used only as a hint to resolve its icon
    provider_domain_hint: str | None = None


@dataclass
class DashboardSession(DataClassDictMixin):
    """Model for an active dashboard session on a registered dashboard endpoint."""

    dashboard_id: str
    name: str
    dashboard: DashboardType
    # set for dashboards scoped to a single player (e.g. now playing)
    player_id: str | None = None
