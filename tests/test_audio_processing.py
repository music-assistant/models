"""Tests for audio processing models."""

from music_assistant_models.audio_processing import (
    AudioDSPDetails,
    AudioFidelity,
    AudioNormalizationDetails,
    AudioNormalizationMeasurementSource,
    AudioOutputDetails,
    AudioProcessingChain,
    AudioQuality,
    AudioQueueProcessing,
)
from music_assistant_models.dsp import AudioChannel, DSPState, ToneControlFilter
from music_assistant_models.enums import (
    ContentType,
    CrossfadeMode,
    VolumeNormalizationMode,
)
from music_assistant_models.helpers import get_serializable_value
from music_assistant_models.media_items import AudioFormat
from music_assistant_models.streamdetails import StreamDetails


def test_audio_processing_defaults() -> None:
    """All audio processing models have safe defaults."""
    chain = AudioProcessingChain()

    assert chain.to_dict() == {
        "input_fidelity": {"quality": "unknown", "bit_perfect": None},
        "queue_processing": None,
        "outputs": [],
    }
    assert AudioProcessingChain.from_dict({}) == chain
    assert AudioNormalizationDetails().to_dict() == {
        "mode": "unknown",
        "measurement_source": "unknown",
        "target_lufs": None,
        "measured_lufs": None,
        "applied_gain_db": None,
    }
    assert AudioQueueProcessing().to_dict() == {
        "pcm_format": None,
        "normalization": None,
        "playback_speed": 1.0,
        "crossfade_mode": "disabled",
        "overlay_active": False,
    }
    assert AudioDSPDetails().to_dict() == {
        "state": "unknown",
        "input_gain": 0.0,
        "filters": [],
        "output_gain": 0.0,
        "output_limiter": False,
        "preset_id": None,
    }
    assert AudioOutputDetails().to_dict() == {
        "player_ids": [],
        "dsp": {
            "state": "unknown",
            "input_gain": 0.0,
            "filters": [],
            "output_gain": 0.0,
            "output_limiter": False,
            "preset_id": None,
        },
        "source_channel": None,
        "output_format": None,
        "fidelity": {"quality": "unknown", "bit_perfect": None},
    }
    assert [quality.value for quality in AudioQuality] == [
        "unknown",
        "low",
        "standard",
        "lossless",
        "hi_res",
    ]
    assert [source.value for source in AudioNormalizationMeasurementSource] == [
        "unknown",
        "track",
        "album",
        "live",
        "fallback",
    ]


def test_audio_processing_roundtrip() -> None:
    """A populated chain retains its compact wire shape."""
    chain = _full_chain()
    serialized = chain.to_dict()
    queue_processing = serialized["queue_processing"]
    output = serialized["outputs"][0]

    assert set(serialized) == {"input_fidelity", "queue_processing", "outputs"}
    assert set(queue_processing) == {
        "pcm_format",
        "normalization",
        "playback_speed",
        "crossfade_mode",
        "overlay_active",
    }
    assert set(queue_processing["normalization"]) == {
        "mode",
        "measurement_source",
        "target_lufs",
        "measured_lufs",
        "applied_gain_db",
    }
    assert set(output) == {
        "player_ids",
        "dsp",
        "source_channel",
        "output_format",
        "fidelity",
    }
    assert set(output["dsp"]) == {
        "state",
        "input_gain",
        "filters",
        "output_gain",
        "output_limiter",
        "preset_id",
    }
    assert output["dsp"]["preset_id"] == "preset-1"
    assert get_serializable_value(chain) == serialized
    assert AudioProcessingChain.from_dict(serialized) == chain


def test_audio_dsp_details_legacy_payload() -> None:
    """Audio DSP details accept payloads without a preset ID."""
    payload = {
        "state": "enabled",
        "input_gain": -1.0,
        "filters": [],
        "output_gain": -0.5,
        "output_limiter": True,
    }

    details = AudioDSPDetails.from_dict(payload)

    assert details.preset_id is None
    assert details == AudioDSPDetails(
        state=DSPState.ENABLED,
        input_gain=-1.0,
        output_gain=-0.5,
        output_limiter=True,
    )


def test_streamdetails_audio_processing_defaults_to_none() -> None:
    """Stream details omit a chain until one is available."""
    streamdetails = _streamdetails()
    serialized = streamdetails.to_dict()

    assert streamdetails.audio_processing is None
    assert serialized["audio_processing"] is None
    assert StreamDetails.from_dict(serialized) == streamdetails


