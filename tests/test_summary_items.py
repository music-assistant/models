"""Tests for the summary (slim) media item models."""

from music_assistant_models.enums import ImageType, MediaType
from music_assistant_models.media_items import (
    AlbumSummary,
    ArtistSummary,
    AudiobookSummary,
    GenreSummary,
    ItemMappingSummary,
    MediaItemImage,
    MediaItemMetadataSummary,
    Playlist,
    PlaylistSummary,
    PodcastSummary,
    Radio,
    RadioSummary,
    Track,
    TrackSummary,
)
from music_assistant_models.media_items.metadata import IMAGE_PROXY_ID_RESOLVER
from music_assistant_models.unique_list import UniqueList


def _track_summary() -> TrackSummary:
    return TrackSummary(
        item_id="123",
        provider="library",
        name="Test Track",
        duration=185,
        favorite=True,
        artists=UniqueList(
            [
                ItemMappingSummary(
                    media_type=MediaType.ARTIST,
                    item_id="1",
                    provider="library",
                    name="Test Artist",
                )
            ]
        ),
        album=ItemMappingSummary(
            media_type=MediaType.ALBUM,
            item_id="2",
            provider="library",
            name="Test Album",
            year=2001,
        ),
        metadata=MediaItemMetadataSummary(
            images=UniqueList(
                [MediaItemImage(type=ImageType.THUMB, path="/cover.jpg", provider="library")]
            ),
            explicit=True,
        ),
    )


def test_summary_serialization_omits_none_fields() -> None:
    """Serialized summary items must not contain any None-valued keys, at any level."""
    d = _track_summary().to_dict()
    assert not [k for k, v in d.items() if v is None]
    assert not [k for k, v in d["metadata"].items() if v is None]
    assert not [k for k, v in d["artists"][0].items() if v is None]
    assert not [k for k, v in d["album"].items() if v is None]


def test_summary_keeps_client_facing_fields() -> None:
    """Fields clients switch on must survive serialization even when default-valued."""
    d = _track_summary().to_dict()
    assert d["media_type"] == "track"
    assert d["available"] is True
    assert d["provider_mappings"] == []
    assert d["metadata"] == {
        "images": [
            {
                "type": "thumb",
                "path": "/cover.jpg",
                "provider": "library",
                "remotely_accessible": False,
                "proxy_id": None,
            }
        ],
        "explicit": True,
    }


def test_summary_roundtrips_through_regular_model() -> None:
    """A serialized summary item must deserialize cleanly with the regular class."""
    summary = _track_summary()
    track = Track.from_dict(summary.to_dict())
    assert track.name == summary.name
    assert track.duration == summary.duration
    assert track.favorite is True
    assert track.artists[0].name == "Test Artist"
    assert track.album is not None
    assert track.album.name == "Test Album"
    assert track.provider_mappings == set()


def test_summary_is_instance_of_regular_model() -> None:
    """Summary items are subtypes of their regular counterparts."""
    assert isinstance(_track_summary(), Track)
    assert isinstance(
        PlaylistSummary(item_id="1", provider="library", name="pl"),
        Playlist,
    )


def test_summary_equality_matches_regular_semantics() -> None:
    """Summary items compare by identity (uri/external ids), like regular items."""
    one = TrackSummary(item_id="123", provider="library", name="A")
    other = TrackSummary(item_id="123", provider="library", name="B")
    assert one == other
    assert hash(one) == hash(other)


def test_summary_image_proxy_id_injection() -> None:
    """The image proxy_id resolver hook must fire for images nested in summary items."""
    token = IMAGE_PROXY_ID_RESOLVER.set(lambda provider, _path: f"{provider}-proxy")
    try:
        d = _track_summary().to_dict()
    finally:
        IMAGE_PROXY_ID_RESOLVER.reset(token)
    assert d["metadata"]["images"][0]["proxy_id"] == "library-proxy"


def test_radio_summary_duration_backcompat() -> None:
    """Radio's None->0 duration shim must not break on the omitted duration key."""
    d = RadioSummary(item_id="1", provider="library", name="radio").to_dict()
    assert d["duration"] == 0
    # regular Radio keeps the same behavior
    radio = Radio(item_id="1", provider="tunein", name="radio", provider_mappings=set())
    assert radio.to_dict()["duration"] == 0


def test_per_type_summaries_serialize_sparse() -> None:
    """Every summary type serializes without None-valued keys."""
    items = [
        ArtistSummary(item_id="1", provider="library", name="artist"),
        AlbumSummary(item_id="1", provider="library", name="album", year=2001),
        PlaylistSummary(item_id="1", provider="library", name="playlist", owner="MA"),
        RadioSummary(item_id="1", provider="library", name="radio"),
        AudiobookSummary(item_id="1", provider="library", name="book", publisher="pub"),
        PodcastSummary(item_id="1", provider="library", name="podcast"),
        GenreSummary(item_id="1", provider="library", name="genre"),
    ]
    for item in items:
        d = item.to_dict()
        assert not [k for k, v in d.items() if v is None], type(item).__name__
        assert d["media_type"] == item.media_type.value
