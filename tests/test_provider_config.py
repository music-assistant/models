"""Tests for ProviderConfig structured error, derived status and access record (de)serialization."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from music_assistant_models.config_entries import ProviderAccess, ProviderConfig, ProviderError
from music_assistant_models.enums import ProviderSharing, ProviderStatus, ProviderType
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
    err = ProviderError(error_code=21, message="auth", translation_key="authentication_failed")
    conf = ProviderConfig.from_dict(_raw(last_error=err.to_dict()))
    assert conf.last_error == err
    assert conf.to_dict()["last_error"] == err.to_dict()


def test_last_error_localizes_message_owner_first() -> None:
    """A bare key resolves under errors.<slug>, owner-first then common."""
    catalog = {
        "errors.login_failed": "Inloggen mislukt.",
        "provider.demo.errors.login_failed": "Demo-login mislukt.",
    }
    common = ProviderError(error_code=6, message="login", translation_key="login_failed")
    with _resolver_active(catalog):
        assert common.to_dict()["message"] == "Inloggen mislukt."
    # a provider that owns the key resolves its own message before common
    owned = ProviderError(
        error_code=6,
        message="login",
        translation_key="login_failed",
        translation_owner="provider.demo",
    )
    with _resolver_active(catalog):
        assert owned.to_dict()["message"] == "Demo-login mislukt."


def test_status_is_served_but_never_persisted() -> None:
    """The derived status is part of the api payload (to_dict) but excluded from to_raw."""
    conf = ProviderConfig.from_dict(_raw())
    conf.status = ProviderStatus.LOADED
    assert conf.to_dict()["status"] == ProviderStatus.LOADED.value
    assert "status" not in conf.to_raw()


def test_access_is_persisted_and_served() -> None:
    """The access record is part of both the api payload (to_dict) and the raw storage dict."""
    access = ProviderAccess(owner="user-1", sharing=ProviderSharing.SELECTED, shared_users=["u2"])
    conf = ProviderConfig.from_dict(_raw(access=access.to_dict()))
    assert conf.access == access
    assert conf.to_dict()["access"] == access.to_dict()
    assert conf.to_raw()["access"] == access.to_dict()


def test_missing_access_defaults_to_none() -> None:
    """A legacy raw dict without access deserializes into a household (unowned) provider."""
    assert ProviderConfig.from_dict(_raw()).access is None


def test_unknown_sharing_falls_back_to_private() -> None:
    """An unknown sharing mode falls back to PRIVATE, so access is never widened by accident."""
    assert ProviderAccess.from_dict({"sharing": "future_mode"}).sharing is ProviderSharing.PRIVATE
    conf = ProviderConfig.from_dict(_raw(access={"owner": "user-1", "sharing": "future_mode"}))
    assert conf.access is not None
    assert conf.access.sharing is ProviderSharing.PRIVATE


def test_access_sharing_defaults_to_private() -> None:
    """A record without an explicit sharing mode is private."""
    assert ProviderAccess(owner="user-1").sharing is ProviderSharing.PRIVATE
    assert ProviderAccess.from_dict({"owner": "user-1"}).sharing is ProviderSharing.PRIVATE


def test_last_error_localized_on_serialize_with_resolver() -> None:
    """With a resolver active, last_error.message is localized and the machinery is stripped."""
    err = ProviderError(
        error_code=26,
        message="raw English",
        translation_key="unsupported_system_cpu",
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
        translation_key="unsupported_system_cpu",
        translation_args=["Smart Fades", 4, 2],
    )
    served = ProviderConfig.from_dict(_raw(last_error=err.to_dict())).to_dict()["last_error"]
    assert served["message"] == "raw English"
    assert served["translation_key"] == "unsupported_system_cpu"
    assert served["translation_args"] == ["Smart Fades", 4, 2]
