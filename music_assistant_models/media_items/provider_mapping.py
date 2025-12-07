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
    # in_library: whether the item is in the user's library within this provider
    # if this is unknown in the current state, this shall be None
    in_library: bool | None = None
    # is_unique: whether this mapping is unique on this provider_instance.
    # setting this to True will prevent mapping additional providerinstances
    # for example, a user-unique upload or playlist that is not globally available
    # can safely be left as None to accept the default behavior based on
    # the 'is_streaming_provider' property of the provider
    is_unique: bool | None = None
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
        # append priority score so filebased providers are scored higher
        return quality + self.priority

    @property
    def priority(self) -> int:
        """Return priority score to sort local providers before online."""
        # prefer in_library items for better instance-steering
        base_score = 1 if self.in_library else 0
        # prefer local file based providers
        if self.provider_domain in ("filesystem_local", "filesystem_smb"):
            return base_score + 2
        if not (local_provs := get_global_cache_value("non_streaming_providers")):
            # this is probably the client
            return base_score
        if TYPE_CHECKING:
            local_provs = cast("set[str]", local_provs)
        if self.provider_instance in local_provs:
            return base_score + 1
        return base_score

    def __hash__(self) -> int:
        """Return custom hash."""
        return hash((self.provider_instance, self.item_id))

    def __eq__(self, other: object) -> bool:
        """Check equality of two items."""
        if not isinstance(other, ProviderMapping):
            return False
        return self.provider_instance == other.provider_instance and self.item_id == other.item_id
