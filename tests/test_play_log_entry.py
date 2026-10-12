"""Tests for playback log entries."""

import pytest

from music_assistant_models.player_queue import PlayLogEntry


def test_play_log_entry_defaults_to_unknown_seek_position() -> None:
    """Existing positional constructors leave the playback offset unspecified."""
    entry = PlayLogEntry("item", 120, 10.5)

    assert entry.queue_item_id == "item"
    assert entry.duration == 120
    assert entry.seconds_streamed == 10.5
    assert entry.seek_position is None


@pytest.mark.parametrize("seek_position", [0.0, 59.5])
def test_play_log_entry_preserves_recorded_seek_position(seek_position: float) -> None:
    """An explicit zero offset is distinct from an unspecified offset."""
    entry = PlayLogEntry("item", seek_position=seek_position)

    assert entry.seek_position == seek_position
    assert entry.seek_position is not None
