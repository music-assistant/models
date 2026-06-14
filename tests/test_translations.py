"""Tests for the serialization-time translation resolution hooks."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from music_assistant_models.background_task import BackgroundTask
from music_assistant_models.config_entries import ConfigEntry, ConfigValueOption
from music_assistant_models.enums import ConfigEntryType, ProviderType
from music_assistant_models.media_items import BrowseFolder, RecommendationFolder
from music_assistant_models.provider import ProviderManifest
from music_assistant_models.translations import TRANSLATION_RESOLVER

# the strings a bound resolver would return for the keys the models look up
_CATALOG = {
    "config_entries.log_level.label": "Logniveau",
    "config_categories.generic": "Algemeen",
    "media.recommendations.recently_played.name": "Onlangs afgespeeld",
    "media.recommendations.recently_played.subtitle": "Ga verder waar je gebleven was",
    "media.folder.libraries.name": "Bibliotheken",
    "provider.demo.manifest.name": "Demo-muziekprovider",
    "provider.demo.manifest.description": "Een demoprovider.",
    "background_task.database_cleanup": "Database opschonen",
    "background_task.update_metadata": "Metadata bijwerken voor {0}",
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


def test_browse_and_recommendation_folders_use_distinct_namespaces() -> None:
    """Folder names key by media type; recommendation folders override to recommendations.*."""
    browse = BrowseFolder(
        item_id="libraries", provider="library", name="Libraries", translation_key="libraries"
    )
    rec = RecommendationFolder(
        item_id="recently_played",
        provider="library",
        name="Recently played",
        translation_key="recently_played",
    )
    with _resolver_active():
        # browse folder (media_type FOLDER) reads media.folder.libraries.name
        assert browse.to_dict()["name"] == "Bibliotheken"
        # recommendation folder overrides its group -> media.recommendations.* (not media.folder.*)
        assert rec.to_dict()["name"] == "Onlangs afgespeeld"


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


def test_background_task_resolves_name_and_strips_machinery() -> None:
    """A background task localizes its name from translation_key and strips the machinery."""
    task = BackgroundTask(
        name="Database cleanup", translation_key="background_task.database_cleanup"
    )
    # plain to_dict keeps the in-code name and the machinery
    plain = task.to_dict()
    assert plain["name"] == "Database cleanup"
    assert plain["translation_key"] == "background_task.database_cleanup"
    # resolver bound -> localized name, machinery stripped from the wire
    with _resolver_active():
        localized = task.to_dict()
    assert localized["name"] == "Database opschonen"
    assert "translation_key" not in localized
    assert "translation_args" not in localized


def test_background_task_interpolates_translation_args() -> None:
    """translation_args fill positional placeholders in the resolved task name."""
    task = BackgroundTask(
        name="Update metadata for My Playlist",
        translation_key="background_task.update_metadata",
        translation_args=["My Playlist"],
    )
    with _resolver_active():
        localized = task.to_dict()
    assert localized["name"] == "Metadata bijwerken voor My Playlist"


def test_config_value_option_value_first() -> None:
    """Value is the first field, so a value-only option needs no keyword."""
    assert ConfigValueOption("the_value").value == "the_value"
    option = ConfigValueOption("the_value", title="Title")
    assert (option.value, option.title) == ("the_value", "Title")
