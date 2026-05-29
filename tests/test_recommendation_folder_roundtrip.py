"""Tests for RecommendationFolder Union deserialization."""

from music_assistant_models.enums import MediaType
from music_assistant_models.media_items import (
    Album,
    Artist,
    ItemMapping,
    Playlist,
    ProviderMapping,
    RecommendationFolder,
    Track,
)
from music_assistant_models.unique_list import UniqueList


def _make_provider_mapping(provider: str = "test", item_id: str = "1") -> set[ProviderMapping]:
    return {ProviderMapping(item_id=item_id, provider_domain="test", provider_instance=provider)}


def test_mixed_items_roundtrip_preserves_all_types() -> None:
    """Multiple different media types in items all survive roundtrip."""
    folder = RecommendationFolder(
        item_id="rec_mixed",
        provider="deezer",
        name="Mixed Recommendations",
        items=UniqueList(
            [
                Artist(
                    item_id="ar_1",
                    provider="deezer",
                    name="Test Artist",
                    provider_mappings=_make_provider_mapping("deezer", "ar_1"),
                ),
                Album(
                    item_id="al_1",
                    provider="deezer",
                    name="Test Album",
                    provider_mappings=_make_provider_mapping("deezer", "al_1"),
                    year=2024,
                ),
                Track(
                    item_id="tr_1",
                    provider="deezer",
                    name="Test Track",
                    provider_mappings=_make_provider_mapping("deezer", "tr_1"),
                    duration=240,
                ),
                Playlist(
                    item_id="pl_1",
                    provider="deezer",
                    name="Test Playlist",
                    provider_mappings=_make_provider_mapping("deezer", "pl_1"),
                    is_dynamic=True,
                ),
                ItemMapping(
                    item_id="im_1",
                    provider="deezer",
                    name="Mapped Item",
                    media_type=MediaType.TRACK,
                ),
            ]
        ),
    )

    deserialized = RecommendationFolder.from_dict(folder.to_dict())

    assert len(deserialized.items) == 5
    assert [(type(i).__name__, i.media_type) for i in deserialized.items] == [
        ("Artist", MediaType.ARTIST),
        ("Album", MediaType.ALBUM),
        ("Track", MediaType.TRACK),
        ("Playlist", MediaType.PLAYLIST),
        ("ItemMapping", MediaType.TRACK),
    ]
