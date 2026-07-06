"""Tests for the authentication models."""

import pytest

from music_assistant_models.auth import (
    AuthProviderType,
    Scope,
    User,
    UserRole,
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


def test_user_with_unknown_role_deserializes() -> None:
    """Test that a User with an unknown role id deserializes with the role id preserved."""
    user = User.from_dict(
        {
            "user_id": "abc123",
            "username": "testuser",
            "role": "some_future_role",
        }
    )
    # the role id is preserved as-is, to allow for custom roles in the future
    assert user.role == "some_future_role"
