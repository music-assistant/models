"""API helper classes for media items."""

from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin

from .media_item import Audiobook


@dataclass
class AudiobookCollection(DataClassDictMixin):
    """Model for an audiobook collection when gathered by the backend.

    A provider may add multiple MediaItemCollection entries to a book, making it part of one or
    multiple collections. The backend then searches the database for all books of an collection, and
    uses this model as a response in the API.

    This model is not to be used by a provider.
    """

    title: str
    # sorted list of audiobooks in this collection
    audiobooks: list[Audiobook] = field(default_factory=list)
