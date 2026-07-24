"""Tests for DSP models."""

import pytest

from music_assistant_models.dsp import (
    BalanceFilter,
    CompressorFilter,
    ConvolutionFilter,
    CrossfeedFilter,
    DSPConfig,
    DSPFilterType,
    GainFilter,
    HighLowPassFilter,
    HighLowPassMode,
    HighLowPassSlope,
    SafetyLimiterFilter,
    StereoWidthFilter,
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


def test_dsp_config_safety_limiter_compressor_roundtrip() -> None:
    """A DSPConfig with Safety Limiter and Compressor filters round-trips to the correct classes."""
    config = DSPConfig(
        enabled=True,
        filters=[
            SafetyLimiterFilter(enabled=True, ceiling=-3.0),
            CompressorFilter(enabled=False, threshold=-20.0, ratio=4.0),
        ],
    )
    serialized = config.to_dict()

    assert serialized["filters"][0]["type"] == "safety_limiter"
    assert serialized["filters"][1]["type"] == "compressor"

    restored = DSPConfig.from_dict(serialized)

    assert restored == config
    assert isinstance(restored.filters[0], SafetyLimiterFilter)
    assert isinstance(restored.filters[1], CompressorFilter)


def test_dsp_config_stereo_width_crossfeed_roundtrip() -> None:
    """A DSPConfig with StereoWidth and Crossfeed filters round-trips to the correct classes."""
    config = DSPConfig(
        enabled=True,
        filters=[
            StereoWidthFilter(enabled=True, width=1.5),
            CrossfeedFilter(enabled=False, strength=0.4, soundstage=0.6),
        ],
    )
    serialized = config.to_dict()

    assert serialized["filters"][0]["type"] == "stereo_width"
    assert serialized["filters"][1]["type"] == "crossfeed"

    restored = DSPConfig.from_dict(serialized)

    assert restored == config
    assert isinstance(restored.filters[0], StereoWidthFilter)
    assert isinstance(restored.filters[1], CrossfeedFilter)


def test_high_low_pass_valid() -> None:
    """A configured High/Low-pass filter validates without raising."""
    f = HighLowPassFilter(
        enabled=True,
        mode=HighLowPassMode.LOW_PASS,
        frequency=12000.0,
        slope=HighLowPassSlope.DB24,
    )
    f.validate()


def test_high_low_pass_defaults() -> None:
    """High/Low-pass constructs with its documented defaults and validates."""
    f = HighLowPassFilter(enabled=True)

    assert f.type == DSPFilterType.HIGH_LOW_PASS
    assert f.mode is HighLowPassMode.HIGH_PASS
    assert f.frequency == 80.0
    assert f.slope is HighLowPassSlope.DB12

    f.validate()


def test_high_low_pass_bad_frequency() -> None:
    """Cutoff frequencies outside the audible band are rejected."""
    for freq in (10.0, 25000.0):
        with pytest.raises(ValueError, match="Cutoff frequency"):
            HighLowPassFilter(enabled=True, frequency=freq).validate()


def test_high_low_pass_bad_slope() -> None:
    """Slopes outside the allowed {12, 24, 48} set are rejected."""
    for slope in (6, 18, 96, 12.0):
        with pytest.raises(ValueError, match="Slope"):
            HighLowPassFilter(enabled=True, slope=slope).validate()  # type: ignore[arg-type]


def test_high_low_pass_unknown_slope_defaults() -> None:
    """An unknown slope value falls back to 12 dB/octave."""
    assert HighLowPassSlope(18) is HighLowPassSlope.DB12


def test_high_low_pass_slope_serializes_as_int() -> None:
    """The slope stays a plain int on the wire."""
    f = HighLowPassFilter(enabled=True, slope=HighLowPassSlope.DB48)
    serialized = f.to_dict()

    assert serialized["slope"] == 48
    assert type(serialized["slope"]) is int
    assert HighLowPassFilter.from_dict(serialized).slope is HighLowPassSlope.DB48


def test_high_low_pass_unknown_mode_defaults() -> None:
    """An unknown mode value falls back to high-pass."""
    assert HighLowPassMode("sideways") is HighLowPassMode.HIGH_PASS


def test_dsp_config_high_low_pass_roundtrip() -> None:
    """A DSPConfig with a High/Low-pass filter round-trips to the correct class."""
    config = DSPConfig(
        enabled=True,
        filters=[
            HighLowPassFilter(
                enabled=True,
                mode=HighLowPassMode.LOW_PASS,
                frequency=8000.0,
                slope=HighLowPassSlope.DB48,
            ),
        ],
    )
    serialized = config.to_dict()

    assert serialized["filters"][0]["type"] == "high_low_pass"

    restored = DSPConfig.from_dict(serialized)

    assert restored == config
    assert isinstance(restored.filters[0], HighLowPassFilter)


def test_stereo_width_filter_defaults() -> None:
    """Stereo Width constructs with its documented defaults and validates."""
    stereo_width = StereoWidthFilter(enabled=True)

    assert stereo_width.type == "stereo_width"
    assert stereo_width.width == 1.0

    stereo_width.validate()


def test_stereo_width_filter_validate() -> None:
    """Width validates within 0.0..2.0 and rejects values outside."""
    StereoWidthFilter(enabled=True, width=0.0).validate()
    StereoWidthFilter(enabled=True, width=2.0).validate()

    with pytest.raises(ValueError, match="Width"):
        StereoWidthFilter(enabled=True, width=-0.1).validate()
    with pytest.raises(ValueError, match="Width"):
        StereoWidthFilter(enabled=True, width=2.1).validate()


def test_crossfeed_filter_defaults() -> None:
    """Crossfeed constructs with its documented defaults and validates."""
    crossfeed = CrossfeedFilter(enabled=True)

    assert crossfeed.type == "crossfeed"
    assert crossfeed.strength == 0.2
    assert crossfeed.soundstage == 0.5

    crossfeed.validate()


def test_crossfeed_filter_validate() -> None:
    """Each Crossfeed field validates within 0.0..1.0 and rejects values just outside."""
    # An in-range configuration passes.
    CrossfeedFilter(enabled=True, strength=0.5, soundstage=0.5).validate()

    # strength: 0.0 .. 1.0
    CrossfeedFilter(enabled=True, strength=0.0).validate()
    CrossfeedFilter(enabled=True, strength=1.0).validate()
    with pytest.raises(ValueError, match="Strength"):
        CrossfeedFilter(enabled=True, strength=-0.1).validate()
    with pytest.raises(ValueError, match="Strength"):
        CrossfeedFilter(enabled=True, strength=1.1).validate()

    # soundstage: 0.0 .. 1.0
    CrossfeedFilter(enabled=True, soundstage=0.0).validate()
    CrossfeedFilter(enabled=True, soundstage=1.0).validate()
    with pytest.raises(ValueError, match="Soundstage"):
        CrossfeedFilter(enabled=True, soundstage=-0.1).validate()
    with pytest.raises(ValueError, match="Soundstage"):
        CrossfeedFilter(enabled=True, soundstage=1.1).validate()


def test_safety_limiter_filter_defaults() -> None:
    """Safety Limiter constructs with its documented defaults and validates."""
    safety_limiter = SafetyLimiterFilter(enabled=True)

    assert safety_limiter.type == "safety_limiter"
    assert safety_limiter.ceiling == -2.0

    safety_limiter.validate()


def test_safety_limiter_filter_validate() -> None:
    """Ceiling validates within -24..0 dB and rejects values outside."""
    SafetyLimiterFilter(enabled=True, ceiling=-2.0).validate()
    SafetyLimiterFilter(enabled=True, ceiling=-24.0).validate()
    SafetyLimiterFilter(enabled=True, ceiling=0.0).validate()

    with pytest.raises(ValueError, match="Ceiling"):
        SafetyLimiterFilter(enabled=True, ceiling=-24.1).validate()
    with pytest.raises(ValueError, match="Ceiling"):
        SafetyLimiterFilter(enabled=True, ceiling=0.1).validate()


def test_compressor_filter_defaults() -> None:
    """Compressor constructs with its documented defaults and validates."""
    compressor = CompressorFilter(enabled=True)

    assert compressor.type == "compressor"
    assert compressor.threshold == -18.0
    assert compressor.ratio == 2.0
    assert compressor.attack == 20.0
    assert compressor.release == 250.0
    assert compressor.knee == 9.0
    assert compressor.makeup == 0.0

    compressor.validate()


def test_compressor_filter_validate() -> None:
    """Each Compressor field validates within its range and rejects values just outside."""
    # An in-range configuration passes.
    CompressorFilter(
        enabled=True,
        threshold=-24.0,
        ratio=6.0,
        attack=10.0,
        release=100.0,
        knee=6.0,
        makeup=3.0,
    ).validate()

    # threshold: -60.0 .. 0.0 dB
    CompressorFilter(enabled=True, threshold=-60.0).validate()
    CompressorFilter(enabled=True, threshold=0.0).validate()
    with pytest.raises(ValueError, match="Threshold"):
        CompressorFilter(enabled=True, threshold=-60.1).validate()
    with pytest.raises(ValueError, match="Threshold"):
        CompressorFilter(enabled=True, threshold=0.1).validate()

    # ratio: 1.0 .. 20.0
    CompressorFilter(enabled=True, ratio=1.0).validate()
    CompressorFilter(enabled=True, ratio=20.0).validate()
    with pytest.raises(ValueError, match="Ratio"):
        CompressorFilter(enabled=True, ratio=0.9).validate()
    with pytest.raises(ValueError, match="Ratio"):
        CompressorFilter(enabled=True, ratio=20.1).validate()

    # attack: 0.01 .. 2000.0 ms
    CompressorFilter(enabled=True, attack=0.01).validate()
    CompressorFilter(enabled=True, attack=2000.0).validate()
    with pytest.raises(ValueError, match="Attack"):
        CompressorFilter(enabled=True, attack=0.0).validate()
    with pytest.raises(ValueError, match="Attack"):
        CompressorFilter(enabled=True, attack=2000.1).validate()

    # release: 0.01 .. 9000.0 ms
    CompressorFilter(enabled=True, release=0.01).validate()
    CompressorFilter(enabled=True, release=9000.0).validate()
    with pytest.raises(ValueError, match="Release"):
        CompressorFilter(enabled=True, release=0.0).validate()
    with pytest.raises(ValueError, match="Release"):
        CompressorFilter(enabled=True, release=9000.1).validate()

    # knee: 0.0 .. 18.0 dB
    CompressorFilter(enabled=True, knee=0.0).validate()
    CompressorFilter(enabled=True, knee=18.0).validate()
    with pytest.raises(ValueError, match="Knee"):
        CompressorFilter(enabled=True, knee=-0.1).validate()
    with pytest.raises(ValueError, match="Knee"):
        CompressorFilter(enabled=True, knee=18.1).validate()

    # makeup: 0.0 .. 36.0 dB
    CompressorFilter(enabled=True, makeup=0.0).validate()
    CompressorFilter(enabled=True, makeup=36.0).validate()
    with pytest.raises(ValueError, match="Make-up gain"):
        CompressorFilter(enabled=True, makeup=-0.1).validate()
    with pytest.raises(ValueError, match="Make-up gain"):
        CompressorFilter(enabled=True, makeup=36.1).validate()
