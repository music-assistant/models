"""Tests for the serialization-time translation resolution hooks."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from music_assistant_models.config_entries import ConfigEntry, ConfigValueOption
from music_assistant_models.enums import ConfigEntryType, ProviderType
from music_assistant_models.media_items import RecommendationFolder
from music_assistant_models.provider import ProviderManifest
from music_assistant_models.translations import TRANSLATION_RESOLVER

# the strings a bound resolver would return for the keys the models look up
_CATALOG = {
    "config_entries.log_level.label": "Logniveau",
    "config_categories.generic": "Algemeen",
    "media.recently_played.name": "Onlangs afgespeeld",
    "media.recently_played.subtitle": "Ga verder waar je gebleven was",
    "provider.demo.manifest.name": "Demo-muziekprovider",
    "provider.demo.manifest.description": "Een demoprovider.",
}


@contextmanager
def _resolver_active() -> Iterator[None]:
    """Bind a fake catalog resolver for the duration of the block."""

    def resolve(key: str, owner: str | None = None, params: list[Any] | None = None) -> str | None:
        for candidate in [f"{owner}.{key}", key] if owner else [key]:
            if (value := _CATALOG.get(candidate)) is not None:
                return value.format(*params) if params else value
        return None

    token = TRANSLATION_RESOLVER.set(resolve)
    try:
        yield
    finally:
        TRANSLATION_RESOLVER.reset(token)


def test_config_entry_resolves_label_and_omits_machinery() -> None:
    """ConfigEntry resolves its label/category and never serializes the translation machinery."""
    entry = ConfigEntry(key="log_level", type=ConfigEntryType.STRING)
    # no resolver -> in-code values kept, machinery never serialized
    plain = entry.to_dict()
    assert plain["label"] is None
    for key in ("translation_key", "translation_params", "category_translation_key"):
        assert key not in plain
    # resolver bound -> localized label + category
    with _resolver_active():
        localized = entry.to_dict()
    assert localized["label"] == "Logniveau"
    assert localized["category_label"] == "Algemeen"


def test_media_item_resolves_name_subtitle_and_strips_machinery() -> None:
    """A media item localizes name/subtitle and strips translation_key/params from API output."""
    folder = RecommendationFolder(
        item_id="recently_played",
        provider="library",
        name="Recently played",
        translation_key="recently_played",
        subtitle="Pick up where you left off",
    )
    # plain to_dict keeps the machinery (needed for cache/item-mapping round-trips)
    plain = folder.to_dict()
    assert plain["name"] == "Recently played"
    assert plain["translation_key"] == "recently_played"
    # resolver bound -> localized name/subtitle, machinery stripped from the wire
    with _resolver_active():
        localized = folder.to_dict()
    assert localized["name"] == "Onlangs afgespeeld"
    assert localized["subtitle"] == "Ga verder waar je gebleven was"
    assert "translation_key" not in localized
    assert "translation_params" not in localized


def test_provider_manifest_resolves_name_and_description() -> None:
    """ProviderManifest resolves name/description from provider.<domain>.manifest.*."""
    manifest = ProviderManifest(
        type=ProviderType.MUSIC,
        domain="demo",
        name="Demo Music Provider",
        description="A demo provider.",
        codeowners=[],
    )
    assert manifest.to_dict()["name"] == "Demo Music Provider"
    with _resolver_active():
        localized = manifest.to_dict()
    assert localized["name"] == "Demo-muziekprovider"
    assert localized["description"] == "Een demoprovider."


def test_config_value_option_value_first() -> None:
    """Value is the first field, so a value-only option needs no keyword."""
    assert ConfigValueOption("the_value").value == "the_value"
    option = ConfigValueOption("the_value", title="Title")
    assert (option.value, option.title) == ("the_value", "Title")
