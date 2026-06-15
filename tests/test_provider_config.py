"""Tests for ProviderConfig structured error and derived status (de)serialization."""

from typing import Any

from music_assistant_models.config_entries import ProviderConfig, ProviderError
from music_assistant_models.enums import ProviderStatus, ProviderType


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
