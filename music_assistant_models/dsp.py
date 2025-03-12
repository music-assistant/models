"""All DSP (Digital Signal Processing) related models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

from mashumaro import DataClassDictMixin

from .media_items.audio_format import AudioFormat

# ruff: noqa: S105


class AudioChannel(StrEnum):
    """Enum of all channel targets for DSP filters."""

    ALL = "ALL"
    FL = "FL"
    FR = "FR"

    @classmethod
    def _missing_(cls, _: object) -> AudioChannel:
        """Set default enum member if an unknown value is provided."""
        return cls.ALL


class DSPFilterType(StrEnum):
    """Enum of all supported DSP Filter Types."""

    PARAMETRIC_EQ = "parametric_eq"
    TONE_CONTROL = "tone_control"


@dataclass
class DSPFilterBase(DataClassDictMixin):
    """Base model for all DSP filters."""

    # Enable/disable this filter
    enabled: bool

    def validate(self) -> None:
        """Validate the DSP filter."""


class ParametricEQBandType(StrEnum):
    """Enum for Parametric EQ band types."""

    PEAK = "peak"
    HIGH_SHELF = "high_shelf"
    LOW_SHELF = "low_shelf"
    HIGH_PASS = "high_pass"
    LOW_PASS = "low_pass"
    NOTCH = "notch"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, _: object) -> ParametricEQBandType:
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN


@dataclass
class ParametricEQBand(DataClassDictMixin):
    """Model for a single Parametric EQ band."""

    # Center frequency of the band in Hz
    frequency: float = 1000.0
    # Q factor, changes the bandwidth of the band
    q: float = 1.0
    # Gain in dB, can be negative or positive
    gain: float = 0.0
    # Equalizer band type, changes the behavior of the band
    type: ParametricEQBandType = ParametricEQBandType.PEAK
    # Enable/disable the band
    enabled: bool = True
    # Channel to apply the band to
    channel: AudioChannel = AudioChannel.ALL


@dataclass
class ParametricEQFilter(DSPFilterBase):
    """Model for a Parametric EQ filter."""

    preamp: float | None = 0.0
    # Additional per-channel preamp values, they are less efficient than the global preamp setting,
    # but are required for some use cases
    # AudioChannel.ALL is not allowed here, use the global preamp setting instead
    per_channel_preamp: dict[AudioChannel, float] = field(default_factory=dict)
    type: Literal[DSPFilterType.PARAMETRIC_EQ] = DSPFilterType.PARAMETRIC_EQ
    bands: list[ParametricEQBand] = field(default_factory=list)

    def validate(self) -> None:
        """Validate the Parametric EQ filter."""
        if self.preamp and (not -60.0 <= self.preamp <= 60.0):
            raise ValueError("Preamp must be in the range -60.0 to 60.0 dB")
        if AudioChannel.ALL in self.per_channel_preamp:
            raise ValueError("AudioChannel.ALL is not allowed in per_channel_preamp")
        for gain in self.per_channel_preamp.values():
            if not -60.0 <= gain <= 60.0:
                raise ValueError("Preamp must be in the range -60.0 to 60.0 dB")
        # Validate bands
        for band in self.bands:
            if not 0.0 < band.frequency <= 100000.0:
                raise ValueError("Band frequency must be in the range 0.0 to 100000.0 Hz")
            if not 0.01 <= band.q <= 100.0:
                raise ValueError("Band Q factor must be in the range 0.01 to 100.0")
            if not -60.0 <= band.gain <= 60.0:
                raise ValueError("Band gain must be in the range -60.0 to 60.0 dB")


@dataclass
class ToneControlFilter(DSPFilterBase):
    """Model for a Tone Control filter."""

    type: Literal[DSPFilterType.TONE_CONTROL] = DSPFilterType.TONE_CONTROL
    # Bass level in dB, can be negative or positive
    bass_level: float = 0.0
    # Mid level in dB, can be negative or positive
    mid_level: float = 0.0
    # Treble level in dB, can be negative or positive
    treble_level: float = 0.0

    def validate(self) -> None:
        """Validate the Tone Control filter."""
        # Validate bass level
        if not -60.0 <= self.bass_level <= 60.0:
            raise ValueError("Bass level must be in the range -60.0 to 60.0 dB")
        # Validate mid level
        if not -60.0 <= self.mid_level <= 60.0:
            raise ValueError("Mid level must be in the range -60.0 to 60.0 dB")
        # Validate treble level
        if not -60.0 <= self.treble_level <= 60.0:
            raise ValueError("Treble level must be in the range -60.0 to 60.0 dB")


# Type alias for all possible DSP filters
DSPFilter = ParametricEQFilter | ToneControlFilter


@dataclass
class DSPConfig(DataClassDictMixin):
    """Model for a complete DSP configuration."""

    # Enable/disable the complete DSP configuration, including input/output stages
    enabled: bool = False
    # List of DSP filters that are applied in order
    filters: list[DSPFilter] = field(default_factory=list)
    # Input gain in dB, will be applied before any other DSP filters
    input_gain: float = 0.0
    # Output gain in dB, will be applied after all other DSP filters
    output_gain: float = 0.0

    def validate(self) -> None:
        """Validate the DSP configuration."""
        # Validate input gain
        if not -60.0 <= self.input_gain <= 60.0:
            raise ValueError("Input gain must be in the range -60.0 to 60.0 dB")
        # Validate output gain
        if not -60.0 <= self.output_gain <= 60.0:
            raise ValueError("Output gain must be in the range -60.0 to 60.0 dB")
        # Validate filters
        for f in self.filters:
            f.validate()


class DSPState(StrEnum):
    """Enum of all DSP states of DSPDetails."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    DISABLED_BY_UNSUPPORTED_GROUP = "disabled_by_unsupported_group"


@dataclass(kw_only=True)
class DSPDetails(DataClassDictMixin):
    """Model for information about a DSP applied to a stream.

    This describes the DSP configuration as applied,
    even when the DSP state is disabled. For example,
    output_limiter can remain true while the DSP is disabled.
    All filters in the list are guaranteed to be enabled.
    output_format is the format that will be sent to the output device (if known).
    """

    state: DSPState = DSPState.DISABLED
    input_gain: float = 0.0
    filters: list[DSPFilter] = field(default_factory=list)
    output_gain: float = 0.0
    output_limiter: bool = True
    output_format: AudioFormat | None = None
