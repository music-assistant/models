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
    assert folder.supports_provider_filter is False
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


def test_recommendation_folder_supports_provider_filter_roundtrip() -> None:
    """supports_provider_filter defaults to False and roundtrips when explicitly True."""
    folder = RecommendationFolder(
        item_id="random_albums",
        provider="library",
        name="Random albums",
    )
    assert folder.supports_provider_filter is False

    folder = RecommendationFolder(
        item_id="random_albums",
        provider="library",
        name="Random albums",
        supports_provider_filter=True,
    )
    data = folder.to_dict()
    assert data["supports_provider_filter"] is True
    restored = RecommendationFolder.from_dict(data)
    assert restored.supports_provider_filter is True


def test_recommendation_folder_supports_provider_filter_backwards_compatible() -> None:
    """Payloads without supports_provider_filter still deserialize, defaulting to False."""
    folder = RecommendationFolder(
        item_id="random_albums",
        provider="library",
        name="Random albums",
    )
    data = folder.to_dict()
    del data["supports_provider_filter"]
    restored = RecommendationFolder.from_dict(data)
    assert restored.supports_provider_filter is False


def test_recommendation_folder_supports_hide_played_roundtrip() -> None:
    """supports_hide_played defaults to False and roundtrips when explicitly True."""
    folder = RecommendationFolder(
        item_id="latest_episodes",
        provider="library",
        name="Latest podcast episodes",
    )
    assert folder.supports_hide_played is False

    folder = RecommendationFolder(
        item_id="latest_episodes",
        provider="library",
        name="Latest podcast episodes",
        supports_hide_played=True,
    )
    data = folder.to_dict()
    assert data["supports_hide_played"] is True
    restored = RecommendationFolder.from_dict(data)
    assert restored.supports_hide_played is True


def test_recommendation_folder_supports_hide_played_backwards_compatible() -> None:
    """Payloads without supports_hide_played still deserialize, defaulting to False."""
    folder = RecommendationFolder(
        item_id="latest_episodes",
        provider="library",
        name="Latest podcast episodes",
    )
    data = folder.to_dict()
    del data["supports_hide_played"]
    restored = RecommendationFolder.from_dict(data)
    assert restored.supports_hide_played is False
