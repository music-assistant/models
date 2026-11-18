"""Tests for ProviderManifest icon handling."""

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from mashumaro.exceptions import InvalidFieldValue

from music_assistant_models.auth import Scope
from music_assistant_models.enums import (
    MediaType,
    ProviderFeature,
    ProviderIconVariant,
    ProviderTier,
    ProviderType,
)
from music_assistant_models.provider import (
    MAX_MENU_ACTION_LABEL_LENGTH,
    MAX_TRANSLATED_MENU_ACTION_LABEL_LENGTH,
    ProviderManifest,
    ProviderMCPTool,
    ProviderMenuAction,
    ProviderPage,
    is_menu_action_label,
)
from music_assistant_models.translations import TRANSLATION_RESOLVER

_MENU_ACTIONS_JSON = (
    '{"type":"plugin","domain":"frame","name":"N","description":"x","codeowners":[],'
    '"menu_actions":[{"id":"send_to_frame","label":"Show on the picture frame",'
    '"media_types":["album","playlist"],"scope":"library.read","icon":"mdi-image-frame"},'
    '{"id":"play_on_frame","label":"Play on the picture frame","media_types":["track"],'
    '"scope":"queues.control","requires_player":true}]}'
)

_PAGE_JSON = (
    '{"type":"plugin","domain":"frame","name":"N","description":"x","codeowners":[],'
    '"page":{"label":"Picture frame","scope":"library.read","icon":"mdi-image-frame"}}'
)

_MCP_TOOLS_JSON = (
    '{"type":"music","domain":"radio","name":"N","description":"x","codeowners":[],'
    '"mcp_tools":[{"id":"play_station","description":"Play a saved station on a player.",'
    '"scope":"queues.control","requires_player":true,"input_schema":{"type":"object",'
    '"properties":{"station":{"type":"string","description":"The name of the station."}},'
    '"required":["station"]}},'
    '{"id":"list_stations","description":"List the saved stations.","scope":"library.read"}]}'
)


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


def test_has_setup_flow_defaults_false() -> None:
    """Test that has_setup_flow defaults to False."""
    assert _manifest().has_setup_flow is False


def test_has_setup_flow_roundtrip() -> None:
    """Test has_setup_flow survives JSON roundtrip."""
    manifest = _manifest(has_setup_flow=True)
    restored = ProviderManifest.from_json(manifest.to_json())
    assert restored.has_setup_flow is True


def test_has_setup_flow_missing_key_backward_compatible() -> None:
    """Test that JSON without has_setup_flow (old server payload) defaults to False."""
    restored = ProviderManifest.from_json(
        '{"type":"music","domain":"d","name":"N","description":"x","codeowners":[]}'
    )
    assert restored.has_setup_flow is False


def test_self_service_defaults_true() -> None:
    """Test that self_service defaults to True."""
    assert _manifest().self_service is True


def test_self_service_roundtrip() -> None:
    """Test that a provider without self-service survives JSON roundtrip."""
    manifest = _manifest(self_service=False)
    restored = ProviderManifest.from_json(manifest.to_json())
    assert restored.self_service is False


def test_self_service_missing_key_backward_compatible() -> None:
    """Test that JSON without self_service (old server payload) defaults to True."""
    restored = ProviderManifest.from_json(
        '{"type":"music","domain":"d","name":"N","description":"x","codeowners":[]}'
    )
    assert restored.self_service is True


def test_tier_values() -> None:
    """Test ProviderTier enum values."""
    assert ProviderTier.CORE == "core"
    assert ProviderTier.COMMUNITY == "community"


def test_tier_unknown_value_falls_back_to_community() -> None:
    """Test that an unknown tier in a payload (newer server) never resolves to core."""
    restored = ProviderManifest.from_json(
        '{"type":"music","domain":"d","name":"N","description":"x","codeowners":[],'
        '"tier":"something_new"}'
    )
    assert restored.tier is ProviderTier.COMMUNITY


def test_tier_defaults_community() -> None:
    """Test that tier defaults to community."""
    assert _manifest().tier is ProviderTier.COMMUNITY


