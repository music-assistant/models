"""Models for runtime audio processing details."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from mashumaro import DataClassDictMixin

from .dsp import DSPFilter, DSPState
from .enums import CrossfadeMode, VolumeNormalizationMode
from .media_items import AudioFormat, ItemMapping


class AudioProcessingState(StrEnum):
    """State of an audio processing snapshot."""

    PENDING = "pending"
    READY = "ready"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, _: object) -> AudioProcessingState:
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN


class AudioQuality(StrEnum):
    """Effective audio quality classification."""

    LOW = "low"
    STANDARD = "standard"
    LOSSLESS = "lossless"
    HI_RES = "hi_res"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, _: object) -> AudioQuality:
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN


class AudioNormalizationMeasurementSource(StrEnum):
    """Source of the loudness measurement used for normalization."""

    TRACK = "track"
    ALBUM = "album"
    LIVE = "live"
    FALLBACK = "fallback"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, _: object) -> AudioNormalizationMeasurementSource:
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN


class AudioCrossfadeState(StrEnum):
    """Runtime state of a crossfade."""

    PENDING = "pending"
    APPLIED = "applied"
    BYPASSED = "bypassed"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, _: object) -> AudioCrossfadeState:
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN


class AudioChannelMode(StrEnum):
    """Effective output channel routing mode."""

    STEREO = "stereo"
    MONO = "mono"
    LEFT = "left"
    RIGHT = "right"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, _: object) -> AudioChannelMode:
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN


class AudioResamplingMethod(StrEnum):
    """Method used to resample an output path."""

    SOXR = "soxr"
    SWR = "swr"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, _: object) -> AudioResamplingMethod:
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN


class AudioDitheringMethod(StrEnum):
    """Method used to dither an output path."""

    TRIANGULAR_HP = "triangular_hp"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, _: object) -> AudioDitheringMethod:
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN


@dataclass(kw_only=True)
class AudioFidelity(DataClassDictMixin):
    """Effective fidelity at an input or final output."""

    quality: AudioQuality = AudioQuality.UNKNOWN
    bit_perfect: bool | None = None


@dataclass(kw_only=True)
class AudioFidelitySummary(DataClassDictMixin):
    """Minimum and maximum quality across all output paths."""

    min_output_quality: AudioQuality = AudioQuality.UNKNOWN
    max_output_quality: AudioQuality = AudioQuality.UNKNOWN


@dataclass(kw_only=True)
class AudioInputDetails(DataClassDictMixin):
    """Source and server-received formats for an audio input."""

    source_format: AudioFormat | None = None
    server_input_format: AudioFormat | None = None
    fidelity: AudioFidelity = field(default_factory=AudioFidelity)


@dataclass(kw_only=True)
class AudioNormalizationDetails(DataClassDictMixin):
    """Effective volume normalization details.

    ``reason_code`` is a machine-readable identifier, not presentation text.
    """

    mode: VolumeNormalizationMode = VolumeNormalizationMode.UNKNOWN
    measurement_source: AudioNormalizationMeasurementSource = (
        AudioNormalizationMeasurementSource.UNKNOWN
    )
    target_lufs: float | None = None
    measured_lufs: float | None = None
    applied_gain_db: float | None = None
    target_true_peak_dbtp: float | None = None
    target_loudness_range_lu: float | None = None
    reason_code: str | None = None


@dataclass(kw_only=True)
class AudioTempoDetails(DataClassDictMixin):
    """Active playback-speed processing details."""

    playback_speed: float = 1.0


@dataclass(kw_only=True)
class AudioCrossfadeDetails(DataClassDictMixin):
    """Effective crossfade details and runtime result.

    ``reason_code`` is a machine-readable identifier, not presentation text.
    """

    mode: CrossfadeMode = CrossfadeMode.UNKNOWN
    state: AudioCrossfadeState = AudioCrossfadeState.UNKNOWN
    from_queue_item_id: str | None = None
    to_queue_item_id: str | None = None
    planned_duration: float | None = None
    actual_duration: float | None = None
    reason_code: str | None = None


@dataclass(kw_only=True)
class AudioOverlayDetails(DataClassDictMixin):
    """Effective audio overlay source and volume."""

    source: ItemMapping | None = None
    volume_percent: int = 100


@dataclass(kw_only=True)
class AudioQueueProcessing(DataClassDictMixin):
    """Shared queue processing before output fan-out."""

    input_format: AudioFormat | None = None
    output_format: AudioFormat | None = None
    normalization: AudioNormalizationDetails | None = None
    tempo: AudioTempoDetails | None = None
    crossfade: AudioCrossfadeDetails | None = None
    overlay: AudioOverlayDetails | None = None


@dataclass(kw_only=True)
class AudioDSPDetails(DataClassDictMixin):
    """Effective user DSP applied to an output path."""

    state: DSPState = DSPState.UNKNOWN
    input_gain: float = 0.0
    filters: list[DSPFilter] = field(default_factory=list)
    output_gain: float = 0.0


@dataclass(kw_only=True)
class AudioChannelDetails(DataClassDictMixin):
    """Effective channel routing or conversion details."""

    mode: AudioChannelMode = AudioChannelMode.UNKNOWN


@dataclass(kw_only=True)
class AudioLimiterDetails(DataClassDictMixin):
    """Output limiter state and threshold in dBFS."""

    enabled: bool = False
    threshold_dbfs: float | None = None


@dataclass(kw_only=True)
class AudioResamplingDetails(DataClassDictMixin):
    """Effective output resampling details."""

    method: AudioResamplingMethod = AudioResamplingMethod.UNKNOWN


@dataclass(kw_only=True)
class AudioDitheringDetails(DataClassDictMixin):
    """Effective output dithering details."""

    method: AudioDitheringMethod = AudioDitheringMethod.UNKNOWN


@dataclass(kw_only=True)
class AudioOutputPath(DataClassDictMixin):
    """Processing shared by a deterministic group of output players.

    ``output_format`` is the furthest downstream format known to Music Assistant.
    ``handoff_format`` is set only when an earlier provider handoff differs.
    """

    player_ids: list[str] = field(default_factory=list)
    input_format: AudioFormat | None = None
    dsp: AudioDSPDetails = field(default_factory=AudioDSPDetails)
    channels: AudioChannelDetails | None = None
    limiter: AudioLimiterDetails = field(default_factory=AudioLimiterDetails)
    resampling: AudioResamplingDetails | None = None
    dithering: AudioDitheringDetails | None = None
    output_format: AudioFormat | None = None
    handoff_format: AudioFormat | None = None
    fidelity: AudioFidelity = field(default_factory=AudioFidelity)


@dataclass(kw_only=True)
class AudioProcessingChain(DataClassDictMixin):
    """Full runtime audio processing snapshot for a queue."""

    queue_id: str = ""
    queue_item_id: str | None = None
    revision: int = 0
    state: AudioProcessingState = AudioProcessingState.UNKNOWN
    input: AudioInputDetails | None = None
    queue_processing: AudioQueueProcessing | None = None
    outputs: list[AudioOutputPath] = field(default_factory=list)
    fidelity: AudioFidelitySummary | None = None
