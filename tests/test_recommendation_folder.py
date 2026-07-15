"""Tests for the RecommendationFolder descriptor fields and the HERO folder type."""

from __future__ import annotations

from music_assistant_models.enums import RecommendationFolderType
from music_assistant_models.media_items import RecommendationFolder


def test_recommendation_folder_type_has_hero() -> None:
    """The hero render style is available and serializes to its string value."""
    assert RecommendationFolderType.HERO == "hero"
    assert RecommendationFolderType("hero") is RecommendationFolderType.HERO
    assert RecommendationFolderType.DEFAULT == "default"
    assert RecommendationFolderType.TIMELINE == "timeline"


def test_recommendation_folder_descriptor_defaults() -> None:
    """A minimal RecommendationFolder fills sensible defaults; usable as a lean descriptor."""
    folder = RecommendationFolder(
        item_id="recently_played",
        provider="library",
        name="Recently played",
        icon="mdi-motion-play",
    )
    assert folder.enabled_by_default is True
    assert folder.type is RecommendationFolderType.DEFAULT
    assert folder.is_playable is False
    assert list(folder.items) == []  # the rows response omits items
    assert folder.uri is not None


def test_recommendation_folder_roundtrip() -> None:
    """RecommendationFolder serializes and deserializes the new descriptor fields."""
    folder = RecommendationFolder(
        item_id="top_picks",
        provider="library",
        name="Top Picks for You",
        icon="mdi-star",
        subtitle="A mix just for you",
        enabled_by_default=False,
        type=RecommendationFolderType.HERO,
    )
    data = folder.to_dict()
    assert data["enabled_by_default"] is False
    assert data["type"] == "hero"
    restored = RecommendationFolder.from_dict(data)
    assert restored.enabled_by_default is False
    assert restored.type is RecommendationFolderType.HERO
