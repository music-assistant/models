"""Tests for MediaItemImage serialization and proxy id injection."""

import hashlib

from music_assistant_models.enums import ImageType
from music_assistant_models.media_items.metadata import (
    IMAGE_PROXY_ID_RESOLVER,
    MediaItemImage,
)


def _resolver(provider: str, path: str) -> str:
    # url-path-segment-safe synthetic id (no '/', '?', '#') — mirrors the
    # opaque-id contract the server-side resolver is expected to honor
    return hashlib.sha256(f"{provider}/{path}".encode()).hexdigest()


def test_image_without_resolver_leaves_proxy_id_none() -> None:
    """When no resolver is set on the context, proxy_id stays None."""
    image = MediaItemImage(type=ImageType.THUMB, path="/local/cover.jpg", provider="filesystem")
    assert image.to_dict()["proxy_id"] is None


def test_image_with_resolver_injects_proxy_id() -> None:
    """When a resolver is set, proxy_id is filled for non-public images."""
    image = MediaItemImage(type=ImageType.THUMB, path="/local/cover.jpg", provider="filesystem")
    token = IMAGE_PROXY_ID_RESOLVER.set(_resolver)
    try:
        d = image.to_dict()
    finally:
        IMAGE_PROXY_ID_RESOLVER.reset(token)
    assert d["proxy_id"] == hashlib.sha256(b"filesystem//local/cover.jpg").hexdigest()


def test_remotely_accessible_image_still_injects_proxy_id() -> None:
    """Public images also get a proxy_id so clients can request proxied thumbnails."""
    image = MediaItemImage(
        type=ImageType.THUMB,
        path="https://cdn.example.com/a.jpg",
        provider="spotify",
        remotely_accessible=True,
    )
    token = IMAGE_PROXY_ID_RESOLVER.set(_resolver)
    try:
        d = image.to_dict()
    finally:
        IMAGE_PROXY_ID_RESOLVER.reset(token)
    assert d["proxy_id"] == hashlib.sha256(b"spotify/https://cdn.example.com/a.jpg").hexdigest()


def test_proxy_id_round_trips_through_from_dict() -> None:
    """Deserializing a dict with a proxy_id preserves it on the instance."""
    raw = {
        "type": "thumb",
        "path": "/local/cover.jpg",
        "provider": "filesystem",
        "remotely_accessible": False,
        "proxy_id": "abc123",
    }
    image = MediaItemImage.from_dict(raw)
    assert image.proxy_id == "abc123"


def test_existing_proxy_id_is_not_overwritten_by_resolver() -> None:
    """A pre-set proxy_id must survive serialization even when a resolver is active."""
    image = MediaItemImage(
        type=ImageType.THUMB,
        path="/local/cover.jpg",
        provider="filesystem",
        proxy_id="pre-existing-id",
    )
    token = IMAGE_PROXY_ID_RESOLVER.set(_resolver)
    try:
        d = image.to_dict()
    finally:
        IMAGE_PROXY_ID_RESOLVER.reset(token)
    assert d["proxy_id"] == "pre-existing-id"
