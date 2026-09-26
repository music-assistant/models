"""Tests for the favorite field on media items (like, dislike or unset)."""

from music_assistant_models.media_items import Track


def _track(favorite: bool | None) -> Track:
    return Track(
        item_id="1",
        provider="library",
        name="Test Track",
        favorite=favorite,
        provider_mappings=set(),
    )


def test_favorite_defaults_to_unset() -> None:
    """An item nobody liked or disliked carries no favorite state."""
    track = Track(item_id="1", provider="library", name="Test Track", provider_mappings=set())
    assert track.favorite is None


def test_favorite_survives_roundtrip() -> None:
    """A like, a dislike and an unset favorite are all preserved through serialization."""
    for favorite in (True, False, None):
        assert Track.from_dict(_track(favorite).to_dict()).favorite is favorite
