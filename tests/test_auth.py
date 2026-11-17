"""Tests for the authentication models."""

import pytest

from music_assistant_models.auth import (
    AuthProviderType,
    Role,
    Scope,
    SignInMethod,
    SignInOptions,
    User,
    UserRole,
    UserSummary,
)
from music_assistant_models.enums import ProviderType


def test_user_role_validation() -> None:
    """Test that an unknown (builtin) user role raises on validation."""
    with pytest.raises(ValueError, match="some_future_role"):
        UserRole("some_future_role")
    assert UserRole("admin") == UserRole.ADMIN


def test_auth_provider_type_missing() -> None:
    """Test that an unknown auth provider type falls back to UNKNOWN, never to BUILTIN."""
    assert AuthProviderType("some_future_provider") == AuthProviderType.UNKNOWN
    assert AuthProviderType("homeassistant") == AuthProviderType.HOME_ASSISTANT
    assert AuthProviderType("oidc") == AuthProviderType.OIDC
    assert AuthProviderType("apple") == AuthProviderType.APPLE
    assert AuthProviderType("google") == AuthProviderType.GOOGLE


def test_auth_provider_type_enum() -> None:
    """Test that auth is a provider type of its own."""
    assert ProviderType("auth") == ProviderType.AUTH


def test_sign_in_method_defaults_and_roundtrip() -> None:
    """Test the defaults of a sign-in method and that it round trips."""
    method = SignInMethod.from_dict(
        {
            "provider_id": "oidc--abc123",
            "provider_type": "some_future_type",
            "name": "Company login",
            "icon": "mdi-key",
        }
    )
    # the type stays the plain string the server sent
    assert method.provider_type == "some_future_type"
    assert method.requires_redirect is True
    assert method.available is True
    assert method.unavailable_reason is None
    assert method.supports_remote_app is False
    assert SignInMethod.from_dict(method.to_dict()) == method


def test_sign_in_options_defaults_and_roundtrip() -> None:
    """Test that sign-in options default to the password form only and round trip."""
    options = SignInOptions.from_dict({})
    assert options.methods == []
    assert options.password_enabled is True
    assert options.auto_launch_provider_id is None

    options = SignInOptions(
        methods=[
            SignInMethod(
                provider_id="homeassistant",
                provider_type="homeassistant",
                name="Home Assistant",
                icon="mdi-home-assistant",
                available=False,
                unavailable_reason="provider_unavailable",
            )
        ],
        password_enabled=False,
        auto_launch_provider_id="homeassistant",
    )
    assert SignInOptions.from_dict(options.to_dict()) == options


def test_scope_missing() -> None:
    """Test that an unknown scope falls back to UNKNOWN (which grants no access)."""
    assert Scope("some.future.scope") == Scope.UNKNOWN
    assert Scope("library.read") == Scope.LIBRARY_READ


def test_user_allow_explicit() -> None:
    """Test that a user may get explicit content by default and round trips the setting."""
    # a user from an older server, without the field, still deserializes
    user = User.from_dict({"user_id": "abc123", "username": "testuser", "role": "user"})
    assert user.allow_explicit is True

    user.allow_explicit = False
    assert user.to_dict()["allow_explicit"] is False
    assert User.from_dict(user.to_dict()).allow_explicit is False


def test_config_providers_own_scope() -> None:
    """Test that the scope for managing one's own provider configs resolves."""
    assert Scope("config.providers.own") is Scope.CONFIG_PROVIDERS_OWN


def test_user_with_unknown_role_deserializes() -> None:
    """Test that a User with an unknown role id deserializes with the role id preserved."""
    user = User.from_dict(
        {
            "user_id": "abc123",
            "username": "testuser",
            "role": "some_future_role",
        }
    )
    # the role id is preserved as-is, as it may be the id of a custom role
    assert user.role == "some_future_role"


def test_user_summary_carries_only_the_public_face_of_a_user() -> None:
    """Test that a user summary serves the public fields of a user and nothing else."""
    user = User(
        user_id="abc123",
        username="testuser",
        role=UserRole.ADMIN,
        display_name="Test User",
        avatar_url="avatar.png",
        preferences={"theme": "dark"},
    )
    assert UserSummary.from_user(user).to_dict() == {
        "user_id": "abc123",
        "username": "testuser",
        "display_name": "Test User",
        "avatar_url": "avatar.png",
    }


def test_role_round_trips_with_its_scopes() -> None:
    """Test that a role serializes its scopes by value and deserializes them back."""
    role = Role(role_id="abc123", name="Kids", scopes=[Scope.LIBRARY_READ, Scope.PLAYERS_READ])
    assert role.to_dict() == {
        "role_id": "abc123",
        "name": "Kids",
        "scopes": ["library.read", "players.read"],
        "builtin": False,
    }
    assert Role.from_dict(role.to_dict()) == role
