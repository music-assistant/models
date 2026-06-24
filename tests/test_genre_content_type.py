"""Tests for the Genre.content_type field (taxonomy namespacing) serialization."""

from music_assistant_models.enums import MediaType
from music_assistant_models.media_items import Genre


def test_content_type_defaults_to_none() -> None:
    """A genre with no content_type defaults to None (music/general)."""
    genre = Genre(item_id="rock", provider="library", name="Rock", provider_mappings=set())
    assert genre.content_type is None
    assert genre.to_dict().get("content_type") is None


def test_content_type_survives_roundtrip() -> None:
    """content_type is preserved through to_dict/from_dict for each taxonomy."""
    for content_type in (None, MediaType.PODCAST, MediaType.AUDIOBOOK):
        genre = Genre(
            item_id="x",
            provider="library",
            name="X",
            content_type=content_type,
            provider_mappings=set(),
        )
        restored = Genre.from_dict(genre.to_dict())
        assert restored.content_type == content_type


def test_missing_content_type_key_deserializes_as_none() -> None:
    """Back-compat: payloads predating the field (no content_type key) load as music (None)."""
    genre = Genre(item_id="rock", provider="library", name="Rock", provider_mappings=set())
    data = genre.to_dict()
    data.pop("content_type", None)
    restored = Genre.from_dict(data)
    assert restored.content_type is None