def test_streamdetails_audio_processing_roundtrip() -> None:
    """Stream details round-trip a complete nested chain."""
    streamdetails = _streamdetails(audio_processing=_full_chain())
    serialized = streamdetails.to_dict()

    assert streamdetails.audio_processing is not None
    assert serialized["audio_processing"] == streamdetails.audio_processing.to_dict()
    assert serialized["audio_processing"]["outputs"][0]["dsp"]["preset_id"] == "preset-1"
    assert StreamDetails.from_dict(serialized) == streamdetails


def test_unknown_audio_processing_enums_fall_back() -> None:
    """Unknown enum values deserialize to forward-compatible fallbacks."""
    payload = _full_chain().to_dict()
    payload["input_fidelity"]["quality"] = "future"
    payload["queue_processing"]["normalization"]["mode"] = "future"
    payload["queue_processing"]["normalization"]["measurement_source"] = "future"
    payload["queue_processing"]["crossfade_mode"] = "future"
    payload["outputs"][0]["dsp"]["state"] = "future"
    payload["outputs"][0]["fidelity"]["quality"] = "future"

    restored = AudioProcessingChain.from_dict(payload)

    assert restored.input_fidelity.quality is AudioQuality.UNKNOWN
    assert restored.queue_processing is not None
    assert restored.queue_processing.normalization is not None
    assert restored.queue_processing.normalization.mode is VolumeNormalizationMode.UNKNOWN
    assert (
        restored.queue_processing.normalization.measurement_source
        is AudioNormalizationMeasurementSource.UNKNOWN
    )
    assert restored.queue_processing.crossfade_mode is CrossfadeMode.UNKNOWN
    assert restored.outputs[0].dsp.state is DSPState.UNKNOWN
    assert restored.outputs[0].fidelity.quality is AudioQuality.UNKNOWN


def test_unknown_fields_are_ignored() -> None:
    """Additive unknown fields do not prevent deserialization."""
    streamdetails = _streamdetails(audio_processing=_full_chain())
    payload = streamdetails.to_dict()
    payload["future"] = True
    payload["audio_processing"]["future"] = True
    payload["audio_processing"]["input_fidelity"]["future"] = True
    payload["audio_processing"]["queue_processing"]["future"] = True
    payload["audio_processing"]["queue_processing"]["normalization"]["future"] = True
    payload["audio_processing"]["outputs"][0]["future"] = True
    payload["audio_processing"]["outputs"][0]["dsp"]["future"] = True
    payload["audio_processing"]["outputs"][0]["fidelity"]["future"] = True

    restored = StreamDetails.from_dict(payload)

    assert restored == streamdetails


def _full_chain() -> AudioProcessingChain:
    processing_format = AudioFormat(
        content_type=ContentType.PCM_F32LE,
        codec_type=ContentType.PCM_F32LE,
        sample_rate=96000,
        bit_depth=32,
        channels=2,
    )
    output_format = AudioFormat(
        content_type=ContentType.FLAC,
        codec_type=ContentType.FLAC,
        sample_rate=48000,
        bit_depth=24,
        channels=1,
        bit_rate=1200,
    )
    return AudioProcessingChain(
        input_fidelity=AudioFidelity(quality=AudioQuality.HI_RES, bit_perfect=True),
        queue_processing=AudioQueueProcessing(
            pcm_format=processing_format,
            normalization=AudioNormalizationDetails(
                mode=VolumeNormalizationMode.DYNAMIC,
                measurement_source=AudioNormalizationMeasurementSource.LIVE,
                target_lufs=-14.0,
                measured_lufs=-17.2,
                applied_gain_db=3.2,
            ),
            playback_speed=1.25,
            crossfade_mode=CrossfadeMode.SMART_CROSSFADE,
            overlay_active=True,
        ),
        outputs=[
            AudioOutputDetails(
                player_ids=["player-1", "player-2"],
                dsp=AudioDSPDetails(
                    state=DSPState.ENABLED,
                    input_gain=-1.0,
                    filters=[
                        ToneControlFilter(
                            enabled=True,
                            bass_level=1.5,
                            mid_level=0.0,
                            treble_level=-0.5,
                        )
                    ],
                    output_gain=-0.5,
                    output_limiter=True,
                    preset_id="preset-1",
                ),
                source_channel=AudioChannel.FL,
                output_format=output_format,
                fidelity=AudioFidelity(quality=AudioQuality.LOSSLESS, bit_perfect=False),
            )
        ],
    )


def _streamdetails(
    audio_processing: AudioProcessingChain | None = None,
) -> StreamDetails:
    return StreamDetails(
        provider="provider",
        item_id="item",
        audio_format=AudioFormat(
            content_type=ContentType.FLAC,
            codec_type=ContentType.FLAC,
            sample_rate=96000,
            bit_depth=24,
            channels=2,
            bit_rate=3200,
        ),
        audio_processing=audio_processing,
    )
