"""Access records: who owns a shareable object and who else may use it."""

from __future__ import annotations

from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin

from .enums import ProviderSharing


@dataclass
class ProviderAccess(DataClassDictMixin):
    """Who a provider instance serves: its owner and the users it is shared with."""

    # owner: user_id of the member this instance belongs to; None = admin managed, and then
    # sharing alone decides who may use it
    owner: str | None = None
    # sharing: defaults to the most restrictive value; a household source is written as EVERYONE
    sharing: ProviderSharing = ProviderSharing.PRIVATE
    # shared_users: only consulted with ProviderSharing.SELECTED
    shared_users: list[str] = field(default_factory=list)


@dataclass
class PlaylistAccess(ProviderAccess):
    """Who a Music Assistant playlist serves: its owner, who may see it and who may edit it."""

    # collaborative: everyone the playlist is shared with may also add and remove its items;
    # otherwise only the owner may
    collaborative: bool = False
