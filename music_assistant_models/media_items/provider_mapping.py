"""Models and helpers for MediaItem's provider mapping details."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast

from mashumaro import DataClassDictMixin

from music_assistant_models.helpers import get_global_cache_value

from .audio_format import AudioFormat


@dataclass(kw_only=True)
class ProviderMapping(DataClassDictMixin):
    """Model for a MediaItem's provider mapping details."""

    item_id: str
    provider_domain: str
    provider_instance: str
    available: bool = True
    # quality/audio details (streamable content only)
    audio_format: AudioFormat = field(default_factory=AudioFormat)
    # url = link to provider details page if exists
    url: str | None = None
    # optional details to store provider specific details
    details: str | None = None

    @property
    def quality(self) -> int:
        """Return quality score."""
        quality = self.audio_format.quality
        # append provider score so filebased providers are scored higher
        return quality + self.priority

    @property
    def priority(self) -> int:
        """Return priority score to sort local providers before online."""
        if not (local_provs := get_global_cache_value("non_streaming_providers")):
            # this is probably the client
            return 0
        if TYPE_CHECKING:
            local_provs = cast("set[str]", local_provs)
        if self.provider_domain in ("filesystem_local", "filesystem_smb"):
            return 2
        if self.provider_instance in local_provs:
            return 1
        return 0

    def __hash__(self) -> int:
        """Return custom hash."""
        return hash((self.provider_instance, self.item_id))

    def __eq__(self, other: object) -> bool:
        """Check equality of two items."""
        if not isinstance(other, ProviderMapping):
            return False
        return self.provider_instance == other.provider_instance and self.item_id == other.item_id
