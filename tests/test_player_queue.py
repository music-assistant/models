"""Tests for the PlayerQueue model (deprecated-key back-compat serialization)."""

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