def test_tier_roundtrip() -> None:
    """Test tier survives JSON roundtrip."""
    manifest = _manifest(tier=ProviderTier.CORE)
    restored = ProviderManifest.from_json(manifest.to_json())
    assert restored.tier is ProviderTier.CORE


def test_support_url_defaults_none() -> None:
    """Test that support_url defaults to None."""
    assert _manifest().support_url is None


def test_support_url_roundtrip() -> None:
    """Test support_url survives JSON roundtrip."""
    manifest = _manifest(support_url="https://example.com/issues")
    restored = ProviderManifest.from_json(manifest.to_json())
    assert restored.support_url == "https://example.com/issues"


def test_tier_and_support_url_missing_keys_backward_compatible() -> None:
    """Test that JSON without tier and support_url (old server payload) uses the defaults."""
    restored = ProviderManifest.from_json(
        '{"type":"music","domain":"d","name":"N","description":"x","codeowners":[]}'
    )
    assert restored.tier is ProviderTier.COMMUNITY
    assert restored.support_url is None


@contextmanager
def _resolver(catalog: dict[str, str]) -> Iterator[None]:
    """Bind a resolver that looks keys up in the given catalog for the duration of the block."""
    token = TRANSLATION_RESOLVER.set(lambda key, **_: catalog.get(key))
    try:
        yield
    finally:
        TRANSLATION_RESOLVER.reset(token)


def test_menu_actions_missing_key_defaults_empty() -> None:
    """Test that a manifest without menu_actions has none."""
    restored = ProviderManifest.from_json(
        '{"type":"music","domain":"d","name":"N","description":"x","codeowners":[]}'
    )
    assert restored.menu_actions == []


def test_menu_actions_parsed() -> None:
    """Test that declared menu actions parse with their defaults."""
    manifest = ProviderManifest.from_json(_MENU_ACTIONS_JSON)
    assert manifest.menu_actions == [
        ProviderMenuAction(
            id="send_to_frame",
            label="Show on the picture frame",
            media_types=[MediaType.ALBUM, MediaType.PLAYLIST],
            scope=Scope.LIBRARY_READ,
            icon="mdi-image-frame",
        ),
        ProviderMenuAction(
            id="play_on_frame",
            label="Play on the picture frame",
            media_types=[MediaType.TRACK],
            scope=Scope.QUEUES_CONTROL,
            requires_player=True,
        ),
    ]
    assert manifest.menu_actions[0].requires_player is False
    assert manifest.menu_actions[1].icon is None
    assert ProviderManifest.from_json(manifest.to_json()) == manifest


def test_menu_action_label_translated() -> None:
    """Test that a menu action label is translated from menu_actions.<id>.label of its provider."""
    manifest = ProviderManifest.from_json(_MENU_ACTIONS_JSON)
    with _resolver({"provider.frame.menu_actions.send_to_frame.label": "Toon op de fotolijst"}):
        labels = [action["label"] for action in manifest.to_dict()["menu_actions"]]
    assert labels == ["Toon op de fotolijst", "Play on the picture frame"]


def test_menu_action_label_english_without_resolver() -> None:
    """Test that a menu action keeps the English label of its manifest without a resolver."""
    manifest = ProviderManifest.from_json(_MENU_ACTIONS_JSON)
    labels = [action["label"] for action in manifest.to_dict()["menu_actions"]]
    assert labels == ["Show on the picture frame", "Play on the picture frame"]


@pytest.mark.parametrize(
    "menu_actions",
    [
        '{"id":"a","label":"L","media_types":["album"],"scope":"library.read"}',
        '[{"id":"a","label":"L","media_types":["album"]}]',
        '"a"',
    ],
)
def test_menu_actions_wrong_type_fails(menu_actions: str) -> None:
    """Test that menu actions of the wrong shape fail to parse the manifest."""
    with pytest.raises(InvalidFieldValue):
        ProviderManifest.from_json(
            '{"type":"plugin","domain":"d","name":"N","description":"x","codeowners":[],'
            f'"menu_actions":{menu_actions}}}'
        )


def test_menu_actions_last_field() -> None:
    """Test that the newer fields come last, so positional construction keeps order."""
    assert list(ProviderManifest.__dataclass_fields__)[-5:] == [
        "credits",
        "menu_actions",
        "mcp_tools",
        "features",
        "page",
    ]


