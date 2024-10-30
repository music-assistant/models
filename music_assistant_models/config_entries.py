"""Model and helpers for Config entries."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import Enum
from types import NoneType
from typing import Any

from mashumaro import DataClassDictMixin

from .constants import SECURE_STRING_SUBSTITUTE
from .enums import ConfigEntryType, ProviderType

LOGGER = logging.getLogger(__name__)

ENCRYPT_CALLBACK: Callable[[str], str] | None = None
DECRYPT_CALLBACK: Callable[[str], str] | None = None

ConfigValueType = (
    str
    | int
    | float
    | bool
    | list[str]
    | list[tuple[int, int]]
    | tuple[int, int]
    | list[int]
    | Enum
    | None
)

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


@dataclass
class ConfigEntry(DataClassDictMixin):
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
    default_value: ConfigValueType = None
    required: bool = True
    # options [optional]: select from list of possible values/options
    options: tuple[ConfigValueOption, ...] | None = None
    # range [optional]: select values within range
    range: tuple[int, int] | None = None
    # description [optional]: extended description of the setting.
    description: str | None = None
    # help_link [optional]: link to help article.
    help_link: str | None = None
    # multi_value [optional]: allow multiple values from the list
    multi_value: bool = False
    # depends_on [optional]: needs to be set before this setting shows up in frontend
    depends_on: str | None = None
    # hidden: hide from UI
    hidden: bool = False
    # category: category to group this setting into in the frontend (e.g. advanced)
    category: str = "generic"
    # action: (configentry)action that is needed to get the value for this entry
    action: str | None = None
    # action_label: default label for the action when no translation for the action is present
    action_label: str | None = None
    # value: set by the config manager/flow (or in rare cases by the provider itself)
    value: ConfigValueType = None

    def parse_value(
        self,
        value: ConfigValueType,
        allow_none: bool = True,
    ) -> ConfigValueType:
        """Parse value from the config entry details and plain value."""
        expected_type = list if self.multi_value else ConfigEntryTypeMap.get(self.type, NoneType)
        if value is None:
            value = self.default_value
        if value is None and (not self.required or allow_none):
            expected_type = NoneType
        if self.type == ConfigEntryType.LABEL:
            value = self.label
        if not isinstance(value, expected_type):
            # handle common conversions/mistakes
            if expected_type is float and isinstance(value, int):
                self.value = float(value)
                return self.value
            if expected_type is int and isinstance(value, float):
                self.value = int(value)
                return self.value
            for val_type in (int, float):
                # convert int/float from string
                if expected_type == val_type and isinstance(value, str):
                    try:
                        self.value = val_type(value)
                    except ValueError:
                        pass
                    else:
                        return self.value
            if self.type in UI_ONLY:
                self.value = self.default_value
                return self.value
            # fallback to default
            if self.default_value is not None:
                LOGGER.warning(
                    "%s has unexpected type: %s, fallback to default",
                    self.key,
                    type(self.value),
                )
                value = self.default_value
            if not (value is None and allow_none):
                msg = f"{self.key} has unexpected type: {type(value)}"
                raise ValueError(msg)
        self.value = value
        return self.value


@dataclass
class Config(DataClassDictMixin):
    """Base Configuration object."""

    values: dict[str, ConfigEntry]

    def get_value(self, key: str) -> ConfigValueType:
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
        config_entries: Iterable[ConfigEntry],
        raw: dict[str, Any],
    ) -> Config:
        """Parse Config from the raw values (as stored in persistent storage)."""
        conf = cls.from_dict({**raw, "values": {}})
        for entry in config_entries:
            # unpack Enum value in default_value
            if isinstance(entry.default_value, Enum):
                entry.default_value = entry.default_value.value
            # create a copy of the entry
            conf.values[entry.key] = ConfigEntry.from_dict(entry.to_dict())
            conf.values[entry.key].parse_value(
                raw.get("values", {}).get(entry.key), allow_none=True
            )
        return conf

    def to_raw(self) -> dict[str, Any]:
        """Return minimized/raw dict to store in persistent storage."""

        def _handle_value(value: ConfigEntry) -> ConfigValueType:
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
