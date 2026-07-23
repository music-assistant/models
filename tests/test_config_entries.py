"""Tests for the IMAGE config entry type and the storage-only setup_data field."""

from typing import Any

from music_assistant_models.config_entries import (
    UI_ONLY,
    ConfigEntry,
    ConfigEntryTypeMap,
    PlayerConfig,
    ProviderConfig,
)
from music_assistant_models.enums import ConfigEntryType, ProviderType


def _provider_raw(**overrides: Any) -> dict[str, Any]:
    """Minimal raw ProviderConfig dict as stored in settings.json."""
    return {
        "values": {},
        "type": ProviderType.MUSIC.value,
        "domain": "demo",
        "instance_id": "demo--1",
        **overrides,
    }


def _player_raw(**overrides: Any) -> dict[str, Any]:
    """Minimal raw PlayerConfig dict as stored in settings.json."""
    return {
        "values": {},
        "provider": "demo",
        "player_id": "demo--player-1",
        **overrides,
    }


def test_config_entry_type_unknown_fallback() -> None:
    """IMAGE is a known ConfigEntryType member; an unknown value falls back to UNKNOWN."""
    assert ConfigEntryType("image") is ConfigEntryType.IMAGE
    assert ConfigEntryType("does-not-exist") is ConfigEntryType.UNKNOWN


def test_image_entry_is_ui_only_and_not_required() -> None:
    """An IMAGE entry is presentational: maps to str, is UI-only and never required."""
    assert ConfigEntryType.IMAGE in UI_ONLY
    assert ConfigEntryTypeMap[ConfigEntryType.IMAGE] is str
    entry = ConfigEntry(
        key="qr",
        type=ConfigEntryType.IMAGE,
        default_value="data:image/png;base64,AAAA",
        required=True,
    )
    # __post_init__ forces required False for UI-only entries, even when constructed required
    assert entry.required is False


def test_image_entry_excluded_from_to_raw_values() -> None:
    """A UI-only IMAGE entry is never persisted in Config.to_raw values."""
    entries = [
        ConfigEntry(
            key="qr", type=ConfigEntryType.IMAGE, default_value="data:image/png;base64,AAAA"
        ),
        ConfigEntry(key="server_url", type=ConfigEntryType.STRING),
    ]
    conf = ProviderConfig.parse(entries, _provider_raw(values={"server_url": "abc"}))
    raw = conf.to_raw()
    assert "qr" not in raw["values"]
    assert raw["values"]["server_url"] == "abc"


def test_provider_setup_data_parses_roundtrips_and_drops_on_api() -> None:
    """ProviderConfig.setup_data is parsed, persisted via to_raw, but dropped from to_dict."""
    conf = ProviderConfig.parse([], _provider_raw(setup_data={"token": "enc:secret"}))
    assert conf.setup_data == {"token": "enc:secret"}
    # persisted (to_raw) keeps it
    assert conf.to_raw()["setup_data"] == {"token": "enc:secret"}
    # api payload (to_dict) never exposes it
    assert "setup_data" not in conf.to_dict()


def test_provider_legacy_raw_without_setup_data_parses() -> None:
    """A legacy ProviderConfig store without setup_data parses to an empty dict."""
    conf = ProviderConfig.parse([], _provider_raw())
    assert conf.setup_data == {}
    assert conf.to_raw()["setup_data"] == {}
    assert "setup_data" not in conf.to_dict()


def test_player_setup_data_parses_roundtrips_and_drops_on_api() -> None:
    """PlayerConfig.setup_data is parsed, persisted via to_raw, but dropped from to_dict."""
    conf = PlayerConfig.parse([], _player_raw(setup_data={"paired": "enc:key"}))
    assert conf.setup_data == {"paired": "enc:key"}
    assert conf.to_raw()["setup_data"] == {"paired": "enc:key"}
    assert "setup_data" not in conf.to_dict()


def test_player_legacy_raw_without_setup_data_parses() -> None:
    """A legacy PlayerConfig store without setup_data parses to an empty dict."""
    conf = PlayerConfig.parse([], _player_raw())
    assert conf.setup_data == {}
    assert conf.to_raw()["setup_data"] == {}
    assert "setup_data" not in conf.to_dict()
