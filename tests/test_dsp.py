"""Tests for DSP models."""

import pytest

from music_assistant_models.dsp import (
    BalanceFilter,
    ConvolutionFilter,
    DSPConfig,
    DSPFilterType,
    GainFilter,
    HighLowPassFilter,
    HighLowPassMode,
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


def test_convolution_filter_defaults() -> None:
    """Convolution constructs with its documented defaults and validates."""
    convolution = ConvolutionFilter(enabled=True)

    assert convolution.type == DSPFilterType.CONVOLUTION
    assert convolution.ir_id == ""
    assert convolution.gain == 0.0

    convolution.validate()


def test_convolution_filter_validate() -> None:
    """Gain validates within +-60 dB and rejects values outside."""
    ConvolutionFilter(enabled=True, gain=-60.0).validate()
    ConvolutionFilter(enabled=True, gain=60.0).validate()

    with pytest.raises(ValueError, match="Gain"):
        ConvolutionFilter(enabled=True, gain=-60.1).validate()
    with pytest.raises(ValueError, match="Gain"):
        ConvolutionFilter(enabled=True, gain=60.1).validate()


def test_dsp_config_convolution_roundtrip() -> None:
    """A DSPConfig with a Convolution filter round-trips to the correct class."""
    config = DSPConfig(
        enabled=True,
        filters=[
            ConvolutionFilter(enabled=True, ir_id="ir-abc123", gain=-3.0),
        ],
    )
    serialized = config.to_dict()

    assert serialized["filters"][0]["type"] == "convolution"

    restored = DSPConfig.from_dict(serialized)

    assert restored == config
    assert isinstance(restored.filters[0], ConvolutionFilter)


def test_high_low_pass_valid() -> None:
    """A configured High/Low-pass filter validates without raising."""
    f = HighLowPassFilter(enabled=True, mode=HighLowPassMode.LOW_PASS, frequency=12000.0, slope=24)
    f.validate()


def test_high_low_pass_defaults() -> None:
    """High/Low-pass constructs with its documented defaults and validates."""
    f = HighLowPassFilter(enabled=True)

    assert f.type == DSPFilterType.HIGH_LOW_PASS
    assert f.mode is HighLowPassMode.HIGH_PASS
    assert f.frequency == 80.0
    assert f.slope == 12

    f.validate()


def test_high_low_pass_bad_frequency() -> None:
    """Cutoff frequencies outside the audible band are rejected."""
    for freq in (10.0, 25000.0):
        with pytest.raises(ValueError, match="Cutoff frequency"):
            HighLowPassFilter(enabled=True, frequency=freq).validate()


def test_high_low_pass_bad_slope() -> None:
    """Slopes outside the allowed {12, 24, 48} set are rejected."""
    for slope in (6, 18, 96):
        with pytest.raises(ValueError, match="Slope"):
            HighLowPassFilter(enabled=True, slope=slope).validate()


def test_high_low_pass_unknown_mode_defaults() -> None:
    """An unknown mode value falls back to high-pass."""
    assert HighLowPassMode("sideways") is HighLowPassMode.HIGH_PASS


def test_dsp_config_high_low_pass_roundtrip() -> None:
    """A DSPConfig with a High/Low-pass filter round-trips to the correct class."""
    config = DSPConfig(
        enabled=True,
        filters=[
            HighLowPassFilter(
                enabled=True, mode=HighLowPassMode.LOW_PASS, frequency=8000.0, slope=48
            ),
        ],
    )
    serialized = config.to_dict()

    assert serialized["filters"][0]["type"] == "high_low_pass"

    restored = DSPConfig.from_dict(serialized)

    assert restored == config
    assert isinstance(restored.filters[0], HighLowPassFilter)
