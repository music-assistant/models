"""Tests for the favorite field on media items (like, dislike or unset)."""

from music_assistant_models.enums import EventType, MediaType
from music_assistant_models.event import MassEvent
from music_assistant_models.favorite_update import FavoriteUpdate
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


def test_favorite_update_roundtrip() -> None:
    """A FavoriteUpdate keeps every state through a dict round trip."""
    for state in (True, False, None):
        update = FavoriteUpdate(
            uri="library://track/1",
            media_type=MediaType.TRACK,
            item_id="1",
            favorite=state,
            user_id="user-1",
        )
        assert FavoriteUpdate.from_dict(update.to_dict()) == update


def test_event_type_favorite_updated_roundtrips() -> None:
    """EventType.FAVORITE_UPDATED is reachable and round-trips through StrEnum."""
    assert EventType("favorite_updated") is EventType.FAVORITE_UPDATED
    assert EventType.FAVORITE_UPDATED.value == "favorite_updated"


def test_favorite_update_as_event_payload() -> None:
    """A FavoriteUpdate serializes as the data of a MassEvent."""
    update = FavoriteUpdate(
        uri="library://album/7",
        media_type=MediaType.ALBUM,
        item_id="7",
        favorite=False,
        user_id="user-1",
    )
    event = MassEvent(event=EventType.FAVORITE_UPDATED, object_id=update.uri, data=update)
    data = event.to_dict()
    assert data["event"] == "favorite_updated"
    assert data["object_id"] == "library://album/7"
    assert data["data"] == update.to_dict()
