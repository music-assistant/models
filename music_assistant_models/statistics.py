"""Statistics models for Music Assistant."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from mashumaro.mixins.orjson import DataClassORJSONMixin

from music_assistant_models.media_items import ItemMapping

if TYPE_CHECKING:
    from music_assistant_models.media_items import MediaItemType


@dataclass(kw_only=True)
class TopItemResult(DataClassORJSONMixin):
    """A top played item with its ItemMapping and play count."""

    item: ItemMapping
    play_count: int


@dataclass(kw_only=True)
class TopItem(DataClassORJSONMixin):
    """An item with aggregated play statistics."""

    item_id: str
    provider: str
    media_type: str
    play_count: int
    total_seconds: float
    first_played: float
    last_played: float


@dataclass(kw_only=True)
class DailyStats(DataClassORJSONMixin):
    """Listening statistics for a single day."""

    date: str  # YYYY-MM-DD
    seconds_listened: float
    tracks_played: int
    unique_artists: int


@dataclass(kw_only=True)
class ListeningSummary(DataClassORJSONMixin):
    """Aggregated listening statistics for a time period."""

    period: str
    period_start: float
    period_end: float
    total_listening_seconds: float
    total_plays: int
    unique_tracks: int
    unique_albums: int
    unique_artists: int
    top_genre: str | None = None


@dataclass(kw_only=True)
class DistributionItem(DataClassORJSONMixin):
    """A single item in a distribution chart (e.g., genre or artist distribution)."""

    name: str
    value: int


@dataclass(kw_only=True)
class TimeSeriesPoint(DataClassORJSONMixin):
    """A single point in a time series chart."""

    timestamp: str  # ISO 8601 date string
    value: int


@dataclass(kw_only=True)
class HeatmapPoint(DataClassORJSONMixin):
    """A single point in a heatmap (e.g., listening activity by hour and weekday)."""

    hour: int  # 0-23
    weekday: int  # 0-6 (Monday=0)
    value: int


@dataclass(kw_only=True)
class ListeningTimeItem(DataClassORJSONMixin):
    """An item with total listening time (e.g., artist or genre listening time)."""

    name: str
    minutes: float
