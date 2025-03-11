"""Model for AudioFormat details."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mashumaro import DataClassDictMixin

from music_assistant_models.enums import ContentType

MetadataTypes = int | bool | str | list[str]


@dataclass(kw_only=True)
class AudioFormat(DataClassDictMixin):
    """Model for AudioFormat details."""

    content_type: ContentType = ContentType.UNKNOWN
    codec_type: ContentType = ContentType.UNKNOWN
    sample_rate: int = 44100
    bit_depth: int = 16
    channels: int = 2
    output_format_str: str = ""
    bit_rate: int | None = None  # optional bitrate in kbps

    def __post_init__(self) -> None:
        """Execute actions after init."""
        if not self.output_format_str and self.content_type.is_pcm():
            self.output_format_str = (
                f"pcm;codec=pcm;rate={self.sample_rate};"
                f"bitrate={self.bit_depth};channels={self.channels}"
            )
        elif not self.output_format_str:
            self.output_format_str = self.content_type.value
        if self.bit_rate and self.bit_rate > 10000:
            # correct bit rate in bits per second to kbps
            self.bit_rate = int(self.bit_rate / 1000)

    @property
    def quality(self) -> int:
        """Calculate quality score."""
        if self.content_type.is_lossless():
            # lossless content is scored very high based on sample rate and bit depth
            return int(self.sample_rate / 1000) + self.bit_depth
        # lossy content, bit_rate is most important score
        # but prefer some codecs over others
        # calculate a rough score based on bit rate per channel
        bit_rate = self.bit_rate or 320
        bit_rate_score = (bit_rate / self.channels) / 100
        if self.content_type in (ContentType.AAC, ContentType.OGG):
            bit_rate_score += 1
        return int(bit_rate_score)

    @property
    def pcm_sample_size(self) -> int:
        """Return the PCM sample size."""
        return int(self.sample_rate * (self.bit_depth / 8) * self.channels)

    def __eq__(self, other: object) -> bool:
        """Check equality of two items."""
        if not isinstance(other, AudioFormat):
            return False
        return str(self) == str(other)

    def __str__(self) -> str:
        """Return string representation."""
        return (
            f"{self.output_format_str} {self.sample_rate}/{self.bit_depth} {self.channels} channels"
        )

    def __post_serialize__(self, d: dict[Any, Any]) -> dict[Any, Any]:
        """Execute action(s) on serialization."""
        # bit_rate is now optional. Set default value to keep compatibility
        # TODO: remove this after release of MA 2.5
        d["bit_rate"] = d["bit_rate"] or 0
        return d
