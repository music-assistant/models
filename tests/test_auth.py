"""Tests for the authentication models."""

import pytest

from music_assistant_models.auth import (
    AuthProviderType,
    Role,
    Scope,
    User,
    UserRole,
    UserSummary,
)


def test_user_role_validation() -> None:
    """Test that an unknown (builtin) user role raises on validation."""
    with pytest.raises(ValueError, match="some_future_role"):
        UserRole("some_future_role")
    assert UserRole("admin") == UserRole.ADMIN


def test_auth_provider_type_missing() -> None:
    """Test that an unknown auth provider type falls back to BUILTIN."""
    assert AuthProviderType("some_future_provider") == AuthProviderType.BUILTIN
    assert AuthProviderType("homeassistant") == AuthProviderType.HOME_ASSISTANT


def test_scope_missing() -> None:
    """Test that an unknown scope falls back to UNKNOWN (which grants no access)."""
    assert Scope("some.future.scope") == Scope.UNKNOWN
    assert Scope("library.read") == Scope.LIBRARY_READ


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
