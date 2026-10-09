"""Tests for the QueueItem model."""

from collections.abc import Callable
from typing import Any

import pytest

from music_assistant_models.enums import MediaType
from music_assistant_models.media_items import ItemMapping, ProviderMapping, Track
from music_assistant_models.queue_item import QueueItem, QueueItemOrigin


def _origin() -> QueueItemOrigin:
    return QueueItemOrigin(
        container=ItemMapping(
            media_type=MediaType.ALBUM, item_id="album1", provider="tidal--a1", name="Album"
        ),
        provider_instance="tidal--a1",
        item_id="track1",
    )


def _queue_item() -> QueueItem:
    track = Track(
        item_id="1",
        provider="library",
        name="Track",
        provider_mappings={
            ProviderMapping(
                item_id="track1", provider_domain="tidal", provider_instance="tidal--a1"
            )
        },
    )
    return QueueItem.from_media_item("q1", track)


def test_origin_defaults_to_none() -> None:
    """A queue item has no origin unless one is given."""
    assert _queue_item().origin is None


def test_origin_serialize_roundtrip() -> None:
    """An origin survives a to_dict -> from_dict round-trip."""
    queue_item = _queue_item()
    queue_item.origin = _origin()
    restored = QueueItem.from_dict(queue_item.to_dict())
    assert restored.origin is not None
    assert restored.origin.to_dict() == _origin().to_dict()


def test_origin_cache_roundtrip() -> None:
    """An origin survives a to_cache -> from_cache round-trip."""
    queue_item = _queue_item()
    queue_item.origin = _origin()
    restored = QueueItem.from_cache(queue_item.to_cache())
    assert restored.origin is not None
    assert restored.origin.to_dict() == _origin().to_dict()


@pytest.mark.parametrize("load", [QueueItem.from_dict, QueueItem.from_cache])
def test_payload_without_origin_key_deserializes(
    load: Callable[[dict[str, Any]], QueueItem],
) -> None:
    """Payloads and queue caches from older servers without the origin key still load."""
    legacy = _queue_item().to_dict()
    legacy.pop("origin")
    assert load(legacy).origin is None
