"""Serialization contract for server-owned item sharing."""

import json

import pytest

from music_assistant_models.sharing import ItemShareInfo, ItemShareLink


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "Song", "text": "Artist - Song (Album)", "links": []},
        {"title": "Station", "text": "Station", "links": []},
        {"title": "Item", "text": None, "links": []},
        {
            "title": "Song",
            "text": None,
            "links": [
                {
                    "provider_domain": "ytmusic",
                    "provider_instance": "ytmusic--account",
                    "url": "https://music.youtube.com/watch?v=meuR1l4j-xs",
                }
            ],
        },
        {
            "title": "Song",
            "text": None,
            "links": [
                {
                    "provider_domain": "spotify",
                    "provider_instance": "spotify--account",
                    "url": "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT",
                },
                {
                    "provider_domain": "ytmusic",
                    "provider_instance": "ytmusic--account",
                    "url": "https://music.youtube.com/watch?v=meuR1l4j-xs",
                },
            ],
        },
    ],
)
def test_sharing_wire_round_trip(payload: dict) -> None:
    """Link choices and nullable text survive dictionary and JSON transports."""
    item = ItemShareInfo.from_dict(payload)
    assert item.to_dict() == payload
    assert json.loads(item.to_json()) == payload
    assert ItemShareInfo.from_json(item.to_json()) == item
    assert all(isinstance(link, ItemShareLink) for link in item.links)


def test_sharing_defaults_are_independent() -> None:
    """An empty response has explicit null text and its own link list."""
    first = ItemShareInfo(title="First")
    second = ItemShareInfo(title="Second")
    first.links.append(
        ItemShareLink(
            provider_domain="example", provider_instance="account", url="https://example.org/item"
        )
    )
    assert second.to_dict() == {"title": "Second", "text": None, "links": []}
