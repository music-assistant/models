"""Tests for config entry types, the storage-only setup_data field and dependency gating."""

from collections.abc import Callable
from typing import Any, cast

import pytest

from music_assistant_models.config_entries import (
    UI_ONLY,
    ConfigEntry,
    ConfigEntryTypeMap,
    ConfigValueType,
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


def test_url_entry_is_ui_only_and_not_required() -> None:
    """A URL entry is one-shot presentational: maps to str, is UI-only and never required."""
    assert ConfigEntryType("url") is ConfigEntryType.URL
    assert ConfigEntryType.URL in UI_ONLY
    assert ConfigEntryTypeMap[ConfigEntryType.URL] is str
    entry = ConfigEntry(
        key="connect_wizard_url",
        type=ConfigEntryType.URL,
        value="https://example.com/connect",
        required=True,
    )
    assert entry.required is False


def test_url_entry_excluded_from_to_raw_values() -> None:
    """A UI-only URL entry is never persisted in Config.to_raw values."""
    entries = [
        ConfigEntry(key="wizard", type=ConfigEntryType.URL, value="https://example.com/x"),
        ConfigEntry(key="server_url", type=ConfigEntryType.STRING),
    ]
    conf = ProviderConfig.parse(entries, _provider_raw(values={"server_url": "abc"}))
    raw = conf.to_raw()
    assert "wizard" not in raw["values"]
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


def _gated(**overrides: Any) -> ConfigEntry:
    """Build a required STRING entry with no default, gated on the `use_proxy` entry."""
    return ConfigEntry(
        key="proxy_url",
        type=ConfigEntryType.STRING,
        required=True,
        depends_on="use_proxy",
        **overrides,
    )


def _switch(*, on: bool) -> ConfigEntry:
    """Build the BOOLEAN entry the gated entry depends on, as it looks once parsed."""
    return ConfigEntry(
        key="use_proxy",
        type=ConfigEntryType.BOOLEAN,
        required=False,
        default_value=on,
        value=on,
    )


def _dependency(value: Any) -> ConfigEntry:
    """Build the dependency as a STRING entry already holding `value`."""
    return ConfigEntry(key="use_proxy", type=ConfigEntryType.STRING, value=value)


def _recording(seen: list[ConfigValueType]) -> Callable[[ConfigValueType], bool]:
    """Build a validation callback that accepts anything and records what it was handed."""

    def _validate(value: ConfigValueType) -> bool:
        seen.append(value)
        return True

    return _validate


def test_dependency_met_without_depends_on() -> None:
    """Report an entry that names no dependency as satisfied."""
    entry = ConfigEntry(key="token", type=ConfigEntryType.STRING)
    assert entry.dependency_met([entry]) is True


def test_dependency_met_follows_the_dependency_value() -> None:
    """Treat any truthy value on the dependency as satisfying it when no bound is given."""
    assert _gated().dependency_met([_switch(on=True), _gated()]) is True
    assert _gated().dependency_met([_switch(on=False), _gated()]) is False


def test_dependency_met_honours_the_value_bounds() -> None:
    """Demand the exact depends_on_value, and forbid the depends_on_value_not."""
    exact = _gated(depends_on_value="ha")
    assert exact.dependency_met([_dependency("ha")]) is True
    assert exact.dependency_met([_dependency("other")]) is False

    inverted = _gated(depends_on_value_not="off")
    assert inverted.dependency_met([_dependency("off")]) is False
    assert inverted.dependency_met([_dependency("ha")]) is True


def test_dependency_met_is_false_for_an_unresolved_key() -> None:
    """Count a dependency key that is not among the entries as unmet."""
    assert _gated().dependency_met([]) is False


def test_validate_skips_a_required_entry_behind_an_unmet_dependency() -> None:
    """Accept a config whose required entry the user has no way to fill in."""
    conf = ProviderConfig.parse([_switch(on=False), _gated()], _provider_raw())

    conf.validate()


def test_validate_enforces_a_required_entry_once_its_dependency_is_met() -> None:
    """Demand the same entry again as soon as its dependency is satisfied."""
    conf = ProviderConfig.parse([_switch(on=True), _gated()], _provider_raw())

    with pytest.raises(ValueError, match="proxy_url is required"):
        conf.validate()


def test_validate_still_enforces_a_required_entry_without_a_dependency() -> None:
    """Reject an ordinary required entry that holds no value."""
    conf = ProviderConfig.parse(
        [ConfigEntry(key="token", type=ConfigEntryType.STRING, required=True)],
        _provider_raw(),
    )

    with pytest.raises(ValueError, match="token is required"):
        conf.validate()


def test_an_entry_without_a_value_never_reaches_its_own_callback() -> None:
    """Keep an entry's validation callback out of the way while it holds no value."""
    seen: list[ConfigValueType] = []
    entries = [
        _switch(on=False),
        # gated and disabled, so the user cannot fill it in
        _gated(validate=_recording(seen)),
        # not gated, but optional and left empty
        ConfigEntry(
            key="chime_url",
            type=ConfigEntryType.STRING,
            required=False,
            validate=_recording(seen),
        ),
    ]

    ProviderConfig.parse(entries, _provider_raw()).validate()

    assert seen == []


def test_validate_accepts_a_gated_entry_whose_callback_assumes_a_value() -> None:
    """Accept a config holding a disabled entry whose callback would choke on an empty value."""
    conf = ProviderConfig.parse(
        [_switch(on=False), _gated(validate=lambda value: cast("str", value).isascii())],
        _provider_raw(),
    )

    conf.validate()

    assert conf.values["proxy_url"].value is None


def test_validate_accepts_a_gated_multi_value_entry() -> None:
    """Accept a disabled entry that expects a list, rather than demanding one."""
    conf = ProviderConfig.parse([_switch(on=False), _gated(multi_value=True)], _provider_raw())

    conf.validate()

    assert conf.values["proxy_url"].value is None


def test_validate_demands_a_gated_multi_value_entry_once_its_dependency_is_met() -> None:
    """Report the same list entry as required as soon as the user can fill it in."""
    conf = ProviderConfig.parse([_switch(on=True), _gated(multi_value=True)], _provider_raw())

    with pytest.raises(ValueError, match="proxy_url is required"):
        conf.validate()


def test_a_supplied_value_is_still_run_through_the_callback() -> None:
    """Keep validating a value the user did give."""
    entry = _gated(validate=lambda value: value == "http://proxy")

    assert entry.parse_value("http://proxy") == "http://proxy"

    with pytest.raises(ValueError, match="is not a valid value for proxy_url"):
        entry.parse_value("http://elsewhere")


def test_a_supplied_value_still_has_to_match_the_entry_shape() -> None:
    """Keep rejecting a value whose shape does not match the entry."""
    with pytest.raises(ValueError, match="value for proxy_url must be a list"):
        _gated(multi_value=True).parse_value("http://proxy")

    with pytest.raises(ValueError, match="proxy_url must be a single value"):
        _gated().parse_value(["http://proxy", "http://elsewhere"])


def test_a_value_of_the_wrong_shape_does_not_reach_the_callback() -> None:
    """Keep the callback out of the way when a value of the wrong shape is dropped."""
    seen: list[ConfigValueType] = []
    entry = ConfigEntry(
        key="proxy_url", type=ConfigEntryType.STRING, required=False, validate=_recording(seen)
    )

    assert entry.parse_value(["http://proxy"], raise_on_error=False) is None
    assert seen == []


def test_a_falsy_value_still_counts_as_a_value() -> None:
    """Treat False and an empty string as values the user gave, not as an empty entry."""
    seen: list[ConfigValueType] = []
    switch = ConfigEntry(
        key="use_proxy", type=ConfigEntryType.BOOLEAN, required=True, validate=_recording(seen)
    )

    assert switch.parse_value(value=False, allow_none=False) is False
    assert seen == [False]

    assert _gated().parse_value("", allow_none=False) == ""
