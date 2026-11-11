"""Tests for ProviderInstance."""

from __future__ import annotations

from typing import Any

import pytest

from music_assistant_models.enums import ArtistType
from music_assistant_models.provider import ProviderInstance

BASE_PAYLOAD: dict[str, Any] = {
    "type": "music",
    "domain": "audiobookshelf",
    "name": "Audiobookshelf",
    "instance_id": "audiobookshelf_1",
    "supported_features": [],
    "available": True,
}


@pytest.mark.parametrize(
    ("extra", "expected"),
    [
        (
            {"supported_artist_types": ["author", "narrator"]},
            {ArtistType.AUTHOR, ArtistType.NARRATOR},
        ),
        ({}, set()),
    ],
)
def test_supported_artist_types(extra: dict[str, Any], expected: set[ArtistType]) -> None:
    """Supported artist types parse from the payload and default to none."""
    instance = ProviderInstance.from_dict({**BASE_PAYLOAD, **extra})
    assert instance.supported_artist_types == expected
