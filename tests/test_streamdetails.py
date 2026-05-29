"""Tests for the StreamDetails model."""

from music_assistant_models.enums import ContentType, MediaType, StreamType
from music_assistant_models.media_items import AudioFormat
from music_assistant_models.streamdetails import StreamDetails


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
