"""Tests for MediaItemBookmark."""

from music_assistant_models.media_items import MediaItemBookmark


def test_bookmark_roundtrip() -> None:
    """A bookmark read without the storage flag is provider-stored and round-trips as a dict."""
    bookmark = MediaItemBookmark.from_dict(
        {
            "position": 1,
            "name": "Intro",
            "start": 12.5,
            "provider_instance_id": "abs",
            "provider_item_id": "book1",
        }
    )
    assert bookmark.stored_by_music_assistant is False
    assert MediaItemBookmark.from_dict(bookmark.to_dict()) == bookmark
