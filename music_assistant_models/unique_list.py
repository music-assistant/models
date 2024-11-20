"""Representation of a custom List that ensures the items are unique."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

_T = TypeVar("_T")


class UniqueList(list[_T]):
    """Custom list that ensures the inserted items are unique."""

    def __init__(self, iterable: Iterable[_T] | None = None) -> None:
        """Initialize."""
        if not iterable:
            super().__init__()
            return
        seen: set[_T] = set()
        seen_add = seen.add
        super().__init__(x for x in iterable if not (x in seen or seen_add(x)))

    def append(self, item: _T) -> None:
        """Append item."""
        if item in self:
            return
        super().append(item)

    def extend(self, other: Iterable[_T]) -> None:
        """Extend list."""
        other = [x for x in other if x not in self]
        super().extend(other)

    def set(self, items: Iterable[_T]) -> None:
        """Set items in the list."""
        self.clear()
        self.extend(items)
