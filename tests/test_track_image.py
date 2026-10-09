"""Tests for the image a Track reports."""

from collections.abc import Callable

import pytest

from music_assistant_models.enums import ImageType, MediaType
from music_assistant_models.media_items import (
    Album,
    ItemMapping,
    MediaItemImage,
    MediaItemMetadata,
    Track,
)
from music_assistant_models.unique_list import UniqueList

ALBUM_THUMB = MediaItemImage(type=ImageType.THUMB, path="album.jpg", provider="test")
TRACK_THUMB = MediaItemImage(type=ImageType.THUMB, path="track.jpg", provider="test")

AlbumFactory = Callable[[MediaItemImage | None], Album | ItemMapping]


def _track(album: Album | ItemMapping | None) -> Track:
    return Track(
        item_id="1",
        provider="test",
        name="Track",
        provider_mappings=set(),
        album=album,
        metadata=MediaItemMetadata(images=UniqueList([TRACK_THUMB])),
    )


def _album(image: MediaItemImage | None) -> Album:
    return Album(
        item_id="2",
        provider="test",
        name="Album",
        provider_mappings=set(),
        metadata=MediaItemMetadata(images=UniqueList([image]) if image else None),
    )


def _album_mapping(image: MediaItemImage | None) -> ItemMapping:
    return ItemMapping(
        media_type=MediaType.ALBUM, item_id="2", provider="test", name="Album", image=image
    )


@pytest.mark.parametrize("album_factory", [_album, _album_mapping])
def test_track_image_prefers_album_image(album_factory: AlbumFactory) -> None:
    """The album image is preferred over the track's own image."""
    assert _track(album_factory(ALBUM_THUMB)).image == ALBUM_THUMB


@pytest.mark.parametrize("album_factory", [_album, _album_mapping])
def test_track_image_falls_back_to_own_image(album_factory: AlbumFactory) -> None:
    """The track's own image is used when its album has none."""
    assert _track(album_factory(None)).image == TRACK_THUMB


def test_track_image_without_album() -> None:
    """A track without an album reports its own image."""
    assert _track(None).image == TRACK_THUMB
