"""Generic models used for the (websockets) API communication."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mashumaro.mixins.orjson import DataClassORJSONMixin

from music_assistant_models.enums import CoreState

from .event import MassEvent
from .helpers import get_serializable_value
from .translations import resolve_translation, translations_active


@dataclass
class CommandMessage(DataClassORJSONMixin):
    """Model for a Message holding a command from server to client or client to server."""

    message_id: str
    command: str
    args: dict[str, Any] | None = None


@dataclass
class ResultMessageBase(DataClassORJSONMixin):
    """Base class for a result/response of a Command Message."""

    message_id: str


@dataclass
class SuccessResultMessage(ResultMessageBase):
    """Message sent when a Command has been successfully executed."""

    result: Any = field(default=None, metadata={"serialize": lambda v: get_serializable_value(v)})
    partial: bool = False


@dataclass
class ErrorResultMessage(ResultMessageBase):
    """Message sent when a command did not execute successfully."""

    error_code: int
    details: str | None = None
    # translation_key (a bare slug) + translation_args + translation_owner localize `details` for
    # the connection's locale during outbound API serialization: __post_serialize__ derives the
    # `errors.<slug>` group and resolves it owner-first then against common. All three are stripped
    # from the client payload when a resolver is active.
    translation_key: str | None = None
    translation_args: list[Any] = field(default_factory=list)
    translation_owner: str | None = None

    def __post_serialize__(self, d: dict[str, Any]) -> dict[str, Any]:
        """Localize `details` from the translation_key when a resolver is active."""
        if self.translation_key:
            params = [str(a) for a in self.translation_args] if self.translation_args else None
            localized = resolve_translation(
                f"errors.{self.translation_key}", owner=self.translation_owner, params=params
            )
            if localized is not None:
                d["details"] = localized
        if translations_active():
            d.pop("translation_key", None)
            d.pop("translation_args", None)
            d.pop("translation_owner", None)
        return d


# EventMessage is the same as MassEvent, this is just a alias.
EventMessage = MassEvent


@dataclass
class ServerInfoMessage(DataClassORJSONMixin):
    """Message sent by the server with it's info when a client connects."""

    server_id: str
    server_version: str
    schema_version: int
    min_supported_schema_version: int
    base_url: str | None = None  # deprecated, use internal_url instead
    homeassistant_addon: bool = False
    onboard_done: bool = False
    name: str | None = None  # added in schema version 29 (MA v2.8)
    status: CoreState = CoreState.RUNNING  # added in schema version 29 (MA v2.8)
    internal_url: str | None = None  # added in schema version 32 (MA v2.10)
    external_url: str | None = None  # added in schema version 32 (MA v2.10)
    has_remote_access: bool = False  # added in schema version 32 (MA v2.10)

    @classmethod
    def __post_serialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Adjust dict object after it has been serialized."""
        # add alias for base_url if internal_url is not None, for backwards compatibility
        if d.get("internal_url") is not None and d.get("base_url") is None:
            d["base_url"] = d["internal_url"]
        # add alias for internal_url, for backwards compatibility
        if d.get("base_url") is not None and d.get("internal_url") is None:
            d["internal_url"] = d["base_url"]
        return d

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Adjust object before it will be deserialized."""
        # add alias for base_url if internal_url is not None, for backwards compatibility
        if d.get("internal_url") is not None and d.get("base_url") is None:
            d["base_url"] = d["internal_url"]
        # add alias for internal_url, for backwards compatibility
        if d.get("base_url") is not None and d.get("internal_url") is None:
            d["internal_url"] = d["base_url"]
        return d


MessageType = (
    CommandMessage | EventMessage | SuccessResultMessage | ErrorResultMessage | ServerInfoMessage
)


def parse_message(raw: dict[Any, Any]) -> MessageType:
    """Parse Message from raw dict object."""
    if "event" in raw:
        return EventMessage.from_dict(raw)
    if "error_code" in raw:
        return ErrorResultMessage.from_dict(raw)
    if "result" in raw:
        return SuccessResultMessage.from_dict(raw)
    if "sdk_version" in raw:
        return ServerInfoMessage.from_dict(raw)
    return CommandMessage.from_dict(raw)
