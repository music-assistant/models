"""Tests for the PlaylistMatchPolicy enum."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from mashumaro import DataClassDictMixin

from music_assistant_models.enums import PlaylistMatchPolicy


@dataclass
class _MatchPolicyHolder(DataClassDictMixin):
    """Minimal dataclass to exercise PlaylistMatchPolicy (de)serialization."""

    match_policy: PlaylistMatchPolicy


def test_values() -> None:
    """The wire values are fixed and must not change without a version bump."""
    assert PlaylistMatchPolicy.EXACT == "exact"
    assert PlaylistMatchPolicy.SAME_RECORDING == "same_recording"
    assert PlaylistMatchPolicy.BEST_EFFORT == "best_effort"


@pytest.mark.parametrize("policy", list(PlaylistMatchPolicy))
def test_roundtrip(policy: PlaylistMatchPolicy) -> None:
    """Each policy survives a model JSON roundtrip."""
    holder = _MatchPolicyHolder(match_policy=policy)
    restored = _MatchPolicyHolder.from_dict(holder.to_dict())
    assert restored.match_policy is policy


def test_deserialize_from_string() -> None:
    """A raw wire string deserializes to the matching enum member."""
    restored = _MatchPolicyHolder.from_dict({"match_policy": "same_recording"})
    assert restored.match_policy is PlaylistMatchPolicy.SAME_RECORDING


def test_unknown_value_is_rejected() -> None:
    """An unrecognized value is rejected rather than silently coerced."""
    with pytest.raises(ValueError, match="invalid value"):
        _MatchPolicyHolder.from_dict({"match_policy": "some_future_policy"})
