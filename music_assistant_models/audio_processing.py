"""Models for effective audio processing details."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from mashumaro import DataClassDictMixin

from .dsp import AudioChannel, DSPFilter, DSPState
from .enums import CrossfadeMode, VolumeNormalizationMode
from .media_items import AudioFormat


class AudioQuality(StrEnum):
    """Quality classification for an audio stream."""

    UNKNOWN = "unknown"
    LOW = "low"
    STANDARD = "standard"
    LOSSLESS = "lossless"
    HI_RES = "hi_res"

    @classmethod
    def _missing_(cls, _: object) -> AudioQuality:
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN


class AudioNormalizationMeasurementSource(StrEnum):
    """Source used for a normalization loudness measurement."""

    UNKNOWN = "unknown"
    TRACK = "track"
    ALBUM = "album"
    LIVE = "live"
    FALLBACK = "fallback"

    @classmethod
    def _missing_(cls, _: object) -> AudioNormalizationMeasurementSource:
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN


@dataclass(kw_only=True)
class AudioFidelity(DataClassDictMixin):
    """Fidelity of an input or output audio stream."""

    quality: AudioQuality = AudioQuality.UNKNOWN
    # None when bit-perfect status cannot be determined.
    bit_perfect: bool | None = None


@dataclass(kw_only=True)
class AudioNormalizationDetails(DataClassDictMixin):
    """Effective volume normalization applied to queue audio."""

    mode: VolumeNormalizationMode = VolumeNormalizationMode.UNKNOWN
    measurement_source: AudioNormalizationMeasurementSource = (
        AudioNormalizationMeasurementSource.UNKNOWN
    )
    # Target loudness in LUFS.
    target_lufs: float | None = None
    # Measured source loudness in LUFS.
    measured_lufs: float | None = None
    # Gain applied during normalization in dB.
    applied_gain_db: float | None = None


@dataclass(kw_only=True)
class AudioQueueProcessing(DataClassDictMixin):
    """Effective processing shared before output fan-out."""

    # Internal PCM format shared by queue processing, including F32 headroom.
    pcm_format: AudioFormat | None = None
    normalization: AudioNormalizationDetails | None = None
    playback_speed: float = 1.0
    # DISABLED means no crossfade is active.
    crossfade_mode: CrossfadeMode = CrossfadeMode.DISABLED
    overlay_active: bool = False


@dataclass(kw_only=True)
class AudioDSPDetails(DataClassDictMixin):
    """Effective DSP applied to an output."""

    state: DSPState = DSPState.UNKNOWN
    # Input gain in dB.
    input_gain: float = 0.0
    filters: list[DSPFilter] = field(default_factory=list)
    # Output gain in dB.
    output_gain: float = 0.0
    output_limiter: bool = False


@dataclass(kw_only=True)
class AudioOutputDetails(DataClassDictMixin):
    """Effective processing for a group of output players."""

    player_ids: list[str] = field(default_factory=list)
    dsp: AudioDSPDetails = field(default_factory=AudioDSPDetails)
    # Set only for explicit left/right routing; formats show mono/stereo conversion.
    source_channel: AudioChannel | None = None
    # Furthest downstream format known to Music Assistant.
    output_format: AudioFormat | None = None
    fidelity: AudioFidelity = field(default_factory=AudioFidelity)


@dataclass(kw_only=True)
class AudioProcessingChain(DataClassDictMixin):
    """Effective audio processing for a stream."""

    # Input provider and audio format come from the containing StreamDetails.
    input_fidelity: AudioFidelity = field(default_factory=AudioFidelity)
    queue_processing: AudioQueueProcessing | None = None
    outputs: list[AudioOutputDetails] = field(default_factory=list)
