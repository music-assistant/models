"""Authentication models for Music Assistant API."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from mashumaro.mixins.orjson import DataClassORJSONMixin


class UserRole(StrEnum):
    """
    The role ids of the builtin user roles.

    A role is identified by its (string) id, of which these are the builtin roles.
    Admins may create custom roles as well, so User.role is a plain string
    and not limited to these values.
    """

    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    SERVICE = "service"


class AuthProviderType(StrEnum):
    """Authentication provider type enum."""

    BUILTIN = "builtin"
    HOME_ASSISTANT = "homeassistant"

    @classmethod
    def _missing_(cls, value: object) -> AuthProviderType:  # noqa: ARG003
        """Return BUILTIN if an unknown value is provided."""
        return cls.BUILTIN


class Scope(StrEnum):
    """Scope enum for fine grained access to (parts of) the API."""

    ALL = "*"
    LIBRARY_READ = "library.read"
    LIBRARY_WRITE = "library.write"
    LIBRARY_MANAGE = "library.manage"
    PLAYERS_READ = "players.read"
    PLAYERS_CONTROL = "players.control"
    QUEUES_READ = "queues.read"
    QUEUES_CONTROL = "queues.control"
    PROVIDERS_READ = "providers.read"
    CONFIG_PLAYERS_READ = "config.players.read"
    CONFIG_PLAYERS_WRITE = "config.players.write"
    CONFIG_PROVIDERS_READ = "config.providers.read"
    CONFIG_PROVIDERS_WRITE = "config.providers.write"
    CONFIG_PROVIDERS_OWN = "config.providers.own"
    CONFIG_CORE_READ = "config.core.read"
    CONFIG_CORE_WRITE = "config.core.write"
    USERS_READ = "users.read"
    USERS_MANAGE = "users.manage"
    USERS_IMPERSONATE = "users.impersonate"
    USERS_INVITE = "users.invite"
    SYSTEM_READ = "system.read"
    SYSTEM_MANAGE = "system.manage"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> Scope:  # noqa: ARG003
        """Return UNKNOWN (which grants no access) if an unknown value is provided."""
        return cls.UNKNOWN


@dataclass
class User(DataClassORJSONMixin):
    """User model."""

    user_id: str
    username: str
    # the id of the role assigned to the user (see UserRole for the builtin roles)
    role: str
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    display_name: str | None = None
    avatar_url: str | None = None
    preferences: dict[str, Any] = field(default_factory=dict)
    provider_filter: list[str] = field(default_factory=list)
    player_filter: list[str] = field(default_factory=list)


@dataclass
class UserSummary(DataClassORJSONMixin):
    """The public face of a user account, safe to serve to every member."""

    user_id: str
    username: str
    display_name: str | None = None
    avatar_url: str | None = None

    @classmethod
    def from_user(cls, user: User) -> UserSummary:
        """Return the summary of the given user account."""
        return cls(
            user_id=user.user_id,
            username=user.username,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
        )


@dataclass
class Role(DataClassORJSONMixin):
    """A user role: a named set of scopes."""

    role_id: str
    name: str
    scopes: list[Scope] = field(default_factory=list)
    # builtin roles ship with Music Assistant and can not be changed or removed
    builtin: bool = False


@dataclass
class UserAuthProvider(DataClassORJSONMixin):
    """Link between a User and an Authentication Provider."""

    link_id: str
    user_id: str
    provider_type: AuthProviderType
    provider_user_id: str  # The user ID from the provider (e.g., HA user ID)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AuthToken(DataClassORJSONMixin):
    """Authentication token model."""

    token_id: str
    user_id: str
    token_hash: str
    name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    is_long_lived: bool = False
