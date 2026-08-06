"""Tests for the one-shot config action result and its message localization."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from music_assistant_models.config_entries import ConfigActionResult
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


def test_empty_result_serializes_without_a_message_or_url() -> None:
    """A result that reports nothing carries no message and no url."""
    payload = ConfigActionResult().to_dict()

    assert payload["message"] is None
    assert payload["open_url"] is None


def test_plain_message_is_served_as_is() -> None:
    """A computed message (no translation key) reaches the client unchanged."""
    result = ConfigActionResult(message="Certificate verification: VALID")

    with _resolver_active({}):
        assert result.to_dict()["message"] == "Certificate verification: VALID"


def test_message_localizes_under_config_actions_owner_first() -> None:
    """A bare key resolves under config_actions.<slug>, owner-first then common."""
    catalog = {
        "config_actions.clear_cache.result": "De cache is geleegd",
        "core.cache.config_actions.clear_cache.result": "De cache van de kern is geleegd",
    }
    common = ConfigActionResult(message="cleared", translation_key="clear_cache.result")
    with _resolver_active(catalog):
        assert common.to_dict()["message"] == "De cache is geleegd"
    # a module that owns the key resolves its own message before common
    owned = ConfigActionResult(
        message="cleared",
        translation_key="clear_cache.result",
        translation_owner="core.cache",
    )
    with _resolver_active(catalog):
        assert owned.to_dict()["message"] == "De cache van de kern is geleegd"


def test_message_keeps_its_english_value_when_the_key_is_unknown() -> None:
    """An unresolvable key leaves the in-code English message in place."""
    result = ConfigActionResult(message="The cache has been cleared", translation_key="nope")

    with _resolver_active({}):
        assert result.to_dict()["message"] == "The cache has been cleared"


def test_translation_args_fill_the_message_placeholders() -> None:
    """Positional translation args are applied to the resolved message."""
    result = ConfigActionResult(
        message="Removed 3 items",
        translation_key="cleanup.result",
        translation_args=[3],
    )

    with _resolver_active({"config_actions.cleanup.result": "{0} items verwijderd"}):
        assert result.to_dict()["message"] == "3 items verwijderd"


def test_translation_machinery_is_stripped_from_the_api_payload() -> None:
    """With a resolver active the localization fields are not served to the client."""
    result = ConfigActionResult(
        message="cleared",
        translation_key="clear_cache.result",
        translation_owner="core.cache",
    )

    with _resolver_active({"core.cache.config_actions.clear_cache.result": "Geleegd"}):
        payload = result.to_dict()

    assert payload == {"message": "Geleegd", "open_url": None}


def test_translation_machinery_is_kept_without_a_resolver() -> None:
    """A plain to_dict (no outbound serialization) keeps the localization fields."""
    payload = ConfigActionResult(message="cleared", translation_key="clear_cache.result").to_dict()

    assert payload["translation_key"] == "clear_cache.result"
    assert payload["translation_args"] == []
    assert payload["translation_owner"] is None


def test_open_url_survives_serialization() -> None:
    """A url-only result serializes its url for the client to open."""
    payload = ConfigActionResult(open_url="https://example.org/connect").to_dict()

    assert payload["open_url"] == "https://example.org/connect"
    assert payload["message"] is None
