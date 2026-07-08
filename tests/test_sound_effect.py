"""Tests for the SoundEffect MediaItem and related types."""

from music_assistant_models.enums import MediaType
from music_assistant_models.media_items import (
    ItemMapping,
    SoundEffect,
    media_from_dict,
)
from music_assistant_models.media_items.provider_mapping import ProviderMapping


def _make_sound_effect() -> SoundEffect:
    return SoundEffect(
        item_id="rain-loop",
        provider="soundlib",
        name="Rain Loop",
        provider_mappings={
            ProviderMapping(
                item_id="rain-loop",
                provider_domain="soundlib",
                provider_instance="soundlib",
            )
        },
        duration=30,
    )


def test_media_type_sound_effect_roundtrips() -> None:
    """MediaType.SOUND_EFFECT is reachable and round-trips through StrEnum."""
    assert MediaType("sound_effect") is MediaType.SOUND_EFFECT
    assert MediaType.SOUND_EFFECT.value == "sound_effect"


def test_sound_effect_defaults() -> None:
    """SoundEffect has sane defaults aligned with the model contract."""
    item = SoundEffect(
        item_id="x",
        provider="y",
        name="z",
        provider_mappings=set(),
    )
    assert item.media_type == MediaType.SOUND_EFFECT
    assert item.duration == 0
    assert item.uri == "y://sound_effect/x"


def test_sound_effect_serialize_roundtrip() -> None:
    """SoundEffect survives a to_dict -> from_dict round-trip."""
    original = _make_sound_effect()
    data = original.to_dict()
    restored = SoundEffect.from_dict(data)
    # MediaItem.__eq__ only checks the URI, so compare the serialized form to
    # verify the full payload (duration, provider mappings, ...)
    assert restored.to_dict() == data


def test_media_from_dict_returns_sound_effect() -> None:
    """media_from_dict deserializes sound_effect payloads to SoundEffect."""
    result = media_from_dict(_make_sound_effect().to_dict())
    assert isinstance(result, SoundEffect)
    assert result.media_type == MediaType.SOUND_EFFECT


def test_item_mapping_for_sound_effect() -> None:
    """A SoundEffect can be reduced to an ItemMapping like other media items."""
    mapping = ItemMapping.from_item(_make_sound_effect())
    assert mapping.media_type == MediaType.SOUND_EFFECT
    assert mapping.item_id == "rain-loop"
