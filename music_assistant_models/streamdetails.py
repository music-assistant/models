"""Model(s) for streamdetails."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from mashumaro import DataClassDictMixin, field_options, pass_through

from .dsp import DSPDetails
from .enums import MediaType, StreamType, VolumeNormalizationMode
from .media_items import AudioFormat


@dataclass(kw_only=True)
class StreamDetails(DataClassDictMixin):
    """Model for streamdetails."""

    # NOTE: the actual provider/itemid of the streamdetails may differ
    # from the connected media_item due to track linking etc.
    # the streamdetails are only used to provide details about the content
    # that is going to be streamed.

    #############################################################################
    # mandatory fields                                                          #
    #############################################################################
    provider: str
    item_id: str
    audio_format: AudioFormat
    media_type: MediaType = MediaType.TRACK
    stream_type: StreamType = StreamType.CUSTOM

    #############################################################################
    # optional fields                                                           #
    #############################################################################

    # duration of the item to stream, copied from media_item if omitted
    duration: int | None = None

    # total size in bytes of the item, calculated at eof when omitted
    size: int | None = None

    # stream_title: radio/live streams can optionally set/use this field
    # to set the title of the playing media during the stream
    stream_title: str | None = None

    #############################################################################
    # the fields below will only be used server-side and not sent to the client #
    #############################################################################

    # path: url or (local accessible) path to the stream (if not custom stream)
    # this field should be set by the provider when creating the streamdetails
    # unless the stream is a custom stream
    path: str | None = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    # data: provider specific data (not exposed externally)
    # this info is for example used to pass slong details to the get_audio_stream
    # this field may be set by the provider when creating the streamdetails
    data: Any = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    # extra_input_args: any additional input args to pass along to ffmpeg
    # this field may be set by the provider when creating the streamdetails
    extra_input_args: list[str] = field(
        default_factory=list,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    # decryption_key: decryption key for encrypted streams (used with StreamType.ENCRYPTED_HTTP)
    # this field may be set by the provider when creating the streamdetails
    decryption_key: str | None = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    # allow_seek: bool to indicate that the content can/may be seeked
    # If set to False, seeking will be completely disabled.
    # NOTE: this is automatically disabled for duration-less streams (e/g. radio)
    allow_seek: bool = field(
        default=False,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )

    # can_seek: bool to indicate that the custom audio stream can be seeked
    # if set to False, and allow seek is set to True, the core logic will attempt
    # to seek in the incoming (bytes)stream, which is not a guarantee it will work.
    # If allow_seek is also set to False, seeking will be completely disabled.
    can_seek: bool = field(
        default=False,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )

    # enable_cache: bool to indicate that the audio be be temporary cached
    # this increases performance (especially while seeking) and reduces network
    # usage for streams that are played multiple times. For some (slow) streams
    # its even required to prevent buffering issues.
    # leave/set to None to let the core decide based on the stream type.
    # True to enforce caching, False to disable caching.
    enable_cache: bool | None = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )

    #############################################################################
    # the fields below will be set/controlled by the streamcontroller           #
    #############################################################################
    loudness: float | None = None
    loudness_album: float | None = None
    prefer_album_loudness: bool = False
    volume_normalization_mode: VolumeNormalizationMode | None = None
    volume_normalization_gain_correct: float | None = None
    target_loudness: float | None = None
    strip_silence_begin: bool = False
    strip_silence_end: bool = False

    # This contains the DSPDetails of all players in the group.
    # In case of single player playback, dict will contain only one entry.
    dsp: dict[str, DSPDetails] | None = None

    # the fields below are managed by the queue/stream controller and may not be set by providers
    fade_in: bool = field(
        default=False,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    seek_position: int = field(
        default=0,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    queue_id: str | None = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    seconds_streamed: float | None = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    stream_error: bool | None = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    cache: Any = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC),
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )

    def __str__(self) -> str:
        """Return pretty printable string of object."""
        return self.uri

    @property
    def uri(self) -> str:
        """Return uri representation of item."""
        return f"{self.provider}://{self.media_type.value}/{self.item_id}"

    def __post_serialize__(self, d: dict[Any, Any]) -> dict[Any, Any]:
        """Execute action(s) on serialization."""
        # TEMP 2025-02-28: convert StreamType.CACHE and StreamType.MULTI_FILE for
        # backwards compatibility with older client versions
        # Remove this in a future release (after 2.5 is released)
        d["stream_type"] = d["stream_type"].replace("cache", "local_file")
        d["stream_type"] = d["stream_type"].replace("multi_file", "local_file")
        return d
