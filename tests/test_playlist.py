"""Tests for the Playlist MediaItem."""

from music_assistant_models.enums import MediaType, ProviderSharing
from music_assistant_models.media_items import (
    Playlist,
    PlaylistAccess,
    PlaylistSummary,
    media_from_dict,
)


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


def test_access_defaults_to_no_record() -> None:
    """A playlist without an access record is a household playlist."""
    playlist = media_from_dict(_playlist_dict())

    assert isinstance(playlist, Playlist)
    assert playlist.access is None
    assert "access" in playlist.to_dict()


def test_access_record_round_trip() -> None:
    """The access record survives serialization, on the full item and on its summary."""
    raw = _playlist_dict()
    raw["access"] = {
        "owner": "user-1",
        "sharing": "selected",
        "shared_users": ["user-2"],
        "collaborative": True,
    }
    playlist = media_from_dict(raw)

    assert isinstance(playlist, Playlist)
    assert playlist.access == PlaylistAccess(
        owner="user-1",
        sharing=ProviderSharing.SELECTED,
        shared_users=["user-2"],
        collaborative=True,
    )
    assert playlist.to_dict()["access"] == raw["access"]
    assert PlaylistSummary.from_dict(raw).access == playlist.access
    assert PlaylistSummary.from_dict(raw).to_dict()["access"] == raw["access"]


def test_access_record_is_private_and_not_collaborative_by_default() -> None:
    """A record that only names an owner is the most restrictive one."""
    access = PlaylistAccess.from_dict({"owner": "user-1"})

    assert access.sharing is ProviderSharing.PRIVATE
    assert access.shared_users == []
    assert access.collaborative is False
