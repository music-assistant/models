"""Tests for audio processing models."""

import orjson

from music_assistant_models.audio_processing import (
    AudioChannelDetails,
    AudioChannelMode,
    AudioCrossfadeDetails,
    AudioCrossfadeState,
    AudioDitheringDetails,
    AudioDitheringMethod,
    AudioDSPDetails,
    AudioFidelity,
    AudioFidelitySummary,
    AudioInputDetails,
    AudioLimiterDetails,
    AudioNormalizationDetails,
    AudioNormalizationMeasurementSource,
    AudioOutputPath,
    AudioOverlayDetails,
    AudioProcessingChain,
    AudioProcessingState,
    AudioQuality,
    AudioQueueProcessing,
    AudioResamplingDetails,
    AudioResamplingMethod,
    AudioTempoDetails,
)
from music_assistant_models.dsp import DSPState, ToneControlFilter
from music_assistant_models.enums import (
    ContentType,
    CrossfadeMode,
    EventType,
    MediaType,
    VolumeNormalizationMode,
)
from music_assistant_models.event import MassEvent
from music_assistant_models.helpers import get_serializable_value
from music_assistant_models.media_items import AudioFormat, ItemMapping


def test_audio_processing_defaults() -> None:
    """All audio processing models have safe defaults."""
    chain = AudioProcessingChain()

    assert chain.to_dict() == {
        "queue_id": "",
        "queue_item_id": None,
        "revision": 0,
        "state": "unknown",
        "input": None,
        "queue_processing": None,
        "outputs": [],
        "fidelity": None,
    }
    assert AudioProcessingChain.from_dict({}) == chain
    assert AudioInputDetails().fidelity == AudioFidelity()
    assert AudioQueueProcessing().tempo is None
    assert AudioOutputPath().dsp == AudioDSPDetails()
    assert AudioOutputPath().limiter == AudioLimiterDetails()
    assert AudioOutputPath().fidelity == AudioFidelity()


def test_audio_processing_roundtrip() -> None:
    """A populated snapshot survives serialization and deserialization."""
    chain = _full_chain()
    serialized = chain.to_dict()
    normalization = serialized["queue_processing"]["normalization"]
    crossfade = serialized["queue_processing"]["crossfade"]

    assert get_serializable_value(chain) == serialized
    assert AudioProcessingChain.from_dict(serialized) == chain
    assert normalization["target_true_peak_dbtp"] == -2.0
    assert "target_true_peak_dbfs" not in normalization
    assert "reason_code" in normalization
    assert "reason" not in normalization
    assert "reason_code" in crossfade
    assert "reason" not in crossfade


def test_audio_processing_event_serialization() -> None:
    """The snapshot serializes as event data."""
    event = MassEvent(
        event=EventType.AUDIO_PROCESSING_UPDATED,
        object_id="queue-1",
        data=_full_chain(),
    )

    serialized = orjson.loads(event.to_json())

    assert serialized["event"] == "audio_processing_updated"
    assert serialized["object_id"] == "queue-1"
    assert serialized["data"]["queue_id"] == "queue-1"
    assert serialized["data"]["outputs"][0]["player_ids"] == ["player-1", "player-2"]


def test_unknown_audio_processing_enums_fall_back() -> None:
    """Unknown enum values deserialize without rejecting the snapshot."""
    payload = _full_chain().to_dict()
    payload["state"] = "future"
    payload["input"]["fidelity"]["quality"] = "future"
    payload["queue_processing"]["normalization"]["measurement_source"] = "future"
    payload["queue_processing"]["crossfade"]["mode"] = "future"
    payload["queue_processing"]["crossfade"]["state"] = "future"
    payload["outputs"][0]["dsp"]["state"] = "future"
    payload["outputs"][0]["channels"]["mode"] = "future"
    payload["outputs"][0]["resampling"]["method"] = "future"
    payload["outputs"][0]["dithering"]["method"] = "future"
    payload["fidelity"]["min_output_quality"] = "future"

    restored = AudioProcessingChain.from_dict(payload)

    assert restored.state is AudioProcessingState.UNKNOWN
    assert restored.input is not None
    assert restored.input.fidelity.quality is AudioQuality.UNKNOWN
    assert restored.queue_processing is not None
    assert restored.queue_processing.normalization is not None
    assert (
        restored.queue_processing.normalization.measurement_source
        is AudioNormalizationMeasurementSource.UNKNOWN
    )
    assert restored.queue_processing.crossfade is not None
    assert restored.queue_processing.crossfade.mode is CrossfadeMode.UNKNOWN
    assert restored.queue_processing.crossfade.state is AudioCrossfadeState.UNKNOWN
    assert restored.outputs[0].dsp.state is DSPState.UNKNOWN
    assert restored.outputs[0].channels is not None
    assert restored.outputs[0].channels.mode is AudioChannelMode.UNKNOWN
    assert restored.outputs[0].resampling is not None
    assert restored.outputs[0].resampling.method is AudioResamplingMethod.UNKNOWN
    assert restored.outputs[0].dithering is not None
    assert restored.outputs[0].dithering.method is AudioDitheringMethod.UNKNOWN
    assert restored.fidelity is not None
    assert restored.fidelity.min_output_quality is AudioQuality.UNKNOWN


