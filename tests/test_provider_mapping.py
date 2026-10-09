"""Tests for the ProviderMapping model."""

import pytest

from music_assistant_models.media_items import ProviderMapping


def _mapping(provider_domain: str, in_library: bool | None = None) -> ProviderMapping:
    return ProviderMapping(
        item_id="1",
        provider_domain=provider_domain,
        provider_instance=f"{provider_domain}--a1",
        in_library=in_library,
    )


def test_local_files_get_the_highest_priority() -> None:
    """A Local files mapping scores two, and one more when it is in the library."""
    assert _mapping("filesystem_local").priority == 2
    assert _mapping("filesystem_local", in_library=True).priority == 3


@pytest.mark.parametrize("provider_domain", ["filesystem_smb", "filesystem_nfs"])
def test_only_local_files_are_preferred_by_domain(provider_domain: str) -> None:
    """Other filesystem domains get no bonus for their domain name."""
    assert _mapping(provider_domain).priority == 0
