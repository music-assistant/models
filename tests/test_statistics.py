"""Tests for the statistics models."""

from music_assistant_models.enums import MediaType
from music_assistant_models.media_items import ItemMapping
from music_assistant_models.statistics import ListeningTimeItem, PlayHistoryItem


def test_play_history_item_roundtrip_and_item_mapping_compatibility() -> None:
    """Dated events retain all the fields expected by existing history readers."""
    event = PlayHistoryItem(
        item_id="track-1",
        provider="test-provider",
        media_type=MediaType.TRACK,
        name="Test Track",
        event_id=42,
        played_at=1_789_000_000.5,
        available=False,
    )
    payload = event.to_dict()
    restored = PlayHistoryItem.from_dict(payload)
    assert restored.event_id == 42
    assert restored.played_at == 1_789_000_000.5
    assert restored.to_dict() == payload
    item_mapping = ItemMapping.from_dict(payload)
    assert item_mapping.item_id == event.item_id
    assert item_mapping.uri == event.uri
    assert not item_mapping.available


def test_play_history_item_preserves_uri_equality_and_hashing() -> None:
    """History entries keep the media reference's URI-based identity."""
    item = ItemMapping(
        item_id="track-1", provider="test-provider", media_type=MediaType.TRACK, name="Track"
    )
    first = PlayHistoryItem.from_dict(
        {**item.to_dict(), "event_id": 1, "played_at": 1_789_000_000.0}
    )
    second = PlayHistoryItem.from_dict(
        {**item.to_dict(), "event_id": 2, "played_at": 1_789_000_100.0}
    )
    assert first == second
    assert first == item
    assert item == first
    assert hash(first) == hash(second) == hash(item)
    assert len({item, first, second}) == 1


def test_listening_time_item_roundtrip_with_item() -> None:
    """A listening time row keeps its artist through serialization."""
    artist = ItemMapping(
        media_type=MediaType.ARTIST, item_id="1", provider="library", name="Test Artist"
    )
    row = ListeningTimeItem(name="Test Artist", minutes=12.5, item=artist)
    restored = ListeningTimeItem.from_dict(row.to_dict())
    assert restored.item is not None
    assert restored.item.item_id == "1"
    assert restored.item.provider == "library"
    assert restored.item.media_type == MediaType.ARTIST


def test_listening_time_item_without_item() -> None:
    """A row without an item (e.g. a genre) still deserializes from older payloads."""
    restored = ListeningTimeItem.from_dict({"name": "Rock", "minutes": 3.0})
    assert restored.item is None
    assert restored.minutes == 3.0
