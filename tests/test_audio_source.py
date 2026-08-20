"""Tests for the AudioSource MediaItem and related types."""

from music_assistant_models.enums import MediaType, SourceControl
from music_assistant_models.media_items import (
    AudioSource,
    ItemMapping,
    SourceQueueCapabilities,
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
    # can_initiate defaults to False so passive sources don't accidentally
    # surface in user-initiated browse listings
    assert item.can_initiate is False
    assert item.uri == "y://audio_source/x"


def test_audio_source_serialize_roundtrip() -> None:
    """AudioSource survives a to_dict -> from_dict round-trip."""
    original = _make_audio_source()
    data = original.to_dict()
    restored = AudioSource.from_dict(data)
    # MediaItem.__eq__ only checks the URI, so compare the serialized form to
    # verify the full payload (capability flags, exclusivity, provider mappings, ...)
    assert restored.to_dict() == data


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


def test_source_control_queue_members() -> None:
    """The queue-delegation SourceControl members round-trip through StrEnum."""
    assert SourceControl("stop") is SourceControl.STOP
    assert SourceControl("shuffle") is SourceControl.SHUFFLE
    assert SourceControl("repeat") is SourceControl.REPEAT


def test_audio_source_queue_capability_defaults() -> None:
    """A plain AudioSource is transport-only: no queue capabilities, no account."""
    item = _make_audio_source()
    assert item.queue_capabilities is None
    assert item.account_id is None
    caps = SourceQueueCapabilities()
    assert caps.provider_domain is None
    assert caps.playable_media_types == []
    assert caps.enqueueable_media_types == []
    assert caps.can_shuffle is False
    assert caps.can_repeat is False
    assert caps.provides_queue_view is False
    assert caps.native_autoplay is False
    assert caps.native_crossfade is False
    assert caps.native_volume_normalization is False


def test_audio_source_queue_capabilities_roundtrip() -> None:
    """queue_capabilities and account_id survive a serialize round-trip."""
    original = _make_audio_source()
    original.queue_capabilities = SourceQueueCapabilities(
        provider_domain="spotify",
        playable_media_types=[MediaType.TRACK, MediaType.ALBUM, MediaType.PLAYLIST],
        enqueueable_media_types=[MediaType.TRACK],
        can_shuffle=True,
        can_repeat=True,
        provides_queue_view=True,
        native_autoplay=True,
        native_crossfade=True,
        native_volume_normalization=True,
    )
    original.account_id = "spotify-user-1"
    data = original.to_dict()
    restored = AudioSource.from_dict(data)
    assert restored.to_dict() == data
    assert restored.queue_capabilities is not None
    assert restored.queue_capabilities.provider_domain == "spotify"
    assert restored.queue_capabilities.playable_media_types == [
        MediaType.TRACK,
        MediaType.ALBUM,
        MediaType.PLAYLIST,
    ]
    assert restored.account_id == "spotify-user-1"


def test_audio_source_payload_without_queue_capability_keys() -> None:
    """Payloads from servers predating queue delegation still deserialize."""
    data = _make_audio_source().to_dict()
    data.pop("queue_capabilities", None)
    data.pop("account_id", None)
    restored = AudioSource.from_dict(data)
    assert restored.queue_capabilities is None
    assert restored.account_id is None
