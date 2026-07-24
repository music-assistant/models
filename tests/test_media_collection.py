"""Tests for MediaCollection."""

import orjson

from music_assistant_models.enums import MediaType
from music_assistant_models.helpers import get_serializable_value
from music_assistant_models.media_items import Audiobook, MediaCollection, media_from_dict
from music_assistant_models.media_items.media_item import ItemMapping
from music_assistant_models.unique_list import UniqueList


def _make_media_collection_audiobook() -> MediaCollection:
    return MediaCollection(
        item_id="audiobook_collection",
        provider="library",
        name="Audiobook Collection",
        provider_mappings=set(),
        items=UniqueList(
            [
                Audiobook(item_id="a1", provider="library", name="book 1", provider_mappings=set()),
                Audiobook(item_id="a2", provider="library", name="book 2", provider_mappings=set()),
            ]
        ),
    )


def test_media_type_media_collection_roundtrips() -> None:
    """MediaType.COLLECTION is reachable and round-trips through StrEnum."""
    assert MediaType("collection") is MediaType.COLLECTION
    assert MediaType.COLLECTION.value == "collection"


def test_media_collection_defaults() -> None:
    """MediaCollection has sane defaults aligned with the model contract."""
    item = MediaCollection(
        item_id="x",
        provider="y",
        name="z",
        provider_mappings=set(),
    )
    assert item.media_type == MediaType.COLLECTION
    assert item.uri == "y://collection/x"
    assert item.items == []


def test_media_collection_serialize_roundtrip() -> None:
    """MediaCollection survives a to_dict -> from_dict round-trip."""
    original = _make_media_collection_audiobook()
    data = original.to_dict()
    restored = MediaCollection.from_dict(data)
    assert restored.to_dict() == data


def test_media_from_dict_returns_media_collection_audiobook() -> None:
    """media_from_dict deserializes media_collection payloads to MediaCollection."""
    result = media_from_dict(_make_media_collection_audiobook().to_dict())
    assert isinstance(result, MediaCollection)
    assert result.media_type == MediaType.COLLECTION
    assert isinstance(result.items[0], Audiobook)


def test_item_mapping_for_media_collection() -> None:
    """A MediaCollection can be reduced to an ItemMapping like other media items."""
    mapping = ItemMapping.from_item(_make_media_collection_audiobook())
    assert mapping.media_type == MediaType.COLLECTION
    assert mapping.item_id == "audiobook_collection"


def test_serialization_to_and_from_json() -> None:
    """Verify serialization strategy of MediaCollection."""
    original = _make_media_collection_audiobook()
    json_string = orjson.dumps(get_serializable_value(original))
    assert original == MediaCollection.from_dict(orjson.loads(json_string))
