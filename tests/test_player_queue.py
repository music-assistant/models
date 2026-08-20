"""Tests for the PlayerQueue model (deprecated-key back-compat serialization)."""

from music_assistant_models.enums import MediaType
from music_assistant_models.media_items import ItemMapping
from music_assistant_models.player_queue import PlayerQueue


def _queue() -> PlayerQueue:
    return PlayerQueue(queue_id="q1", active=True, display_name="Q1", available=True, items=0)


def test_sources_mirrors_deprecated_radio_source() -> None:
    """to_dict mirrors sources to the deprecated radio_source key for older clients."""
    d = _queue().to_dict()
    assert "sources" in d
    assert d["radio_source"] == d["sources"]


def test_legacy_radio_source_maps_to_sources() -> None:
    """from_dict accepts the legacy radio_source key (no sources) as sources."""
    legacy = _queue().to_dict()
    legacy.pop("sources", None)
    restored = PlayerQueue.from_dict(legacy)
    assert restored.sources == []


def test_autoplay_dont_stop_backcompat_preserved() -> None:
    """The existing autoplay <-> dont_stop_the_music back-compat still holds."""
    d = _queue().to_dict()
    assert d["dont_stop_the_music_enabled"] == d["autoplay_enabled"]


def test_overlay_defaults() -> None:
    """The audio overlay fields have sane defaults."""
    queue = _queue()
    assert queue.overlay_enabled is False
    assert queue.overlay_source is None
    assert queue.overlay_volume == 100


def test_overlay_serialize_roundtrip() -> None:
    """A populated audio overlay survives a to_dict -> from_dict round-trip."""
    queue = _queue()
    queue.overlay_enabled = True
    queue.overlay_source = ItemMapping(
        media_type=MediaType.SOUND_EFFECT,
        item_id="rain-loop",
        provider="soundlib",
        name="Rain Loop",
    )
    queue.overlay_volume = 40
    restored = PlayerQueue.from_dict(queue.to_dict())
    assert restored.overlay_enabled is True
    assert restored.overlay_source is not None
    assert restored.overlay_source.media_type == MediaType.SOUND_EFFECT
    assert restored.overlay_source.item_id == "rain-loop"
    assert restored.overlay_volume == 40


def test_payload_without_overlay_keys_deserializes() -> None:
    """Payloads from older servers without the overlay keys still deserialize."""
    legacy = _queue().to_dict()
    for key in ("overlay_enabled", "overlay_source", "overlay_volume"):
        legacy.pop(key, None)
    restored = PlayerQueue.from_dict(legacy)
    assert restored.overlay_enabled is False
    assert restored.overlay_source is None
    assert restored.overlay_volume == 100


def test_queue_owner_defaults_to_none() -> None:
    """queue_owner defaults to None (MA owns the queue)."""
    assert _queue().queue_owner is None


def test_queue_owner_serialize_roundtrip() -> None:
    """queue_owner survives a serialize round-trip."""
    queue = _queue()
    queue.queue_owner = "spotify_connect://audio_source/main"
    restored = PlayerQueue.from_dict(queue.to_dict())
    assert restored.queue_owner == "spotify_connect://audio_source/main"


def test_payload_without_queue_owner_key_deserializes() -> None:
    """Payloads from servers predating queue delegation still deserialize."""
    data = _queue().to_dict()
    data.pop("queue_owner", None)
    assert PlayerQueue.from_dict(data).queue_owner is None


def test_ended_defaults_to_false() -> None:
    """A fresh queue has not ended."""
    assert _queue().ended is False


def test_ended_serialize_roundtrip() -> None:
    """A queue that reached its end survives a to_dict -> from_dict round-trip."""
    queue = _queue()
    queue.ended = True
    queue.current_index = 4
    restored = PlayerQueue.from_dict(queue.to_dict())
    assert restored.ended is True
    # the position stays on the item that finished; `ended` is what makes it legible
    assert restored.current_index == 4


def test_payload_without_ended_key_deserializes() -> None:
    """Payloads from older servers without the ended key still deserialize."""
    legacy = _queue().to_dict()
    legacy.pop("ended", None)
    assert PlayerQueue.from_dict(legacy).ended is False
