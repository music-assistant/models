"""Tests for MediaItemBookmark and BookmarksUpdate."""

from music_assistant_models.bookmarks_update import BookmarksUpdate
from music_assistant_models.enums import MediaType
from music_assistant_models.media_items import MediaItemBookmark


def test_bookmark_roundtrip() -> None:
    """A bookmark read without the storage flag is provider-stored and round-trips as a dict."""
    bookmark = MediaItemBookmark.from_dict(
        {
            "name": "Intro",
            "start": 12.5,
            "provider_instance_id": "abs",
            "provider_item_id": "book1",
        }
    )
    assert bookmark.stored_by_music_assistant is False
    assert MediaItemBookmark.from_dict(bookmark.to_dict()) == bookmark


def test_bookmarks_update_roundtrip() -> None:
    """A BookmarksUpdate round-trips as a dict, with its media type as an enum."""
    update = BookmarksUpdate(
        media_type=MediaType.PODCAST_EPISODE,
        provider_instance_id="abs",
        provider_item_id="episode1",
        user_id="listener",
    )
    assert BookmarksUpdate.from_dict(update.to_dict()) == update
