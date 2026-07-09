"""Tests for the serialization-time translation resolution hooks."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from music_assistant_models.background_task import BackgroundTask
from music_assistant_models.config_entries import ConfigEntry, ConfigValueOption
from music_assistant_models.enums import ConfigEntryType, MediaType, ProviderType
from music_assistant_models.media_items import (
    BrowseFolder,
    Genre,
    ItemMapping,
    Playlist,
    Podcast,
    ProviderMapping,
    Radio,
    RecommendationFolder,
    SoundEffect,
    Track,
)
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
    "config_entries.crossfade_mode.options.global": "Globaal",
    "config_entries.crossfade_mode.option_descriptions.global": "Volg de standaardinstelling.",
    "config_entries.crossfade_mode.disabled_reasons.smart_crossfade": "Niet beschikbaar.",
    "config_categories.generic": "Algemeen",
    "media.recommendations.recently_played.name": "Onlangs afgespeeld",
    "media.recommendations.recently_played.subtitle": "Ga verder waar je gebleven was",
    "media.folder.libraries.name": "Bibliotheken",
    "media.podcast.unknown_podcast.name": "Onbekende podcast",
    "media.sound_effect.white_noise.name": "Witte ruis",
    "media.genre.jazz.name": "Jazz (NL)",
    "media.genre.jazz.description": "Jazz is een Amerikaans muziekgenre.",
    "media.genre.comedy.name": "Komedie (muziek)",
    "media.podcast_genre.comedy.name": "Komedie (podcast)",
    "media.audiobook_genre.history.name": "Geschiedenis (audioboek)",
    "media.playlist.infinite_mix.name": "Oneindige mix",
    "media.playlist.flow.name": "Stroom: {0}",
    "media.radio.pandora_station.name": "Pandora-zender {0}",
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


def test_config_entry_resolves_option_title_description_and_disabled_reason() -> None:
    """An option resolves its title, its own per-option description and its disabled_reason."""
    entry = ConfigEntry(
        key="crossfade_mode",
        type=ConfigEntryType.STRING,
        options=[
            ConfigValueOption(value="global"),
            ConfigValueOption(value="smart_crossfade", disabled=True),
        ],
    )
    # no resolver -> unset option fields stay None (never invented)
    plain = entry.to_dict()["options"]
    assert plain[0]["title"] is None
    assert plain[0]["description"] is None
    with _resolver_active():
        options = entry.to_dict()["options"]
    # the "global" option carries both its title and its own explanatory description
    assert options[0]["title"] == "Globaal"
    assert options[0]["description"] == "Volg de standaardinstelling."
    # a description is only attached when the catalog has one for that option
    assert options[1]["description"] is None
    # disabled_reason still resolves for the disabled option
    assert options[1]["disabled_reason"] == "Niet beschikbaar."


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


def test_genre_content_type_uses_distinct_translation_namespace() -> None:
    """content_type namespaces a genre's translation group so names don't collide per taxonomy."""
    # same name + slug across taxonomies: each resolves its own group, no collision
    music = Genre(
        item_id="comedy",
        provider="library",
        name="Comedy",
        translation_key="comedy",
        provider_mappings=set(),
    )
    podcast = Genre(
        item_id="comedy",
        provider="library",
        name="Comedy",
        translation_key="comedy",
        content_type=MediaType.PODCAST,
        provider_mappings=set(),
    )
    audiobook = Genre(
        item_id="history",
        provider="library",
        name="History",
        translation_key="history",
        content_type=MediaType.AUDIOBOOK,
        provider_mappings=set(),
    )
    with _resolver_active():
        # music genre (content_type None) keeps the bare media.genre.* group
        assert music.to_dict()["name"] == "Komedie (muziek)"
        # identical slug under podcast resolves the distinct media.podcast_genre.* key
        assert podcast.to_dict()["name"] == "Komedie (podcast)"
        # audiobook gets its own media.audiobook_genre.* namespace
        assert audiobook.to_dict()["name"] == "Geschiedenis (audioboek)"


def test_playlist_resolves_static_name_and_with_params() -> None:
    """A Playlist localizes a static name, and interpolates params for dynamic titles."""
    pm = {ProviderMapping(item_id="x", provider_domain="builtin", provider_instance="builtin")}
    static = Playlist(
        item_id="infinite_mix",
        provider="builtin",
        name="Infinite Mix",
        translation_key="infinite_mix",
        provider_mappings=set(pm),
    )
    dynamic = Playlist(
        item_id="flow",
        provider="deezer",
        name="Flow: Pop",
        translation_key="flow",
        translation_params=["Pop"],
        provider_mappings=set(pm),
    )
    with _resolver_active():
        assert static.to_dict()["name"] == "Oneindige mix"
        localized = dynamic.to_dict()
    assert localized["name"] == "Stroom: Pop"
    assert "translation_key" not in localized
    assert "translation_params" not in localized


def test_radio_resolves_name_with_params() -> None:
    """A Radio interpolates translation_params into its localized name (e.g. Pandora stations)."""
    pm = {ProviderMapping(item_id="5", provider_domain="pandora", provider_instance="pandora")}
    radio = Radio(
        item_id="5",
        provider="pandora",
        name="Pandora Station 5",
        translation_key="pandora_station",
        translation_params=["5"],
        provider_mappings=set(pm),
    )
    with _resolver_active():
        assert radio.to_dict()["name"] == "Pandora-zender 5"


def test_podcast_resolves_name() -> None:
    """A Podcast localizes its name from media.podcast.<key>.name (e.g. an Unknown placeholder)."""
    podcast = Podcast(
        item_id="unknown",
        provider="spotify",
        name="Unknown Podcast",
        translation_key="unknown_podcast",
        provider_mappings=set(),
    )
    with _resolver_active():
        assert podcast.to_dict()["name"] == "Onbekende podcast"


def test_sound_effect_resolves_name() -> None:
    """A SoundEffect localizes its name from media.sound_effect.<key>.name."""
    sound_effect = SoundEffect(
        item_id="white-noise",
        provider="ambient_sounds",
        name="White noise",
        translation_key="white_noise",
        provider_mappings=set(),
    )
    with _resolver_active():
        assert sound_effect.to_dict()["name"] == "Witte ruis"


def test_item_mapping_media_type_keeps_its_default() -> None:
    """The mixin must keep ItemMapping.media_type optional (no phantom required field)."""
    # constructs without media_type; a mixin field lacking a default would break that
    mapping = ItemMapping(item_id="x", provider="p", name="N")
    assert mapping.media_type.value == "unknown"


def test_plain_media_item_has_no_translation_machinery() -> None:
    """Non-localizable media types (e.g. Track) carry neither translation_key nor params."""
    pm = {ProviderMapping(item_id="t", provider_domain="d", provider_instance="i")}
    track = Track(item_id="t", provider="i", name="Some Track", provider_mappings=set(pm))
    plain = track.to_dict()
    assert "translation_key" not in plain
    assert "translation_params" not in plain
    # serialization works even with a resolver bound (the hook simply isn't present)
    with _resolver_active():
        assert track.to_dict()["name"] == "Some Track"


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
