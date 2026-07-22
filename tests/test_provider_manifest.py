"""Tests for ProviderManifest icon handling."""

from music_assistant_models.enums import ProviderIconVariant, ProviderType
from music_assistant_models.provider import ProviderManifest


def _manifest(**kwargs) -> ProviderManifest:
    return ProviderManifest(
        type=ProviderType.MUSIC,
        domain="dummy",
        name="Dummy",
        description="Dummy provider",
        codeowners=[],
        **kwargs,
    )


def test_icon_variant_values() -> None:
    """Test ProviderIconVariant enum values."""
    assert ProviderIconVariant.DEFAULT == "default"
    assert ProviderIconVariant.DARK == "dark"
    assert ProviderIconVariant.MONOCHROME == "monochrome"


def test_icon_images_defaults_empty() -> None:
    """Test that icon_images defaults to empty list."""
    assert _manifest().icon_images == []


def test_icon_images_roundtrip() -> None:
    """Test icon_images survives JSON roundtrip."""
    manifest = _manifest(icon_images=[ProviderIconVariant.DEFAULT, ProviderIconVariant.DARK])
    restored = ProviderManifest.from_json(manifest.to_json())
    assert restored.icon_images == [
        ProviderIconVariant.DEFAULT,
        ProviderIconVariant.DARK,
    ]


def test_legacy_icon_svg_key_ignored() -> None:
    """Test that legacy icon_svg key in JSON is safely ignored."""
    # old servers/persisted json may still contain icon_svg; it must be ignored
    restored = ProviderManifest.from_json(
        '{"type":"music","domain":"d","name":"N","description":"x",'
        '"codeowners":[],"icon_svg":"<svg/>"}'
    )
    assert restored.icon_images == []
    assert not hasattr(restored, "icon_svg")
