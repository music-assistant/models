"""Tests for the names each module exports through __all__."""

import importlib
import pkgutil

import pytest

import music_assistant_models

MODULE_NAMES = [
    music_assistant_models.__name__,
    *(
        info.name
        for info in pkgutil.walk_packages(
            music_assistant_models.__path__, prefix=f"{music_assistant_models.__name__}."
        )
    ),
]


@pytest.mark.parametrize("module_name", MODULE_NAMES)
def test_all_only_lists_defined_names(module_name: str) -> None:
    """Every name in a module's __all__ exists, so a star import of the module works."""
    module = importlib.import_module(module_name)
    missing = [name for name in getattr(module, "__all__", []) if not hasattr(module, name)]
    assert not missing