def test_unknown_fields_are_ignored() -> None:
    """Additive unknown fields do not prevent deserialization."""
    payload = _full_chain().to_dict()
    payload["future"] = True
    payload["input"]["future"] = True
    payload["queue_processing"]["future"] = True
    payload["queue_processing"]["normalization"]["future"] = True
    payload["outputs"][0]["future"] = True
    payload["outputs"][0]["dsp"]["future"] = True
    payload["outputs"][0]["fidelity"]["future"] = True
    payload["fidelity"]["future"] = True

    restored = AudioProcessingChain.from_dict(payload)

    assert restored == _full_chain()


def _full_chain() -> AudioProcessingChain:
    source_format = AudioFormat(
        content_type=ContentType.FLAC,
        codec_type=ContentType.FLAC,
        sample_rate=96000,
        bit_depth=24,
        channels=2,
        bit_rate=3200,
    )
    input_format = AudioFormat(
        content_type=ContentType.PCM_S24LE,
        codec_type=ContentType.PCM_S24LE,
        sample_rate=96000,
        bit_depth=24,
        channels=2,
    )
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
    overlay_source = ItemMapping(
        media_type=MediaType.SOUND_EFFECT,
        item_id="rain",
        provider="builtin",
        name="Rain",
    )
    return AudioProcessingChain(
        queue_id="queue-1",
        queue_item_id="item-1",
        revision=3,
        state=AudioProcessingState.READY,
        input=AudioInputDetails(
            source_format=source_format,
            server_input_format=input_format,
            fidelity=AudioFidelity(quality=AudioQuality.HI_RES, bit_perfect=True),
        ),
        queue_processing=AudioQueueProcessing(
            input_format=input_format,
            output_format=processing_format,
            normalization=AudioNormalizationDetails(
                mode=VolumeNormalizationMode.DYNAMIC,
                measurement_source=AudioNormalizationMeasurementSource.LIVE,
                target_lufs=-14.0,
                measured_lufs=-17.2,
                target_true_peak_dbtp=-2.0,
                target_loudness_range_lu=10.0,
            ),
            tempo=AudioTempoDetails(playback_speed=1.25),
            crossfade=AudioCrossfadeDetails(
                mode=CrossfadeMode.SMART_CROSSFADE,
                state=AudioCrossfadeState.APPLIED,
                from_queue_item_id="item-0",
                to_queue_item_id="item-1",
                planned_duration=8.0,
                actual_duration=7.8,
            ),
            overlay=AudioOverlayDetails(source=overlay_source, volume_percent=40),
        ),
        outputs=[
            AudioOutputPath(
                player_ids=["player-1", "player-2"],
                input_format=processing_format,
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
                ),
                channels=AudioChannelDetails(mode=AudioChannelMode.LEFT),
                limiter=AudioLimiterDetails(enabled=True, threshold_dbfs=-2.0),
                resampling=AudioResamplingDetails(method=AudioResamplingMethod.SOXR),
                dithering=AudioDitheringDetails(method=AudioDitheringMethod.TRIANGULAR_HP),
                output_format=output_format,
                handoff_format=processing_format,
                fidelity=AudioFidelity(quality=AudioQuality.LOSSLESS, bit_perfect=False),
            )
        ],
        fidelity=AudioFidelitySummary(
            min_output_quality=AudioQuality.LOSSLESS,
            max_output_quality=AudioQuality.LOSSLESS,
        ),
    )
