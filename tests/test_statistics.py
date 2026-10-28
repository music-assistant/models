"""Tests for the statistics models."""

from music_assistant_models.enums import MediaType
from music_assistant_models.media_items import ItemMapping
from music_assistant_models.statistics import ListeningTimeItem


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