def test_page_missing_key_defaults_none() -> None:
    """Test that a manifest without a page declares none."""
    restored = ProviderManifest.from_json(
        '{"type":"plugin","domain":"d","name":"N","description":"x","codeowners":[]}'
    )
    assert restored.page is None
    assert restored.to_dict()["page"] is None


def test_page_parsed() -> None:
    """Test that a declared page parses, without an icon by default, and round-trips."""
    manifest = ProviderManifest.from_json(_PAGE_JSON)
    assert manifest.page == ProviderPage(
        label="Picture frame", scope=Scope.LIBRARY_READ, icon="mdi-image-frame"
    )
    assert ProviderPage.from_dict({"label": "L", "scope": "library.read"}).icon is None
    assert ProviderManifest.from_json(manifest.to_json()) == manifest


def test_page_label_translated() -> None:
    """Test that the label of a page is translated from page.label of its provider."""
    manifest = ProviderManifest.from_json(_PAGE_JSON)
    with _resolver({"provider.frame.page.label": "Fotolijstje"}):
        assert manifest.to_dict()["page"]["label"] == "Fotolijstje"
    assert manifest.to_dict()["page"]["label"] == "Picture frame"


def test_page_label_translation_refused() -> None:
    """Test that a translated page label that is not one readable line keeps the English."""
    manifest = ProviderManifest.from_json(_PAGE_JSON)
    too_long = "x" * (MAX_TRANSLATED_MENU_ACTION_LABEL_LENGTH + 1)
    for value in ("Picture\nframe", too_long):
        with _resolver({"provider.frame.page.label": value}):
            assert manifest.to_dict()["page"]["label"] == "Picture frame"


@pytest.mark.parametrize(
    "page",
    ['{"label":"L"}', '[{"label":"L","scope":"library.read"}]', '"a"'],
)
def test_page_wrong_type_fails(page: str) -> None:
    """Test that a page of the wrong shape fails to parse the manifest."""
    with pytest.raises(InvalidFieldValue):
        ProviderManifest.from_json(
            '{"type":"plugin","domain":"d","name":"N","description":"x","codeowners":[],'
            f'"page":{page}}}'
        )


def test_features_missing_key_defaults_empty() -> None:
    """Test that a manifest without features declares none."""
    restored = ProviderManifest.from_json(
        '{"type":"plugin","domain":"d","name":"N","description":"x","codeowners":[]}'
    )
    assert restored.features == set()


def test_features_parsed() -> None:
    """Test that declared features parse and survive a roundtrip, an unknown one as UNKNOWN."""
    restored = ProviderManifest.from_json(
        '{"type":"plugin","domain":"d","name":"N","description":"x","codeowners":[],'
        '"features":["audio_source","not_a_feature"]}'
    )
    assert restored.features == {ProviderFeature.AUDIO_SOURCE, ProviderFeature.UNKNOWN}
    manifest = _manifest(features={ProviderFeature.AUDIO_SOURCE})
    assert ProviderManifest.from_json(manifest.to_json()).features == {ProviderFeature.AUDIO_SOURCE}


def test_mcp_tools_missing_key_defaults_empty() -> None:
    """Test that a manifest without mcp_tools has none."""
    restored = ProviderManifest.from_json(
        '{"type":"music","domain":"d","name":"N","description":"x","codeowners":[]}'
    )
    assert restored.mcp_tools == []


def test_mcp_tools_parsed() -> None:
    """Test that declared tools parse with their defaults and survive a round trip."""
    manifest = ProviderManifest.from_json(_MCP_TOOLS_JSON)
    assert manifest.mcp_tools == [
        ProviderMCPTool(
            id="play_station",
            description="Play a saved station on a player.",
            scope=Scope.QUEUES_CONTROL,
            input_schema={
                "type": "object",
                "properties": {
                    "station": {"type": "string", "description": "The name of the station."}
                },
                "required": ["station"],
            },
            requires_player=True,
        ),
        ProviderMCPTool(
            id="list_stations",
            description="List the saved stations.",
            scope=Scope.LIBRARY_READ,
        ),
    ]
    assert manifest.mcp_tools[1].input_schema == {}
    assert manifest.mcp_tools[1].requires_player is False
    assert ProviderManifest.from_json(manifest.to_json()) == manifest
    assert ProviderManifest.from_dict(manifest.to_dict()) == manifest


