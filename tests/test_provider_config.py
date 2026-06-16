"""Tests for ProviderConfig structured error and derived status (de)serialization."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from music_assistant_models.config_entries import ProviderConfig, ProviderError
from music_assistant_models.enums import ProviderStatus, ProviderType
from music_assistant_models.translations import TRANSLATION_RESOLVER


@contextmanager
def _resolver_active(catalog: dict[str, str]) -> Iterator[None]:
    """Bind a fake catalog resolver for the duration of the block."""

    def resolve(key: str, owner: str | None = None, params: list[Any] | None = None) -> str | None:
        for candidate in [f"{owner}.{key}", key] if owner else [key]:
            if (value := catalog.get(candidate)) is not None:
                return value.format(*params) if params else value
        return None

    token = TRANSLATION_RESOLVER.set(resolve)
    try:
        yield
    finally:
        TRANSLATION_RESOLVER.reset(token)


def _raw(**overrides: Any) -> dict[str, Any]:
    """Minimal raw ProviderConfig dict as stored in settings.json."""
    return {
        "values": {},
        "type": ProviderType.MUSIC.value,
        "domain": "demo",
        "instance_id": "demo--1",
        **overrides,
    }


def test_legacy_string_last_error_is_coerced() -> None:
    """A legacy string last_error (from older settings.json) deserializes into a ProviderError."""
    conf = ProviderConfig.from_dict(_raw(last_error="kaboom"))
    assert conf.last_error == ProviderError(error_code=999, message="kaboom")


def test_structured_last_error_roundtrips() -> None:
    """A structured last_error survives a from_dict/to_dict round-trip."""
    err = ProviderError(
        error_code=21, message="auth", translation_key="errors.authentication_failed"
    )
    conf = ProviderConfig.from_dict(_raw(last_error=err.to_dict()))
    assert conf.last_error == err
    assert conf.to_dict()["last_error"] == err.to_dict()


def test_status_is_served_but_never_persisted() -> None:
    """The derived status is part of the api payload (to_dict) but excluded from to_raw."""
    conf = ProviderConfig.from_dict(_raw())
    conf.status = ProviderStatus.LOADED
    assert conf.to_dict()["status"] == ProviderStatus.LOADED.value
    assert "status" not in conf.to_raw()


def test_last_error_localized_on_serialize_with_resolver() -> None:
    """With a resolver active, last_error.message is localized and the machinery is stripped."""
    err = ProviderError(
        error_code=26,
        message="raw English",
        translation_key="errors.unsupported_system_cpu",
        translation_args=["Smart Fades", 4, 2],
    )
    conf = ProviderConfig.from_dict(_raw(last_error=err.to_dict()))
    with _resolver_active({"errors.unsupported_system_cpu": "{0} needs {1} cores ({2} detected)"}):
        served = conf.to_dict()["last_error"]
    assert served["message"] == "Smart Fades needs 4 cores (2 detected)"
    assert "translation_key" not in served
    assert "translation_args" not in served


def test_last_error_raw_without_resolver() -> None:
    """Without a resolver (e.g. during persistence) the raw message + machinery are preserved."""
    err = ProviderError(
        error_code=26,
        message="raw English",
        translation_key="errors.unsupported_system_cpu",
        translation_args=["Smart Fades", 4, 2],
    )
    served = ProviderConfig.from_dict(_raw(last_error=err.to_dict())).to_dict()["last_error"]
    assert served["message"] == "raw English"
    assert served["translation_key"] == "errors.unsupported_system_cpu"
    assert served["translation_args"] == ["Smart Fades", 4, 2]
