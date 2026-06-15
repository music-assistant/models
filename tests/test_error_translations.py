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
    """Each standard error type carries its default translation key; the base stays None."""
    assert MusicAssistantError.translation_key is None
    assert ProviderUnavailableError.translation_key == "errors.provider_unavailable"
    assert MediaNotFoundError.translation_key == "errors.media_not_found"
    assert InvalidToken.translation_key == "errors.invalid_token"
    # RateLimited subclasses ResourceTemporarilyUnavailable but defines its own key
    assert RateLimited.translation_key == "errors.rate_limited"
    # UnsupportedSystemError subclasses SetupFailedError but defines its own key
    assert UnsupportedSystemError.translation_key == "errors.unsupported_system"
    # default key is readable on an instance too
    assert ProviderUnavailableError("boom").translation_key == "errors.provider_unavailable"


def test_error_per_instance_override() -> None:
    """A per-instance translation_key/args overrides the type default; backoff is preserved."""
    err = MediaNotFoundError(
        "not found", translation_key="provider.demo.errors.x", translation_args=["a"]
    )
    assert err.translation_key == "provider.demo.errors.x"
    assert err.translation_args == ["a"]
    # custom-__init__ error forwards the translation kwargs and keeps backoff_time
    rate = RateLimited("Spotify", backoff_time=30, translation_args=["Spotify"])
    assert rate.translation_key == "errors.rate_limited"
    assert rate.backoff_time == 30
    assert rate.translation_args == ["Spotify"]
    # raised with only a backoff and no message: str() is empty, default key carries the text
    empty = ResourceTemporarilyUnavailable(backoff_time=5)
    assert str(empty) == ""
    assert empty.translation_key == "errors.resource_temporarily_unavailable"


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
    msg = ErrorResultMessage(
        "abc", 2, "Track 123 not found", translation_key="errors.media_not_found"
    )
    with _resolver_active():
        d = msg.to_dict()
    assert d["details"] == "Track 123 not found"
    assert "translation_key" not in d


def test_error_result_message_plain_to_dict_keeps_machinery() -> None:
    """Without a resolver bound the message keeps details + machinery (round-trip safe)."""
    msg = ErrorResultMessage(
        "abc", 1, "Spotify is offline", translation_key="errors.provider_unavailable"
    )
    d = msg.to_dict()
    assert d["details"] == "Spotify is offline"
    assert d["translation_key"] == "errors.provider_unavailable"
    assert d["translation_args"] == []


def test_error_result_message_substitutes_params() -> None:
    """Positional translation_args fill {0}/{1} placeholders in the localized message."""
    msg = ErrorResultMessage(
        "abc", 2, "raw", translation_key="errors.media_count", translation_args=[3]
    )
    with _resolver_active():
        d = msg.to_dict()
    assert d["details"] == "3 items niet gevonden"


def test_error_map_still_registers_all_subclasses() -> None:
    """Adding the translation key does not disturb error_code registration."""
    assert ERROR_MAP[1] is ProviderUnavailableError
    assert ERROR_MAP[25] is RateLimited
    assert ERROR_MAP[26] is UnsupportedSystemError
