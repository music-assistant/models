"""Tests for the PlaylogUpdate model and the PLAYLOG_UPDATED event type."""

from music_assistant_models.enums import EventType, MediaType
from music_assistant_models.event import MassEvent
from music_assistant_models.playlog_update import PlaylogUpdate


def test_event_type_playlog_updated_roundtrips() -> None:
    """EventType.PLAYLOG_UPDATED is reachable and round-trips through StrEnum."""
    assert EventType("playlog_updated") is EventType.PLAYLOG_UPDATED
    assert EventType.PLAYLOG_UPDATED.value == "playlog_updated"


def test_playlog_update_serialize_roundtrip() -> None:
    """PlaylogUpdate serializes to plain values and survives a round-trip."""
    original = PlaylogUpdate(
        uri="library://track/123",
        media_type=MediaType.TRACK,
        fully_played=True,
        seconds_played=245,
    )
    data = original.to_dict()
    assert data["media_type"] == "track"
    assert PlaylogUpdate.from_dict(data) == original


def test_playlog_update_as_event_payload() -> None:
    """A PlaylogUpdate serializes as the data of a MassEvent."""
    update = PlaylogUpdate(
        uri="library://podcast_episode/9",
        media_type=MediaType.PODCAST_EPISODE,
        fully_played=False,
        seconds_played=0,
    )
    event = MassEvent(
        event=EventType.PLAYLOG_UPDATED,
        object_id=update.uri,
        data=update,
    )
    data = event.to_dict()
    assert data["event"] == "playlog_updated"
    assert data["object_id"] == "library://podcast_episode/9"
    assert data["data"] == update.to_dict()