def test_mcp_tool_unknown_scope_and_keys() -> None:
    """Test that an unknown scope parses as UNKNOWN and unknown keys are ignored."""
    tool = ProviderMCPTool.from_dict(
        {"id": "a", "description": "D", "scope": "future.scope", "extra": True}
    )
    assert tool == ProviderMCPTool(id="a", description="D", scope=Scope.UNKNOWN)


@pytest.mark.parametrize(
    "mcp_tools",
    [
        '{"id":"a","description":"D","scope":"library.read"}',
        '[{"id":"a","description":"D"}]',
        '"a"',
    ],
)
def test_mcp_tools_wrong_type_fails(mcp_tools: str) -> None:
    """Test that tools of the wrong shape fail to parse the manifest."""
    with pytest.raises(InvalidFieldValue):
        ProviderManifest.from_json(
            '{"type":"plugin","domain":"d","name":"N","description":"x","codeowners":[],'
            f'"mcp_tools":{mcp_tools}}}'
        )


@pytest.mark.parametrize(
    "text",
    [
        "Show on the picture frame",
        "x" * MAX_MENU_ACTION_LABEL_LENGTH,
        "Op de fotolijst tonen",
        "Показать на рамке",
        "عرض على الإطار",
        "フォトフレームに表示",
        "می\u200cخواهم",  # noqa: RUF001 - Persian, with a zero width non-joiner
        "Family \U0001f468\u200d\U0001f469\u200d\U0001f467",
        "\U0001f5bc️",
    ],
)
def test_menu_action_label_accepted(text: str) -> None:
    """Test that one readable line of text in any script, emoji included, is a label."""
    assert is_menu_action_label(text)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "\u200b",
        "\ufeff",
        "\u00ad",
        "\u200b\u200d ",
        "Show\non the frame",
        "Show\ton the frame",
        "Show\x00",
        "Show\u2028on the frame",
        "Show\u2029on the frame",
        "Show\u202aon the frame",
        "Show\u202eemarf eht no",
        "Show\u2066on the frame",
        "Show\u2069",
        "x" * (MAX_MENU_ACTION_LABEL_LENGTH + 1),
    ],
)
def test_menu_action_label_refused(text: str) -> None:
    """Test that an invisible, multi-line, reordering or too long text is no label."""
    assert not is_menu_action_label(text)


def test_menu_action_label_longer_limit() -> None:
    """Test that the limit can be raised, as for a translated label."""
    text = "x" * MAX_TRANSLATED_MENU_ACTION_LABEL_LENGTH
    assert is_menu_action_label(text, MAX_TRANSLATED_MENU_ACTION_LABEL_LENGTH)
    assert not is_menu_action_label(text + "x", MAX_TRANSLATED_MENU_ACTION_LABEL_LENGTH)


@pytest.mark.parametrize(
    ("translation", "label"),
    [
        ("Toon op de fotolijst", "Toon op de fotolijst"),
        ("y" * 41, "y" * 41),
        (
            "y" * MAX_TRANSLATED_MENU_ACTION_LABEL_LENGTH,
            "y" * MAX_TRANSLATED_MENU_ACTION_LABEL_LENGTH,
        ),
        ("y" * (MAX_TRANSLATED_MENU_ACTION_LABEL_LENGTH + 1), "Show on the picture frame"),
        ("Toon op\nde fotolijst", "Show on the picture frame"),
        ("Toon \u202eop de fotolijst", "Show on the picture frame"),
        ("\u200b\u200b", "Show on the picture frame"),
    ],
)
def test_menu_action_translation_used_only_when_a_label(translation: str, label: str) -> None:
    """Test that a translation that is no label leaves the label of the manifest in the output."""
    manifest = ProviderManifest.from_json(_MENU_ACTIONS_JSON)
    with _resolver({"provider.frame.menu_actions.send_to_frame.label": translation}):
        labels = [action["label"] for action in manifest.to_dict()["menu_actions"]]
    assert labels == [label, "Play on the picture frame"]
