"""Tests for the enabled_by_default descriptor field on RecommendationFolder."""

from __future__ import annotations

from music_assistant_models.enums import RecommendationFolderType
from music_assistant_models.media_items import RecommendationFolder


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


def test_recommendation_folder_enabled_by_default_roundtrip() -> None:
    """enabled_by_default serializes and deserializes."""
    folder = RecommendationFolder(
        item_id="random_albums",
        provider="library",
        name="Random albums",
        enabled_by_default=False,
    )
    data = folder.to_dict()
    assert data["enabled_by_default"] is False
    restored = RecommendationFolder.from_dict(data)
    assert restored.enabled_by_default is False
