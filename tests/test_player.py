"""Tests for the Player and PlayerMedia models (serialization/back-compat)."""

from music_assistant_models.enums import MediaType, PlayerType
from music_assistant_models.player import DeviceInfo, Player, PlayerMedia


def _media() -> PlayerMedia:
    return PlayerMedia(uri="library://track/1", media_type=MediaType.TRACK, duration=300)


def _player() -> Player:
    return Player(
        player_id="test_player",
        provider="test_provider",
        type=PlayerType.PLAYER,
        name="Test Player",
        available=True,
        device_info=DeviceInfo(),
    )


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


def test_queue_session_id_is_not_serialized() -> None:
    """The queue session id is server-internal and must never reach a client."""
    media = _media()
    media.queue_session_id = "abcd1234"
    assert "queue_session_id" not in media.to_dict()


def test_queue_session_id_is_not_serialized_on_a_player() -> None:
    """Players are what clients actually read, so the nested payload must be clean too."""
    media = _media()
    media.queue_session_id = "abcd1234"
    player = _player()
    player.current_media = media
    assert "queue_session_id" not in player.to_dict()["current_media"]


def test_queue_session_id_is_kept_out_of_repr() -> None:
    """The value must not surface through logging that prints the media."""
    media = _media()
    media.queue_session_id = "abcd1234"
    assert "abcd1234" not in repr(media)


def test_private_defaults_to_false() -> None:
    """A player is only private when its provider marks it as such."""
    assert _player().private is False


def test_private_serialize_roundtrip() -> None:
    """A private player keeps the flag across serialization."""
    player = _player()
    player.private = True
    assert Player.from_dict(player.to_dict()).private is True


def test_payload_without_private_key_deserializes() -> None:
    """Payloads from older servers without the private key still deserialize."""
    legacy = _player().to_dict()
    legacy.pop("private", None)
    assert Player.from_dict(legacy).private is False
