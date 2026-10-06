"""Tests for the SortOptionInfo API model."""

from music_assistant_models.api import SortOptionInfo
from music_assistant_models.enums import SortDirection, SortField


def test_sort_option_info_serialization_roundtrip_with_optional_fields() -> None:
    """Optional sort metadata survives serialization and deserialization."""
    option = SortOptionInfo(
        field=SortField.NAME,
        supports_direction=True,
        default_direction=SortDirection.ASC,
        label_key="sort.name",
    )

    data = option.to_dict()

    assert data == {
        "field": "name",
        "supports_direction": True,
        "default_direction": "asc",
        "label_key": "sort.name",
    }
    assert SortOptionInfo.from_dict(data) == option


def test_sort_option_info_serialization_roundtrip_with_none_defaults() -> None:
    """Optional sort metadata defaults to None and remains None after roundtrip."""
    option = SortOptionInfo(field=SortField.NAME, supports_direction=False)

    data = option.to_dict()

    assert data == {
        "field": "name",
        "supports_direction": False,
        "default_direction": None,
        "label_key": None,
    }
    assert SortOptionInfo.from_dict(data) == option
