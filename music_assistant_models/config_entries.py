"""Model and helpers for Config entries."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, cast

from mashumaro import DataClassDictMixin

from .constants import SECURE_STRING_SUBSTITUTE
from .enums import ConfigEntryType, ProviderType

LOGGER = logging.getLogger(__name__)

ENCRYPT_CALLBACK: Callable[[str], str] | None = None
DECRYPT_CALLBACK: Callable[[str], str] | None = None

ConfigValueType = (
    # order is important here for the (de)serialization!
    # https://github.com/Fatal1ty/mashumaro/pull/256
    bool | float | int | str | tuple[int, int]
)
ConfigValueTypeMulti = (
    # order is important here for the (de)serialization!
    # https://github.com/Fatal1ty/mashumaro/pull/256
    list[bool] | list[float] | list[int] | list[str] | list[tuple[int, int]]
)

ConfigValueTypes = ConfigValueType | ConfigValueTypeMulti | None

ConfigEntryTypeMap: dict[ConfigEntryType, type[ConfigValueType]] = {
    ConfigEntryType.BOOLEAN: bool,
    ConfigEntryType.STRING: str,
    ConfigEntryType.SECURE_STRING: str,
    ConfigEntryType.INTEGER: int,
    ConfigEntryType.INTEGER_TUPLE: tuple[int, int],
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

    title: str
    value: ConfigValueType


@dataclass(kw_only=True)
class _ConfigEntry(DataClassDictMixin):
    """Model for a Config Entry.

    The definition of something that can be configured
    for an object (e.g. provider or player)
    within Music Assistant.
    """

    # key: used as identifier for the entry, also for localization
    key: str
    type: ConfigEntryType
    # label: default label when no translation for the key is present
    label: str
    default_value: ConfigValueType | ConfigValueTypeMulti | None = None
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
    # depends_on [optional]: needs to be set before this setting is enabled in the frontend
    depends_on: str | None = None
    # depends_on_value [optional]: complementary to depends_on, only enable if this value is set
    depends_on_value: str | None = None
    # hidden: hide from UI
    hidden: bool = False
    # category: category to group this setting into in the frontend (e.g. advanced)
    category: str = "generic"
    # action: (configentry)action that is needed to get the value for this entry
    action: str | None = None
    # action_label: default label for the action when no translation for the action is present
    action_label: str | None = None
    # value: set by the config manager/flow (or in rare cases by the provider itself)
    value: ConfigValueType | ConfigValueTypeMulti | None = None

    def __post_init__(self) -> None:
        """Run some basic sanity checks after init."""
        if self.multi_value and not isinstance(self, MultiValueConfigEntry):
            raise ValueError(f"{self.key} must be a MultiValueConfigEntry")
        if self.type in UI_ONLY:
            self.required = False

    def parse_value(
        self,
        value: ConfigValueTypes,
        allow_none: bool = True,  # noqa: ARG002
    ) -> ConfigValueTypes:
        """Parse value from the config entry details and plain value."""
        self.value = value
        return self.value


@dataclass(kw_only=True)
class ConfigEntry(_ConfigEntry):
    """Model for a Config Entry.

    The definition of something that can be configured
    for an object (e.g. provider or player)
    within Music Assistant.
    """

    multi_value: bool = False
    default_value: ConfigValueType | None = None
    value: ConfigValueType | None = None

    def parse_value(  # type: ignore[override]
        self,
        value: ConfigValueType | None,
        allow_none: bool = True,
    ) -> ConfigValueType | None:
        """Parse value from the config entry details and plain value."""
        if self.type == ConfigEntryType.LABEL:
            value = self.label
        elif self.type in UI_ONLY:
            value = cast(str | None, value or self.default_value)

        if value is None and (not self.required or allow_none):
            value = cast(ConfigValueType | None, self.default_value)

        if value is None and self.required:
            raise ValueError(f"{self.key} is required")

        self.value = value
        return self.value


@dataclass(kw_only=True)
class MultiValueConfigEntry(_ConfigEntry):
    """Model for a Config Entry which allows multiple values to be selected.

    This is a helper class to handle multiple values in a single config entry,
    otherwise the serializer gets confused with the types.
    """

    multi_value: bool = True
    default_value: ConfigValueTypeMulti = field(default_factory=list)
    value: ConfigValueTypeMulti | None = None

    def parse_value(  # type: ignore[override]
        self,
        value: ConfigValueTypeMulti | None,
        allow_none: bool = True,
    ) -> ConfigValueTypeMulti:
        """Parse value from the config entry details and plain value."""
        if value is None and (not self.required or allow_none):
            value = self.default_value
        if value is None:
            raise ValueError(f"{self.key} is required")
        if self.multi_value and not isinstance(value, list):
            raise ValueError(f"{self.key} must be a list")

        self.value = value
        return self.value

    def __post_init__(self) -> None:
        """Run some basic sanity checks after init."""
        super().__post_init__()
        if self.multi_value and not isinstance(self.default_value, list):
            raise ValueError(f"default value for {self.key} must be a list")


@dataclass
class Config(DataClassDictMixin):
    """Base Configuration object."""

    values: dict[str, ConfigEntry | MultiValueConfigEntry]

    def get_value(self, key: str) -> ConfigValueTypes:
        """Return config value for given key."""
        config_value = self.values[key]
        if config_value.type == ConfigEntryType.SECURE_STRING and config_value.value:
            assert isinstance(config_value.value, str)
            assert DECRYPT_CALLBACK is not None
            return DECRYPT_CALLBACK(config_value.value)

        return config_value.value

    @classmethod
    def parse(
        cls,
        config_entries: Iterable[ConfigEntry | MultiValueConfigEntry],
        raw: dict[str, Any],
    ) -> Config:
        """Parse Config from the raw values (as stored in persistent storage)."""
        conf = cls.from_dict({**raw, "values": {}})
        for entry in config_entries:
            # unpack Enum value in default_value
            if isinstance(entry.default_value, Enum):
                entry.default_value = entry.default_value.value  # type: ignore[unreachable]
            # create a copy of the entry
            if entry.multi_value:
                conf.values[entry.key] = MultiValueConfigEntry.from_dict(entry.to_dict())
            else:
                conf.values[entry.key] = ConfigEntry.from_dict(entry.to_dict())
            conf.values[entry.key].parse_value(
                raw.get("values", {}).get(entry.key), allow_none=True
            )
        return conf

    def to_raw(self) -> dict[str, Any]:
        """Return minimized/raw dict to store in persistent storage."""

        def _handle_value(
            value: ConfigEntry | MultiValueConfigEntry,
        ) -> ConfigValueTypes:
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

    def update(self, update: dict[str, ConfigValueTypes]) -> set[str]:
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
            parsed_val = self.values[key].parse_value(new_val)  # type: ignore[arg-type]
            if cur_val != parsed_val:
                changed_keys.add(f"values/{key}")

        return changed_keys

    def validate(self) -> None:
        """Validate if configuration is valid."""
        # For now we just use the parse method to check for not allowed None values
        # this can be extended later
        for value in self.values.values():
            value.parse_value(value.value, allow_none=False)  # type: ignore[arg-type]


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
    # last_error: an optional error message if the provider could not be setup with this config
    last_error: str | None = None


@dataclass
class PlayerConfig(Config):
    """Player Configuration."""

    provider: str
    player_id: str
    # enabled: boolean to indicate if the player is enabled
    enabled: bool = True
    # name: an (optional) custom name for this player
    name: str | None = None
    # available: boolean to indicate if the player is available
    available: bool = True
    # default_name: default name to use when there is no name available
    default_name: str | None = None


@dataclass
class CoreConfig(Config):
    """CoreController Configuration."""

    domain: str  # domain/name of the core module
    # last_error: an optional error message if the module could not be setup with this config
    last_error: str | None = None
