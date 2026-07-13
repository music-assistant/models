"""Tests for the RecommendationInfo descriptor model and the HERO folder type."""

from __future__ import annotations

from music_assistant_models.enums import RecommendationFolderType


def test_recommendation_folder_type_has_hero() -> None:
    """The hero render style is available and serializes to its string value."""
    assert RecommendationFolderType.HERO == "hero"
    assert RecommendationFolderType("hero") is RecommendationFolderType.HERO
    # existing members still present
    assert RecommendationFolderType.DEFAULT == "default"
    assert RecommendationFolderType.TIMELINE == "timeline"
