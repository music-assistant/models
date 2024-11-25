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
