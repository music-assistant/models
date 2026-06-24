"""Model and helpers for Config entries."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Final, cast

from mashumaro import DataClassDictMixin, field_options, pass_through

from .constants import SECURE_STRING_SUBSTITUTE
from .enums import ConfigEntryType, PlayerType, ProviderStatus, ProviderType
from .translations import resolve_translation, translations_active

LOGGER = logging.getLogger(__name__)

ENCRYPT_CALLBACK: Callable[[str], str] | None = None
DECRYPT_CALLBACK: Callable[[str], str] | None = None


def _localized_base(override: str | None, key: str, group: str) -> str:
    """
    Return the translations base ``<group>.<slug>`` for a localized config field.

    The slug is the explicit ``override`` (a bare key, never a group-qualified path) or, by
    default, the entry's own ``key``/category — the group is always derived from the model.

    :param override: Optional caller-supplied key (a bare slug).
    :param key: The entry's own key (or category) used when no override is given.
    :param group: The localization group the slug lives under (e.g. ``config_entries``).
    """
    return f"{group}.{override if override is not None else key}"


_ConfigValueTypeSingle = (
    # order is important here for the (de)serialization!
    # https://github.com/Fatal1ty/mashumaro/pull/256
    bool | float | int | str
)
_ConfigValueTypeMulti = (
    # order is important here for the (de)serialization!
    # https://github.com/Fatal1ty/mashumaro/pull/256
    list[float] | list[int] | list[str] | list[bool]
)
ConfigValueType = _ConfigValueTypeSingle | _ConfigValueTypeMulti | None


ConfigEntryTypeMap: dict[ConfigEntryType, type[ConfigValueType]] = {
    ConfigEntryType.BOOLEAN: bool,
    ConfigEntryType.STRING: str,
    ConfigEntryType.SECURE_STRING: str,
    ConfigEntryType.INTEGER: int,
    ConfigEntryType.SPLITTED_STRING: str,
    ConfigEntryType.FLOAT: float,
    ConfigEntryType.LABEL: str,
    ConfigEntryType.DIVIDER: str,
    ConfigEntryType.ACTION: str,
    ConfigEntryType.ALERT: str,
    ConfigEntryType.ICON: str,
}

UI_ONLY = (
    ConfigEntryType.LABEL,
    ConfigEntryType.DIVIDER,
    ConfigEntryType.ACTION,
    ConfigEntryType.ALERT,
)


@dataclass
class ConfigValueOption(DataClassDictMixin):
    """Model for a value with separated name/value."""

    # value: the stored value identifying this option, and the first positional argument so a
    # value-only option can be written as ConfigValueOption("the_value"). Required (pass None
    # explicitly only when None is a meaningful sentinel).
    value: ConfigValueType
    # title: display title for the option. Optional: when omitted it is resolved from the
    # translations at serialization (keyed by the owning entry + this option's value). Dynamic,
    # data-driven options (player names, sample rates, ...) still pass a title directly.
    title: str | None = None
    # disabled: when True the option is shown but not selectable (e.g. a capability that is
    # currently unavailable), so clients can surface it greyed-out instead of omitting it.
    disabled: bool = False
    # disabled_reason: optional human-readable explanation of why the option is disabled, resolved
    # from the translations at serialization (keyed by the owning entry: disabled_reasons.<value>).
    disabled_reason: str | None = None


MULTI_VALUE_SPLITTER: Final[str] = "||"


@dataclass(kw_only=True)
class ConfigEntry(DataClassDictMixin):
    """Model for a Config Entry.

    The definition of something that can be configured
    for an object (e.g. provider or player)
    within Music Assistant.
    """

    # key: used as identifier for the entry, also for localization
    key: str
    type: ConfigEntryType
    default_value: ConfigValueType = None
    required: bool = True
    # options [optional]: select from list of possible values/options
    options: list[ConfigValueOption] = field(default_factory=list)
    # range [optional]: select values within range
    range: tuple[int, int] | None = None
    # description [optional]: extended description of the setting.
    description: str | None = None
    # help_link [optional]: link to help article.
    help_link: str | None = None
    # multi_value [optional]: allow multiple values from the list
    # NOTE: for using multi_value, it is required to use the MultiValueConfigEntry
    # class instead of ConfigEntry to prevent (de)serialization issues
    multi_value: bool = False
    # depends_on [optional]: needs to be set before this setting is visible in the frontend
    depends_on: str | None = None
    # depends_on_value [optional]: complementary to depends_on, only show if this value is set
    depends_on_value: ConfigValueType | None = None
    # depends_on_value_not [optional]: same as depends_on_value but inverted
    depends_on_value_not: ConfigValueType | None = None
    # hidden: hide from UI
    hidden: bool = False
    # read_only: prevent user from changing this setting (make it disabled)
    read_only: bool = False
    # category: category to group this setting into in the frontend (e.g. advanced)
    category: str = "generic"
    # action: (configentry)action that is needed to get the value for this entry
    action: str | None = None
    # action_label: default label for the action when no translation for the action is present
    action_label: str | None = None
    # immediate_apply: apply changes immediately when changed in the UI
    immediate_apply: bool = False
    # requires_reload: indicates that a reload of the provider (or player playback)
    # is required when this setting is changed
    requires_reload: bool = False
    # advanced: mark this setting as advanced (e.g. hide behind an advanced toggle in frontend)
    advanced: bool = False
    # translation_params / category_translation_params: optional positional arguments for the
    # {0}/{1} placeholders in this entry's label/description and category translation, provided
    # by the implementer.
    translation_params: list[str] | None = field(
        default=None, metadata=field_options(serialize="omit"), repr=False
    )
    category_translation_params: list[str] | None = field(
        default=None, metadata=field_options(serialize="omit"), repr=False
    )

    # validate: an optional custom validation callback (author-provided)
    validate: Callable[[ConfigValueType], bool] | None = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )

    # ----------------------------------------------------------------------------------
    # The fields below are populated by the server at runtime — consumers/providers
    # should NOT set these; they are filled in by Music Assistant.
    # ----------------------------------------------------------------------------------

    # label: localized display label, resolved from the translations at serialization.
    label: str | None = None
    # category_label: localized category display name, resolved from the translations at
    # serialization. The stable `category` value is still used for grouping.
    category_label: str | None = None
    # translation_owner: the namespace ("provider.<domain>"/"core.<domain>") this entry's strings
    # are resolved under; stamped by the config controller when the entry is served. Not serialized.
    translation_owner: str | None = field(
        default=None, metadata=field_options(serialize="omit"), repr=False
    )

    # translation_key / category_translation_key: server-set translation-key overrides (e.g. the
    # protocol-output block re-keys copied entries to keep their original translation key). Not
    # author-facing and not serialized; the structural defaults are config_entries.<key> /
    # config_categories.<category>.
    translation_key: str | None = field(
        default=None, metadata=field_options(serialize="omit"), repr=False
    )
    category_translation_key: str | None = field(
        default=None, metadata=field_options(serialize="omit"), repr=False
    )

    # value: the current value, set by the config manager/flow
    # (or in rare cases by the provider itself during action flows).
    value: ConfigValueType = None

    def __post_init__(self) -> None:
        """Run some basic sanity checks after init."""
        if self.type in UI_ONLY:
            self.required = False

    def __post_serialize__(self, d: dict[str, Any]) -> dict[str, Any]:
        """
        Localize human-readable fields from the translations for the connection locale.

        Resolves label/description/option titles and the category name under this entry's owner
        namespace (keyed by config_entries.<key> / config_categories.<category>). A server-set
        translation_key/category_translation_key override is the bare slug under that same group,
        unless it is fully qualified. No-op when nothing matches, so the in-code values are kept.
        The translation machinery fields are not serialized.
        """
        owner = self.translation_owner
        base = _localized_base(self.translation_key, self.key, "config_entries")
        label = resolve_translation(f"{base}.label", owner=owner, params=self.translation_params)
        if label is not None:
            d["label"] = label
        description = resolve_translation(
            f"{base}.description", owner=owner, params=self.translation_params
        )
        if description is not None:
            d["description"] = description
        if self.action is not None:
            action_label = resolve_translation(f"{base}.action_label", owner=owner)
            if action_label is not None:
                d["action_label"] = action_label
        for option_dict, option in zip(d.get("options", []), self.options, strict=False):
            title = resolve_translation(f"{base}.options.{option.value}", owner=owner)
            if title is not None:
                option_dict["title"] = title
            if option.disabled:
                reason = resolve_translation(f"{base}.disabled_reasons.{option.value}", owner=owner)
                if reason is not None:
                    option_dict["disabled_reason"] = reason
        category_key = _localized_base(
            self.category_translation_key, self.category, "config_categories"
        )
        category_label = resolve_translation(
            category_key, owner=owner, params=self.category_translation_params
        )
        if category_label is not None:
            d["category_label"] = category_label
        return d

    def parse_value(
        self,
        value: ConfigValueType,
        allow_none: bool = True,
        raise_on_error: bool = True,
    ) -> ConfigValueType:
        """Parse value from the config entry details and plain value."""
        if self.type == ConfigEntryType.LABEL:
            value = self.label
        elif self.type in UI_ONLY:
            value = value or self.default_value

        if value is None:
            value = self.default_value

        if isinstance(value, list) and not self.multi_value:
            if raise_on_error:
                raise ValueError(f"{self.key} must be a single value")
            value = self.default_value
        if self.multi_value and not isinstance(value, list):
            if raise_on_error:
                raise ValueError(f"value for {self.key} must be a list")
            value = self.default_value

        # handle some value type conversions caused by the serialization
        def convert_value(_value: _ConfigValueTypeSingle) -> _ConfigValueTypeSingle:
            if self.type == ConfigEntryType.FLOAT and isinstance(_value, int | str):
                return float(_value)
            if self.type == ConfigEntryType.INTEGER and isinstance(_value, float | str):
                return int(_value)
            if self.type == ConfigEntryType.BOOLEAN and isinstance(_value, int | str):
                return bool(_value)
            return _value

        if value is None and self.required and not allow_none:
            if raise_on_error:
                raise ValueError(f"{self.key} is required")
            value = self.default_value

        # handle optional validation callback
        if self.validate is not None and not (self.validate(value)):
            if raise_on_error:
                raise ValueError(f"{value} is not a valid value for {self.key}")
            value = self.default_value

        if self.multi_value and value is not None:
            value = cast("_ConfigValueTypeMulti", value)
            value = [convert_value(x) for x in value]  # type: ignore[assignment]
        elif value is not None:
            value = cast("_ConfigValueTypeSingle", value)
            value = convert_value(value)

        self.value = value
        return self.value

    def get_splitted_values(self) -> tuple[str, ...] | list[tuple[str, ...]]:
        """Return split values for SPLITTED_STRING type."""
        if self.type != ConfigEntryType.SPLITTED_STRING:
            raise ValueError(f"{self.key} is not a SPLITTED_STRING")
        value = self.value or self.default_value
        if self.multi_value:
            assert isinstance(value, list)
            value = cast("list[str]", value)
            return [tuple(x.split(MULTI_VALUE_SPLITTER, 1)) for x in value]
        assert isinstance(value, str)
        return tuple(value.split(MULTI_VALUE_SPLITTER, 1))


@dataclass
class Config(DataClassDictMixin):
    """Base Configuration object."""

    values: dict[str, ConfigEntry]

    def get_value(self, key: str, default: ConfigValueType = None) -> ConfigValueType:
        """Return config value for given key."""
        try:
            config_value = self.values[key]
        except KeyError:
            return default
        if config_value.type == ConfigEntryType.SECURE_STRING and config_value.value:
            assert isinstance(config_value.value, str)
            assert DECRYPT_CALLBACK is not None
            return DECRYPT_CALLBACK(config_value.value)

        return config_value.value

    @classmethod
    def parse(
        cls,
        config_entries: Iterable[ConfigEntry],
        raw: dict[str, Any],
    ) -> Config:
        """Parse Config from the raw values (as stored in persistent storage)."""
        conf = cls.from_dict({**raw, "values": {}})
        owner = conf._translation_owner()  # noqa: SLF001 - own protected method on a same-class instance
        for entry in config_entries:
            # unpack Enum value in default_value
            if isinstance(entry.default_value, Enum):
                entry.default_value = entry.default_value.value  # type: ignore[unreachable]
            # copy original entry to prevent mutation, and stamp the owner for string resolution
            copied = deepcopy(entry)
            copied.translation_owner = owner
            conf.values[entry.key] = copied
            copied.parse_value(
                raw.get("values", {}).get(entry.key),
                allow_none=True,
                raise_on_error=False,
            )
        return conf

    def _translation_owner(self) -> str | None:
        """Return the translations owner namespace for this config's entries (None = common)."""
        return None

    def to_raw(self) -> dict[str, Any]:
        """Return minimized/raw dict to store in persistent storage."""

        def _handle_value(
            value: ConfigEntry,
        ) -> ConfigValueType:
            if value.type == ConfigEntryType.SECURE_STRING:
                assert isinstance(value.value, str)
                assert ENCRYPT_CALLBACK is not None
                return ENCRYPT_CALLBACK(value.value)
            return value.value

        res = self.to_dict()
        res["values"] = {
            x.key: _handle_value(x)
            for x in self.values.values()
            if (x.value != x.default_value and x.type not in UI_ONLY)
        }
        return res

    def __post_serialize__(self, d: dict[str, Any]) -> dict[str, Any]:
        """Adjust dict object after it has been serialized."""
        for key, value in self.values.items():
            # drop all password values from the serialized dict
            # API consumers (including the frontend) are not allowed to retrieve it
            # (even if its encrypted) but they can only set it.
            if value.value and value.type == ConfigEntryType.SECURE_STRING:
                d["values"][key]["value"] = SECURE_STRING_SUBSTITUTE
        return d

    def update(self, update: dict[str, ConfigValueType]) -> set[str]:
        """Update Config with updated values."""
        changed_keys: set[str] = set()

        # root values (enabled, name)
        root_values = ("enabled", "name")
        for key in root_values:
            if key not in update:
                continue
            cur_val = getattr(self, key)
            new_val = update[key]
            if new_val == cur_val:
                continue
            setattr(self, key, new_val)
            changed_keys.add(key)

        for key, new_val in update.items():
            if key in root_values:
                continue
            if key not in self.values:
                continue
            cur_val = self.values[key].value if key in self.values else None
            # parse entry to do type validation
            parsed_val = self.values[key].parse_value(new_val)
            if cur_val != parsed_val:
                changed_keys.add(f"values/{key}")

        return changed_keys

    def validate(self) -> None:
        """Validate if configuration is valid."""
        # For now we just use the parse method to check for not allowed None values
        # this can be extended later
        for value in self.values.values():
            value.parse_value(value.value, allow_none=False)


