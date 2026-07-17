"""Tests for DSP models."""

import pytest

from music_assistant_models.dsp import (
    BalanceFilter,
    DSPConfig,
    GainFilter,
)


def test_dsp_config_defaults() -> None:
    """DSP config serializes the default preset identity."""
    config = DSPConfig()

    assert config.to_dict() == {
        "enabled": False,
        "filters": [],
        "input_gain": 0.0,
        "output_gain": 0.0,
        "preset_id": None,
    }


def test_dsp_config_legacy_payload() -> None:
    """DSP config accepts payloads without a preset ID."""
    payload = {
        "enabled": True,
        "filters": [],
        "input_gain": -1.0,
        "output_gain": 2.0,
    }

    config = DSPConfig.from_dict(payload)

    assert config.preset_id is None
    assert config == DSPConfig(enabled=True, input_gain=-1.0, output_gain=2.0)


def test_dsp_config_preset_id_roundtrip() -> None:
    """DSP config retains a non-null preset ID."""
    config = DSPConfig(preset_id="preset-1")
    payload = config.to_dict()

    assert payload["preset_id"] == "preset-1"
    assert DSPConfig.from_dict(payload) == config


def test_dsp_config_gain_balance_roundtrip() -> None:
    """A DSPConfig with Gain and Balance filters round-trips to the correct classes."""
    config = DSPConfig(
        enabled=True,
        filters=[
            GainFilter(enabled=True, gain=-3.5),
            BalanceFilter(enabled=False, balance=25.0),
        ],
    )
    serialized = config.to_dict()

    assert serialized["filters"][0]["type"] == "gain"
    assert serialized["filters"][1]["type"] == "balance"

    restored = DSPConfig.from_dict(serialized)

    assert restored == config
    assert isinstance(restored.filters[0], GainFilter)
    assert isinstance(restored.filters[1], BalanceFilter)


def test_gain_filter_validate() -> None:
    """Gain validates within +-60 dB and rejects values outside."""
    GainFilter(enabled=True).validate()
    GainFilter(enabled=True, gain=-60.0).validate()
    GainFilter(enabled=True, gain=60.0).validate()

    with pytest.raises(ValueError, match="Gain"):
        GainFilter(enabled=True, gain=-60.1).validate()
    with pytest.raises(ValueError, match="Gain"):
        GainFilter(enabled=True, gain=60.1).validate()


def test_balance_filter_validate() -> None:
    """Balance validates within +-100 and rejects values outside."""
    BalanceFilter(enabled=True).validate()
    BalanceFilter(enabled=True, balance=-100.0).validate()
    BalanceFilter(enabled=True, balance=100.0).validate()

    with pytest.raises(ValueError, match="Balance"):
        BalanceFilter(enabled=True, balance=-100.1).validate()
    with pytest.raises(ValueError, match="Balance"):
        BalanceFilter(enabled=True, balance=100.1).validate()
