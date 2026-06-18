"""Tests for localized MusicAssistantError messages on ErrorResultMessage."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from music_assistant_models.api import ErrorResultMessage
from music_assistant_models.errors import (
    ERROR_MAP,
    InvalidToken,
    MediaNotFoundError,
    MusicAssistantError,
    ProviderUnavailableError,
    RateLimited,
    ResourceTemporarilyUnavailable,
    UnsupportedSystemError,
)
from music_assistant_models.translations import TRANSLATION_RESOLVER

# the strings a bound resolver would return for the keys the error message looks up
_CATALOG = {
    "errors.provider_unavailable": "De provider is niet beschikbaar.",
    "errors.media_count": "{0} items niet gevonden",
    "errors.login_failed": "Inloggen mislukt.",
    "provider.demo.errors.login_failed": "Demo-login mislukt.",
}


@contextmanager
def _resolver_active() -> Iterator[None]:
    """Bind a fake catalog resolver for the duration of the block."""

    def resolve(key: str, owner: str | None = None, params: list[Any] | None = None) -> str | None:
        for candidate in [f"{owner}.{key}", key] if owner else [key]:
            if (value := _CATALOG.get(candidate)) is not None:
                return value.format(*params) if params else value
        return None

    token = TRANSLATION_RESOLVER.set(resolve)
    try:
        yield
    finally:
        TRANSLATION_RESOLVER.reset(token)


def test_error_subclasses_expose_default_translation_key() -> None:
    """Each standard error type carries its default (bare) translation key; the base stays None."""
    assert MusicAssistantError.translation_key is None
    assert MusicAssistantError.translation_owner is None
    assert ProviderUnavailableError.translation_key == "provider_unavailable"
    assert MediaNotFoundError.translation_key == "media_not_found"
    assert InvalidToken.translation_key == "invalid_token"
    # RateLimited subclasses ResourceTemporarilyUnavailable but defines its own key
    assert RateLimited.translation_key == "rate_limited"
    # UnsupportedSystemError subclasses SetupFailedError but defines its own key
    assert UnsupportedSystemError.translation_key == "unsupported_system"
    # default key is readable on an instance too
    assert ProviderUnavailableError("boom").translation_key == "provider_unavailable"


def test_error_per_instance_override() -> None:
    """A per-instance translation_key/args/owner overrides the type default; backoff kept."""
    err = MediaNotFoundError(
        "not found",
        translation_key="custom_not_found",
        translation_args=["a"],
        translation_owner="provider.demo",
    )
    assert err.translation_key == "custom_not_found"
    assert err.translation_args == ["a"]
    assert err.translation_owner == "provider.demo"
    # custom-__init__ error forwards the translation kwargs and keeps backoff_time
    rate = RateLimited("Spotify", backoff_time=30, translation_args=["Spotify"])
    assert rate.translation_key == "rate_limited"
    assert rate.translation_owner is None
    assert rate.backoff_time == 30
    assert rate.translation_args == ["Spotify"]
    # raised with only a backoff and no message: str() is empty, default key carries the text
    empty = ResourceTemporarilyUnavailable(backoff_time=5)
    assert str(empty) == ""
    assert empty.translation_key == "resource_temporarily_unavailable"


def test_error_result_message_localizes_details_and_strips_machinery() -> None:
    """A bound resolver replaces `details` and strips the translation machinery from the wire."""
    err = ProviderUnavailableError("Spotify is offline")
    msg = ErrorResultMessage(
        "abc",
        err.error_code,
        str(err),
        translation_key=err.translation_key,
        translation_args=err.translation_args,
    )
    with _resolver_active():
        d = msg.to_dict()
    assert d["details"] == "De provider is niet beschikbaar."
    assert d["error_code"] == 1
    assert d["message_id"] == "abc"
    # machinery never reaches the client when a resolver is active
    assert "translation_key" not in d
    assert "translation_args" not in d


def test_error_result_message_unknown_key_keeps_details() -> None:
    """When the key does not resolve, the in-code `details` (str(err)) is kept."""
    msg = ErrorResultMessage("abc", 2, "Track 123 not found", translation_key="media_not_found")
    with _resolver_active():
        d = msg.to_dict()
    assert d["details"] == "Track 123 not found"
    assert "translation_key" not in d


def test_error_result_message_plain_to_dict_keeps_machinery() -> None:
    """Without a resolver bound the message keeps details + machinery (round-trip safe)."""
    msg = ErrorResultMessage("abc", 1, "Spotify is offline", translation_key="provider_unavailable")
    d = msg.to_dict()
    assert d["details"] == "Spotify is offline"
    assert d["translation_key"] == "provider_unavailable"
    assert d["translation_args"] == []


def test_error_result_message_substitutes_params() -> None:
    """Positional translation_args fill {0}/{1} placeholders in the localized message."""
    msg = ErrorResultMessage("abc", 2, "raw", translation_key="media_count", translation_args=[3])
    with _resolver_active():
        d = msg.to_dict()
    assert d["details"] == "3 items niet gevonden"


def test_error_result_message_resolves_owner_before_common() -> None:
    """A provider-owned error resolves its own message first; without an owner it hits common."""
    owned = ErrorResultMessage(
        "abc", 6, "raw", translation_key="login_failed", translation_owner="provider.demo"
    )
    with _resolver_active():
        d = owned.to_dict()
    assert d["details"] == "Demo-login mislukt."
    assert "translation_owner" not in d
    # the same bare key with no owner falls back to the shared common string
    common = ErrorResultMessage("abc", 6, "raw", translation_key="login_failed")
    with _resolver_active():
        d = common.to_dict()
    assert d["details"] == "Inloggen mislukt."


def test_error_map_still_registers_all_subclasses() -> None:
    """Adding the translation key does not disturb error_code registration."""
    assert ERROR_MAP[1] is ProviderUnavailableError
    assert ERROR_MAP[25] is RateLimited
    assert ERROR_MAP[26] is UnsupportedSystemError
