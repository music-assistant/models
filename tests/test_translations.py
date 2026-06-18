"""Tests for the serialization-time translation resolution hooks."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from music_assistant_models.background_task import BackgroundTask
from music_assistant_models.config_entries import ConfigEntry, ConfigValueOption
from music_assistant_models.enums import ConfigEntryType, ProviderType
from music_assistant_models.media_items import BrowseFolder, Genre, RecommendationFolder
from music_assistant_models.player import (
    PlayerOption,
    PlayerOptionEntry,
    PlayerOptionType,
    PlayerSoundMode,
)
from music_assistant_models.provider import ProviderManifest
from music_assistant_models.translations import TRANSLATION_RESOLVER

# the strings a bound resolver would return for the keys the models look up
_CATALOG = {
    "config_entries.log_level.label": "Logniveau",
    "config_entries.preset.label": "Preset",
    "config_categories.generic": "Algemeen",
    "media.recommendations.recently_played.name": "Onlangs afgespeeld",
    "media.recommendations.recently_played.subtitle": "Ga verder waar je gebleven was",
    "media.folder.libraries.name": "Bibliotheken",
    "media.genre.jazz.name": "Jazz (NL)",
    "media.genre.jazz.description": "Jazz is een Amerikaans muziekgenre.",
    "provider.demo.manifest.name": "Demo-muziekprovider",
    "provider.demo.manifest.description": "Een demoprovider.",
    "core.cache.manifest.name": "Cache (NL)",
    "core.cache.manifest.description": "Cache-configuratie.",
    "background_task.database_cleanup": "Database opschonen",
    "background_task.update_metadata": "Metadata bijwerken voor {0}",
    "player_options.surround_decoder_type.name": "Type surround-decoder",
    "player_options.surround_decoder_type.options.auto": "Automatisch",
    "player_options.sleep.name": "Slaaptimer na {0} minuten",
    "sound_mode.stereo.name": "Stereo (NL)",
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


def test_config_entry_explicit_translation_key_is_a_bare_slug() -> None:
    """An explicit translation_key is a bare slug; the model derives config_entries.<slug>."""
    # e.g. a shared key for a dynamic config key (preset_1, preset_2, ...) -> config_entries.preset
    entry = ConfigEntry(key="preset_1", type=ConfigEntryType.STRING, translation_key="preset")
    with _resolver_active():
        assert entry.to_dict()["label"] == "Preset"


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


def test_genre_resolves_nested_metadata_description() -> None:
    """A Genre localizes its name and its nested metadata.description from media.genre.<key>.*."""
    genre = Genre(
        item_id="jazz",
        provider="library",
        name="Jazz",
        translation_key="jazz",
        provider_mappings=set(),
    )
    # plain to_dict keeps the in-code values (no description authored in code)
    plain = genre.to_dict()
    assert plain["name"] == "Jazz"
    assert plain["metadata"]["description"] is None
    # resolver bound -> localized name + nested metadata.description, machinery stripped
    with _resolver_active():
        localized = genre.to_dict()
    assert localized["name"] == "Jazz (NL)"
    assert localized["metadata"]["description"] == "Jazz is een Amerikaans muziekgenre."
    assert "translation_key" not in localized


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


def test_core_manifest_resolves_under_core_namespace() -> None:
    """A CORE manifest resolves name/description from core.<domain>.manifest.*."""
    manifest = ProviderManifest(
        type=ProviderType.CORE,
        domain="cache",
        name="Cache",
        description="Cache configuration.",
        codeowners=[],
    )
    assert manifest.to_dict()["name"] == "Cache"
    with _resolver_active():
        localized = manifest.to_dict()
    assert localized["name"] == "Cache (NL)"
    assert localized["description"] == "Cache-configuratie."


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


def test_player_option_resolves_name_and_titles_keeps_translation_key() -> None:
    """A PlayerOption localizes its name + option titles but keeps translation_key for HA."""
    option = PlayerOption(
        key="surround_decoder_type",
        name="Surround decoder type",
        type=PlayerOptionType.STRING,
        value="auto",
        options=[
            PlayerOptionEntry(key="auto", name="Auto", type=PlayerOptionType.STRING, value="auto"),
        ],
    )
    # plain to_dict keeps the in-code values and the translation machinery
    plain = option.to_dict()
    assert plain["name"] == "Surround decoder type"
    assert plain["translation_key"] == "surround_decoder_type"
    assert plain["options"][0]["name"] == "Auto"
    assert "translation_params" in plain
    # resolver bound -> localized name + option title; translation_key kept (HA depends on it)
    with _resolver_active():
        localized = option.to_dict()
    assert localized["name"] == "Type surround-decoder"
    assert localized["options"][0]["name"] == "Automatisch"
    assert localized["translation_key"] == "surround_decoder_type"
    assert localized["options"][0]["translation_key"] == "auto"
    assert "translation_params" not in localized


def test_player_option_interpolates_translation_params() -> None:
    """translation_params fill positional placeholders in the resolved option name."""
    option = PlayerOption(
        key="sleep",
        name="Sleep timer",
        type=PlayerOptionType.INTEGER,
        value=30,
        translation_params=["30"],
    )
    with _resolver_active():
        assert option.to_dict()["name"] == "Slaaptimer na 30 minuten"


def test_player_sound_mode_resolves_name_and_keeps_translation_key() -> None:
    """A PlayerSoundMode localizes its name but keeps translation_key for the HA integration."""
    sound_mode = PlayerSoundMode(id="stereo", name="Stereo", translation_key="stereo")
    plain = sound_mode.to_dict()
    assert plain["name"] == "Stereo"
    assert plain["translation_key"] == "stereo"
    with _resolver_active():
        localized = sound_mode.to_dict()
    assert localized["name"] == "Stereo (NL)"
    # translation_key is kept on the wire for the HA integration
    assert localized["translation_key"] == "stereo"


def test_config_value_option_value_first() -> None:
    """Value is the first field, so a value-only option needs no keyword."""
    assert ConfigValueOption("the_value").value == "the_value"
    option = ConfigValueOption("the_value", title="Title")
    assert (option.value, option.title) == ("the_value", "Title")
