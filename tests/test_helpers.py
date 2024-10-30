"""Tests for utility/helper functions."""

from music_assistant_models import helpers


def test_create_sort_name() -> None:
    """Test create_sort_name helper."""
    assert helpers.create_sort_name("The Beatles") == "beatles, the"
    assert helpers.create_sort_name("The Rolling Stones") == "rolling stones, the"
    assert helpers.create_sort_name("The Who") == "who, the"
    assert helpers.create_sort_name("De Radios") == "radios, de"
    assert helpers.create_sort_name("Las Ketchup") == "ketchup, las"
    assert helpers.create_sort_name("Los Lobos") == "lobos, los"
    assert helpers.create_sort_name("Le Tigre") == "tigre, le"
    assert helpers.create_sort_name("La Oreja de Van Gogh") == "oreja de van gogh, la"
    assert helpers.create_sort_name("El Canto del Loco") == "canto del loco, el"
    assert helpers.create_sort_name("A Perfect Circle") == "perfect circle, a"


def test_is_valid_uuid() -> None:
    """Test is_valid_uuid helper."""
    assert helpers.is_valid_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d479")
    assert not helpers.is_valid_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d4791")
    assert not helpers.is_valid_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d47")
    assert not helpers.is_valid_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d47z")
    assert not helpers.is_valid_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d47z")
    assert not helpers.is_valid_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d47z")
    assert not helpers.is_valid_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d47z")
    assert not helpers.is_valid_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d47z")
    assert not helpers.is_valid_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d47z")
    assert not helpers.is_valid_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d47z")
    assert not helpers.is_valid_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d47z")
    assert not helpers.is_valid_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d47z")
    assert not helpers.is_valid_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d47z")
    assert not helpers.is_valid_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d47z")
    assert not helpers.is_valid_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d47z")
