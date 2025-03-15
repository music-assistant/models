"""Models for the builtin player provider."""

from dataclasses import dataclass

from mashumaro import DataClassDictMixin

from .enums import BuiltinPlayerEventType


@dataclass
class BuiltinPlayerEvent(DataClassDictMixin):
    """Model for events sent to the builtin (web) player."""

    type: BuiltinPlayerEventType
    volume: int | None = None  # set if action is SET_VOLUME
    media_url: str | None = None  # set if action is PLAY_MEDIA


@dataclass
class BuiltinPlayerState(DataClassDictMixin):
    """Model for state updates from the builtin (web) player."""

    powered: bool
    playing: bool
    paused: bool
    position: int
    volume: int
    muted: bool
