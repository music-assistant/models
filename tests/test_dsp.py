"""Tests for DSP models."""

from music_assistant_models.dsp import DSPConfig


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