@dataclass
class ProviderError(DataClassDictMixin):
    """Structured, localizable error describing why a provider failed to load."""

    error_code: int  # MusicAssistantError.error_code; 999 for non-MusicAssistant exceptions
    message: str
    # translation_key: optional bare slug to localize the message; __post_serialize__ derives the
    # errors.<slug> group and resolves it owner-first then common (mirrors ErrorResultMessage)
    translation_key: str | None = None
    translation_args: list[Any] = field(default_factory=list)
    # translation_owner: owning namespace ("provider.<domain>"/"core.<domain>") consulted before
    # common — set when a provider/controller defines its own message for the key
    translation_owner: str | None = None

    def __post_serialize__(self, d: dict[str, Any]) -> dict[str, Any]:
        """Localize `message` from translation_key when a resolver is active; strip machinery."""
        if self.translation_key:
            params = [str(a) for a in self.translation_args] if self.translation_args else None
            localized = resolve_translation(
                f"errors.{self.translation_key}", owner=self.translation_owner, params=params
            )
            if localized is not None:
                d["message"] = localized
        if translations_active():
            d.pop("translation_key", None)
            d.pop("translation_args", None)
            d.pop("translation_owner", None)
        return d


@dataclass
class ProviderConfig(Config):
    """Provider(instance) Configuration."""

    type: ProviderType
    domain: str
    instance_id: str
    # enabled: boolean to indicate if the provider is enabled
    enabled: bool = True
    # name: an (optional) custom name for this provider instance/config
    name: str | None = None
    # default_name: default name to use/persist when there is no name set by the user
    default_name: str | None = None
    # last_error: structured error if the provider could not be setup with this config
    last_error: ProviderError | None = None
    # status: load/lifecycle status, derived and stamped server-side on the api read path.
    # Never persisted (see to_raw) and not set during normal config save/load.
    status: ProviderStatus | None = None

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Coerce a legacy string last_error (from older settings.json) into a ProviderError."""
        last_error = d.get("last_error")
        if isinstance(last_error, str):
            d["last_error"] = {"error_code": 999, "message": last_error}
        return d

    def to_raw(self) -> dict[str, Any]:
        """Return minimized/raw dict to store; the derived `status` is never persisted."""
        res = super().to_raw()
        res.pop("status", None)
        return res

    def _translation_owner(self) -> str | None:
        return f"provider.{self.domain}"


@dataclass
class PlayerConfig(Config):
    """Player Configuration."""

    provider: str
    player_id: str
    # enabled: boolean to indicate if the player is enabled
    enabled: bool = True
    # name: an (optional) custom name for this player
    name: str | None = None
    # default_name: default name to use/persist when there is no name set by the user
    default_name: str | None = None
    # player_type: type of player (player, protocol, group etc.)
    player_type: PlayerType = PlayerType.PLAYER

    def _translation_owner(self) -> str | None:
        return f"provider.{self.provider}"


@dataclass
class PlayerQueueConfig(Config):
    """PlayerQueue Configuration."""

    queue_id: str

    def _translation_owner(self) -> str | None:
        # queue config entries are owned by the player_queues core controller's strings
        return "core.player_queues"


@dataclass
class CoreConfig(Config):
    """CoreController Configuration."""

    domain: str  # domain/name of the core module
    # last_error: an optional error message if the module could not be setup with this config
    last_error: str | None = None

    def _translation_owner(self) -> str | None:
        return f"core.{self.domain}"
