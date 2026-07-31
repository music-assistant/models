"""Tests for the PlayerMedia model (stream_duration serialization/back-compat)."""

from music_assistant_models.enums import MediaType
from music_assistant_models.player import PlayerMedia


def _media() -> PlayerMedia:
    return PlayerMedia(uri="library://track/1", media_type=MediaType.TRACK, duration=300)


def test_stream_duration_defaults_to_none() -> None:
    """Media that plays from the start has no separate stream length."""
    assert _media().stream_duration is None


def test_stream_duration_serialize_roundtrip() -> None:
    """A seeked item keeps the full duration and the shorter stream length apart."""
    media = _media()
    media.stream_duration = 120
    restored = PlayerMedia.from_dict(media.to_dict())
    assert restored.duration == 300
    assert restored.stream_duration == 120


def test_payload_without_stream_duration_key_deserializes() -> None:
    """Payloads from older servers without the stream_duration key still deserialize."""
    legacy = _media().to_dict()
    legacy.pop("stream_duration", None)
    assert PlayerMedia.from_dict(legacy).stream_duration is None
