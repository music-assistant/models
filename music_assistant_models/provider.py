"""Models for providers and plugins in the MA ecosystem."""

from __future__ import annotations

import asyncio
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

from mashumaro.mixins.orjson import DataClassORJSONMixin

from .auth import Scope
from .enums import (
    ArtistType,
    MediaType,
    ProviderFeature,
    ProviderIconVariant,
    ProviderStage,
    ProviderTier,
    ProviderType,
)
from .translations import resolve_translation

# the longest label of a menu action in a manifest
MAX_MENU_ACTION_LABEL_LENGTH: Final = 40
# the longest translated label of a menu action: texts grow in translation, and a translator
# does not see the limit, so a translation gets more room than the English in the manifest
MAX_TRANSLATED_MENU_ACTION_LABEL_LENGTH: Final = 80
# what breaks a label out of its single line or reorders the text around it: control
# characters, line and paragraph separators, and the bidirectional embeddings, overrides
# and isolates
_LABEL_FORBIDDEN_CATEGORIES: Final = frozenset({"Cc", "Zl", "Zp"})
_LABEL_FORBIDDEN_CHARACTERS: Final = frozenset(
    "\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
)
# letters, numbers, punctuation and symbols: the characters a reader can see
_LABEL_VISIBLE_CATEGORY_GROUPS: Final = ("L", "N", "P", "S")


def is_menu_action_label(text: str, max_length: int = MAX_MENU_ACTION_LABEL_LENGTH) -> bool:
    """
    Return whether a text can be shown as the label of a menu action.

    A label is one line of at most ``max_length`` characters, with at least one character a
    reader can see and none that breaks the line or reorders the text around it.

    :param text: The text to check.
    :param max_length: The most characters the label may have.
    """
    return (
        len(text) <= max_length
        and any(unicodedata.category(char)[0] in _LABEL_VISIBLE_CATEGORY_GROUPS for char in text)
        and not any(
            unicodedata.category(char) in _LABEL_FORBIDDEN_CATEGORIES
            or char in _LABEL_FORBIDDEN_CHARACTERS
            for char in text
        )
    )


@dataclass
class ProviderMenuAction(DataClassORJSONMixin):
    """An entry a provider adds to the menu of a media item."""

    # id: names the action within its provider
    id: str
    # label: English text of the menu entry, translated from menu_actions.<id>.label
    # in the texts of the provider
    label: str
    # media_types: the kinds of media item the entry is offered for
    media_types: list[MediaType]
    # scope: what a user needs to use the action; a client does not show it to anyone without it
    scope: Scope
    # icon: name of the material design icon (https://pictogrammers.com/library/mdi)
    icon: str | None = None
    # requires_player: whether the action acts on a player; the client then offers it with the
    # ways to play the item and also passes the player to act on
    requires_player: bool = False


@dataclass
class ProviderManifest(DataClassORJSONMixin):
    """ProviderManifest, details of a provider."""

    type: ProviderType
    domain: str
    name: str
    description: str
    codeowners: list[str]

    # optional params

    # stage: the stage of the provider, used to determine if it is stable or experimental
    stage: ProviderStage = ProviderStage.STABLE
    # tier: who maintains the provider, defaults to community so a missing value never claims core
    tier: ProviderTier = ProviderTier.COMMUNITY
    # requirements: list of (pip style) python packages required for this provider
    requirements: list[str] = field(default_factory=list)
    # documentation: link/url to documentation.
    documentation: str | None = None
    # support_url: where the maintainer takes bug reports and questions,
    # when None reports go to the project's support repository
    support_url: str | None = None
    # multi_instance: whether multiple instances of the same provider are allowed/possible
    multi_instance: bool = False
    # builtin: whether this provider is a system/builtin provider, loaded by default
    builtin: bool = False
    # allow_disable: whether this provider can be disabled (used with builtin)
    allow_disable: bool = True
    # depends_on: depends on another provider to function
    depends_on: str | None = None
    # icon: name of the material design icon (https://pictogrammers.com/library/mdi)
    icon: str | None = None
    # icon_images: which icon variants this provider supplies as image files
    # (svg or transparent png in the provider folder).
    icon_images: list[ProviderIconVariant] = field(default_factory=list)
    # mdns_discovery: list of mdns types to discover
    mdns_discovery: list[str] | None = None
    # upnp_discovery: list of SSDP search targets to discover
    upnp_discovery: list[str] | None = None
    # has_setup_flow: if True, this provider offers an interactive setup flow
    # that can also be re-run on demand (reconfigure), regardless of auth state
    has_setup_flow: bool = False
    # self_service: whether a member may set up (and reconfigure) an instance of this
    # provider as a music source of its own; when False, only a user who manages every
    # music source may set it up
    self_service: bool = True

    # credits: list of credits/attributions
    # e.g. for libraries used, icons, etc.
    # accepts markdown formatting.
    credits: list[str] = field(default_factory=list)
    # menu_actions: entries this provider adds to the menu of a media item
    menu_actions: list[ProviderMenuAction] = field(default_factory=list)

    @classmethod
    async def parse(cls, manifest_file: str) -> ProviderManifest:
        """Parse ProviderManifest from file."""
        file_contents = await asyncio.to_thread(Path(manifest_file).read_text)
        return cls.from_json(file_contents)

    def __post_serialize__(self, d: dict[Any, Any]) -> dict[Any, Any]:
        """Localize name/description/menu action labels when a translation resolver is set."""
        # core controllers use the core.<domain> namespace, providers use provider.<domain>
        namespace = "core" if self.type == ProviderType.CORE else "provider"
        if (value := resolve_translation(f"{namespace}.{self.domain}.manifest.name")) is not None:
            d["name"] = value
        if (
            value := resolve_translation(f"{namespace}.{self.domain}.manifest.description")
        ) is not None:
            d["description"] = value
        for action in d.get("menu_actions", []):
            key = f"{namespace}.{self.domain}.menu_actions.{action['id']}.label"
            value = resolve_translation(key)
            if value is not None and is_menu_action_label(
                value, MAX_TRANSLATED_MENU_ACTION_LABEL_LENGTH
            ):
                action["label"] = value
        return d


@dataclass
class ProviderInstance(DataClassORJSONMixin):
    """Provider instance details when a provider is serialized over the api."""

    type: ProviderType
    domain: str
    name: str
    instance_id: str
    supported_features: set[ProviderFeature]
    available: bool
    is_streaming_provider: bool | None = None  # music providers only
    supported_artist_types: set[ArtistType] = field(default_factory=set)  # music providers only
    # lookup_key: kept for backwards compatibility; mirrors the server wire value (== instance_id)
    lookup_key: str | None = None
