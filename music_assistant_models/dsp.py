"""All DSP (Digital Signal Processing) related models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

from mashumaro import DataClassDictMixin

# ruff: noqa: S105

class DSPFilterType(StrEnum):
    """Enum of all supported DSP Filter Types."""

    PARAMETRIC_EQ = "parametric_eq"

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


@dataclass
class ParametricEQFilter(DSPFilterBase):
    """Model for a Parametric EQ filter."""

    type: Literal[DSPFilterType.PARAMETRIC_EQ] = DSPFilterType.PARAMETRIC_EQ
    bands: list[ParametricEQBand] = field(default_factory=list)

    def validate(self) -> None:
        """Validate the Parametric EQ filter."""
        # Validate bands
        for band in self.bands:
            if not 0.0 < band.frequency <= 100000.0:
                raise ValueError("Band frequency must be in the range 0.0 to 100000.0 Hz")
            if not 0.01 <= band.q <= 100.0:
                raise ValueError("Band Q factor must be in the range 0.01 to 100.0")
            if not -60.0 <= band.gain <= 60.0:
                raise ValueError("Band gain must be in the range -60.0 to 60.0 dB")


# Type alias for all possible DSP filters
DSPFilter = ParametricEQFilter


@dataclass
class DSPConfig(DataClassDictMixin):
    """Model for a complete DSP configuration."""

    # Enable/disable the complete DSP configuration, including input/output stages
    enabled: bool = True
    # List of DSP filters that are applied in order
    filters: list[DSPFilter] = field(default_factory=list)
    # Input gain in dB, will be applied before any other DSP filters
    input_gain: float = 0.0
    # Output gain in dB, will be applied after all other DSP filters
    output_gain: float = 0.0
    # Enable/disable the default output limiter, will be applied after all other DSP effects
    # to prevent clipping
    output_limiter: bool = True

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
