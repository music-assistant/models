"""Tests for the AudioSource MediaItem and related types."""

from music_assistant_models.enums import MediaType, SourceControl
from music_assistant_models.media_items import (
    AudioSource,
    ItemMapping,
    media_from_dict,
)
from music_assistant_models.media_items.provider_mapping import ProviderMapping


def _make_audio_source() -> AudioSource:
    return AudioSource(
        item_id="airplay-living-room",
        provider="airplay",
        name="Living Room",
        provider_mappings={
            ProviderMapping(
                item_id="airplay-living-room",
                provider_domain="airplay",
                provider_instance="airplay",
            )
        },
        can_play_pause=True,
        can_seek=False,
        can_next_previous=True,
        exclusive=False,
        allow_external_trigger=True,
    )


def test_media_type_audio_source_roundtrips() -> None:
    """MediaType.AUDIO_SOURCE is reachable and round-trips through StrEnum."""
    assert MediaType("audio_source") is MediaType.AUDIO_SOURCE
    assert MediaType.AUDIO_SOURCE.value == "audio_source"


def test_source_control_missing_returns_unknown() -> None:
    """Unknown SourceControl values fall back to UNKNOWN."""
    assert SourceControl("not-a-real-control") is SourceControl.UNKNOWN
    assert SourceControl.PLAY.value == "play"


def test_audio_source_defaults() -> None:
    """AudioSource has sane defaults aligned with the model contract."""
    item = AudioSource(
        item_id="x",
        provider="y",
        name="z",
        provider_mappings=set(),
    )
    assert item.media_type == MediaType.AUDIO_SOURCE
    assert item.can_play_pause is False
    assert item.can_seek is False
    assert item.can_next_previous is False
    # exclusive defaults to True so plugins opt into multi-consumer support explicitly
    assert item.exclusive is True
    assert item.allow_external_trigger is False
    assert item.uri == "y://audio_source/x"


def test_audio_source_serialize_roundtrip() -> None:
    """AudioSource survives a to_dict -> from_dict round-trip."""
    original = _make_audio_source()
    restored = AudioSource.from_dict(original.to_dict())
    assert restored == original
    assert restored.can_play_pause is True
    assert restored.exclusive is False
    assert restored.allow_external_trigger is True


def test_media_from_dict_returns_audio_source() -> None:
    """media_from_dict deserializes audio_source payloads to AudioSource."""
    result = media_from_dict(_make_audio_source().to_dict())
    assert isinstance(result, AudioSource)
    assert result.media_type == MediaType.AUDIO_SOURCE


def test_item_mapping_for_audio_source() -> None:
    """An AudioSource can be reduced to an ItemMapping like other media items."""
    mapping = ItemMapping.from_item(_make_audio_source())
    assert mapping.media_type == MediaType.AUDIO_SOURCE
    assert mapping.item_id == "airplay-living-room"
