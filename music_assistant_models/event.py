"""Model for Music Assistant Event."""

from dataclasses import dataclass, field
from typing import Any

from mashumaro.mixins.orjson import DataClassORJSONMixin

from .enums import EventType
from .helpers import get_serializable_value


@dataclass(frozen=True)
class MassEvent(DataClassORJSONMixin):
    """Representation of an Event emitted in/by Music Assistant."""

    event: EventType
    object_id: str | None = None  # player_id, queue_id or uri
    data: Any = field(
        default=None,
        metadata={"serialize": lambda v: get_serializable_value(v)},
    )
