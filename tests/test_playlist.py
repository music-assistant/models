"""Tests for the Playlist MediaItem."""

from music_assistant_models.enums import MediaType
from music_assistant_models.media_items import Playlist, media_from_dict


def _playlist_dict(supported_mediatypes: list[str] | None = None) -> dict:
    playlist: dict = {
        "item_id": "1",
        "provider": "library",
        "name": "Summer",
        "media_type": "playlist",
        "provider_mappings": [
            {
                "item_id": "abc",
                "provider_domain": "builtin",
                "provider_instance": "builtin--1",
            }
        ],
    }
    if supported_mediatypes is not None:
        playlist["supported_mediatypes"] = supported_mediatypes
    return playlist


def test_supported_mediatypes_defaults_to_tracks() -> None:
    """A playlist holds tracks unless it says otherwise."""
    playlist = media_from_dict(_playlist_dict())

    assert isinstance(playlist, Playlist)
    assert playlist.supported_mediatypes == {MediaType.TRACK}


def test_unknown_supported_mediatype_is_dropped() -> None:
    """A media type this version does not know is dropped, not rejected."""
    playlist = media_from_dict(_playlist_dict(["track", "radio", "some_future_type"]))

    assert isinstance(playlist, Playlist)
    assert playlist.supported_mediatypes == {MediaType.TRACK, MediaType.RADIO}


def test_media_type_invalid_for_playlists_is_dropped() -> None:
    """A media type that can never be in a playlist is dropped, not rejected."""
    playlist = media_from_dict(_playlist_dict(["track", "artist", "album"]))

    assert isinstance(playlist, Playlist)
    assert playlist.supported_mediatypes == {MediaType.TRACK}


def test_only_unknown_supported_mediatypes_falls_back_to_tracks() -> None:
    """A playlist that ends up supporting nothing falls back to tracks."""
    playlist = media_from_dict(_playlist_dict(["some_future_type"]))

    assert isinstance(playlist, Playlist)
    assert playlist.supported_mediatypes == {MediaType.TRACK}


def test_supported_mediatypes_roundtrip() -> None:
    """The supported media types survive a serialization roundtrip."""
    supported = {MediaType.TRACK, MediaType.RADIO, MediaType.SOUND_EFFECT}
    playlist = media_from_dict(_playlist_dict([x.value for x in supported]))

    assert isinstance(playlist, Playlist)
    assert Playlist.from_dict(playlist.to_dict()).supported_mediatypes == supported
