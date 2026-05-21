"""Models for audio analysis results and coverage reporting."""

from __future__ import annotations

from dataclasses import dataclass

from mashumaro import DataClassDictMixin


@dataclass(kw_only=True)
class AudioAnalysisCoverage(DataClassDictMixin):
    """Coverage / health counts for an audio analysis provider's analyzed library.

    Returned by the server's ``audio_analysis/coverage`` API command. ``analyzed``
    is the count of unique tracks the provider has stored analysis data for;
    ``pending`` is the count of candidate tracks awaiting analysis;
    ``stale_version`` is the count of stored rows whose ``analysis_version`` is
    older than the provider's current version; ``analysis_version`` is the
    provider's current schema version.
    """

    analyzed: int
    pending: int
    stale_version: int
    analysis_version: int
