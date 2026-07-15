"""Tests for DSP models."""

import pytest

from music_assistant_models.dsp import (
    BalanceFilter,
    DSPConfig,
    GainFilter,
)


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
    """Gain validates within +-15 dB and rejects values outside."""
    GainFilter(enabled=True).validate()
    GainFilter(enabled=True, gain=-15.0).validate()
    GainFilter(enabled=True, gain=15.0).validate()

    with pytest.raises(ValueError, match="Gain"):
        GainFilter(enabled=True, gain=-15.1).validate()
    with pytest.raises(ValueError, match="Gain"):
        GainFilter(enabled=True, gain=15.1).validate()


def test_balance_filter_validate() -> None:
    """Balance validates within +-100 and rejects values outside."""
    BalanceFilter(enabled=True).validate()
    BalanceFilter(enabled=True, balance=-100.0).validate()
    BalanceFilter(enabled=True, balance=100.0).validate()

    with pytest.raises(ValueError, match="Balance"):
        BalanceFilter(enabled=True, balance=-100.1).validate()
    with pytest.raises(ValueError, match="Balance"):
        BalanceFilter(enabled=True, balance=100.1).validate()
