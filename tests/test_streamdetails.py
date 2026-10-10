"""Tests for the StreamDetails model."""

from music_assistant_models.enums import ContentType, CrossfadeMode, MediaType, StreamType
from music_assistant_models.media_items import AudioFormat
from music_assistant_models.streamdetails import StreamDetails, TailOverlap


def _make_streamdetails(**overrides: object) -> StreamDetails:
    kwargs: dict[str, object] = {
        "provider": "spotify_connect",
        "item_id": "main",
        "audio_format": AudioFormat(
            content_type=ContentType.OGG,
            codec_type=ContentType.OGG,
            sample_rate=44100,
            bit_depth=16,
            channels=2,
            bit_rate=320,
        ),
        "media_type": MediaType.AUDIO_SOURCE,
        "stream_type": StreamType.NAMED_PIPE,
    }
    kwargs.update(overrides)
    return StreamDetails(**kwargs)  # type: ignore[arg-type]


def test_decoded_audio_format_defaults_to_none() -> None:
    """decoded_audio_format is optional and defaults to None."""
    sd = _make_streamdetails()
    assert sd.decoded_audio_format is None


def test_decoded_audio_format_accepts_value() -> None:
    """decoded_audio_format accepts an AudioFormat distinct from audio_format."""
    decoded = AudioFormat(
        content_type=ContentType.PCM_S16LE,
        codec_type=ContentType.PCM_S16LE,
        sample_rate=44100,
        bit_depth=16,
        channels=2,
    )
    sd = _make_streamdetails(decoded_audio_format=decoded)
    assert sd.decoded_audio_format is decoded
    assert sd.audio_format.content_type is ContentType.OGG


def test_decoded_audio_format_is_not_serialized() -> None:
    """decoded_audio_format is server-internal and must not be sent to clients."""
    decoded = AudioFormat(
        content_type=ContentType.PCM_S16LE,
        codec_type=ContentType.PCM_S16LE,
        sample_rate=44100,
        bit_depth=16,
        channels=2,
    )
    sd = _make_streamdetails(decoded_audio_format=decoded)
    assert "decoded_audio_format" not in sd.to_dict()


def test_is_realtime_defaults_to_false() -> None:
    """is_realtime defaults to False, so a source is read ahead unless it says otherwise."""
    assert _make_streamdetails().is_realtime is False


def test_is_realtime_is_not_serialized() -> None:
    """is_realtime is server-internal and must not be sent to clients."""
    assert "is_realtime" not in _make_streamdetails(is_realtime=True).to_dict()


def test_tail_overlap_is_not_serialized() -> None:
    """tail_overlap is server-internal and must not be sent to clients."""
    sd = _make_streamdetails(tail_overlap=TailOverlap(duration=4.5, next_queue_item_id="qi-2"))
    assert "tail_overlap" not in sd.to_dict()


def test_tail_overlap_defaults_to_none_on_deserialize() -> None:
    """A payload without tail_overlap deserializes to None and still round-trips equal."""
    sd = _make_streamdetails()
    restored = StreamDetails.from_dict(sd.to_dict())
    assert restored.tail_overlap is None
    assert restored == sd


def test_crossfade_mode_voice_over() -> None:
    """The voice_over crossfade mode deserializes to its own member."""
    assert CrossfadeMode("voice_over") is CrossfadeMode.VOICE_OVER


def test_queue_session_id_is_not_serialized() -> None:
    """queue_session_id is server-internal and must not be sent to clients."""
    sd = _make_streamdetails()
    sd.queue_session_id = "sess-1"
    assert "queue_session_id" not in sd.to_dict()


def test_legacy_dsp_is_not_serialized() -> None:
    """Legacy DSP details are not included in stream details."""
    assert "dsp" not in _make_streamdetails().to_dict()


def test_legacy_dsp_payload_is_ignored() -> None:
    """Legacy DSP details do not affect deserialization."""
    streamdetails = _make_streamdetails()
    payload = streamdetails.to_dict()
    payload["dsp"] = {
        "player-id": {
            "state": "enabled",
            "input_gain": 0.0,
            "filters": [],
            "output_gain": 0.0,
            "output_format": None,
        }
    }

    assert StreamDetails.from_dict(payload) == streamdetails
