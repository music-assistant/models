"""Tests for the Player and PlayerMedia models (serialization/back-compat)."""

from music_assistant_models.audio_processing import ActiveSourceAudioDetails, AudioOutputDetails
from music_assistant_models.enums import (
    ContentType,
    CrossfadeMode,
    MediaType,
    PlayerType,
    RepeatMode,
)
from music_assistant_models.media_items import AudioFormat
from music_assistant_models.player import DeviceInfo, Player, PlayerMedia, PlayerSource


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


def test_active_source_audio_serializes_as_explicit_null() -> None:
    """A player without active source audio details serializes an explicit null.

    Merged PLAYER_UPDATED snapshots rely on the key being present so stale
    details are cleared rather than left untouched.
    """
    serialized = _player().to_dict()
    assert "active_source_audio" in serialized
    assert serialized["active_source_audio"] is None


def test_active_source_audio_roundtrip() -> None:
    """Populated active source audio details survive a round-trip."""
    player = _player()
    player.active_source_audio = ActiveSourceAudioDetails(
        input_format=AudioFormat(content_type=ContentType.FLAC, codec_type=ContentType.FLAC),
        crossfade_mode=CrossfadeMode.SOURCE,
        outputs=[AudioOutputDetails(player_ids=["test_player"])],
    )

    restored = Player.from_dict(player.to_dict())

    assert restored.active_source_audio == player.active_source_audio
    assert restored.active_source_audio.crossfade_mode is CrossfadeMode.SOURCE


def test_payload_without_active_source_audio_key_deserializes() -> None:
    """Payloads from older servers without the key still deserialize to None."""
    legacy = _player().to_dict()
    legacy.pop("active_source_audio", None)
    assert Player.from_dict(legacy).active_source_audio is None


def test_player_source_ordering_defaults() -> None:
    """A source orders nothing and reports no ordering state until it says so."""
    source = PlayerSource(id="airplay", name="AirPlay")
    assert source.can_shuffle is False
    assert source.can_repeat is False
    # None rather than a default: an ordering source that has not reported yet
    # must not read as "shuffle off"
    assert source.shuffle_enabled is None
    assert source.repeat_mode is None
    assert source.account_id is None


def test_player_source_ordering_roundtrip() -> None:
    """The ordering capability and reported state survive a round-trip."""
    original = PlayerSource(
        id="spotify://audio_source/main",
        name="Spotify Connect",
        can_shuffle=True,
        can_repeat=True,
        shuffle_enabled=True,
        repeat_mode=RepeatMode.ALL,
        account_id="spotify-user-1",
    )
    data = original.to_dict()
    restored = PlayerSource.from_dict(data)
    assert restored.to_dict() == data
    assert restored.shuffle_enabled is True
    assert restored.repeat_mode is RepeatMode.ALL
    assert restored.account_id == "spotify-user-1"


def test_player_source_payload_without_ordering_keys() -> None:
    """Payloads from servers predating the ordering fields still deserialize."""
    data = PlayerSource(id="line-in", name="Line In").to_dict()
    for key in (
        "can_shuffle",
        "can_repeat",
        "shuffle_enabled",
        "repeat_mode",
        "account_id",
    ):
        data.pop(key, None)
    restored = PlayerSource.from_dict(data)
    assert restored.can_shuffle is False
    assert restored.shuffle_enabled is None
    assert restored.repeat_mode is None
    assert restored.account_id is None
