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


def test_create_safe_string() -> None:
    """Test create_safe_string helper."""
    # accented latin transliterates to plain ascii
    assert helpers.create_safe_string("Café") == "cafe"
    assert helpers.create_safe_string("Björk") == "bjork"
    assert helpers.create_safe_string("Mötley Crüe") == "motley crue"
    # special-cased artist names bypass general transliteration
    assert helpers.create_safe_string("P!nk") == "pink"
    assert helpers.create_safe_string("Wh♂") == "who"
    assert helpers.create_safe_string("KoЯn") == "korn"
    assert helpers.create_safe_string("$hort") == "short"
    # non-latin scripts must transliterate, not disappear
    assert helpers.create_safe_string("Кино") == "kino"
    assert helpers.create_safe_string("방탄소년단") == "bangtansonyeondan"
    # symbols that transliterate to uppercase are lowered
    assert helpers.create_safe_string("Track™") == "tracktm"
    # emoji transliterate to their name
    assert helpers.create_safe_string("DJ 🔥 Snake") == "dj fire snake"
    # spaces are kept by default, stripped with replace_space=True
    assert helpers.create_safe_string("The Beatles") == "the beatles"
    assert helpers.create_safe_string("The Beatles", replace_space=True) == "thebeatles"
    # lowercase can be disabled
    assert helpers.create_safe_string("Café", lowercase=False) == "Cafe"


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
