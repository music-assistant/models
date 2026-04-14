"""API helper classes for media items."""

from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin

from .media_item import Audiobook


@dataclass
class AudiobookSeries(DataClassDictMixin):
    """An audiobook series as acquired from the database.

    This is used as API response, and not to be used by a provider.
    """

    title: str
    # sorted list of audiobooks in this series
    audiobooks: list[Audiobook] = field(default_factory=list)
