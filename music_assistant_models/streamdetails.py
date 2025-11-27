"""Model(s) for streamdetails."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from mashumaro import DataClassDictMixin, field_options, pass_through

from .dsp import DSPDetails
from .enums import MediaType, StreamType, VolumeNormalizationMode
from .media_items import AudioFormat

type StreamMetadataUpdateCallback = Callable[[StreamDetails, int], Awaitable[None]]


@dataclass
class StreamMetadata(DataClassDictMixin):
    """
    Metadata of a live broadcast / media stream.

    This is used, for example, to provide information about the currently playing
    track on a radio station. A provider may use this to expose additional
    metadata about the stream.
    """

    # mandatory fields
    title: str

    # optional fields
    artist: str | None = None
    album: str | None = None
    image_url: str | None = None
    duration: int | None = None
    description: str | None = None
    uri: str | None = None
    elapsed_time: int | None = None
    elapsed_time_last_updated: float | None = None  # UTC timestamp

    @property
    def corrected_elapsed_time(self) -> float | None:
        """Return the corrected/realtime elapsed time (while playing)."""
        if self.elapsed_time is None or self.elapsed_time_last_updated is None:
            return None
        return self.elapsed_time + (time.time() - self.elapsed_time_last_updated)


@dataclass
class MultiPartPath:
    """
    Model for a multipart path.

    Used when a stream is split into multiple parts, e.g. chapters.
    """

    path: str
    # use the duration field to specify the duration of this part
    # for more efficient seeking
    duration: float | None = None


@dataclass(kw_only=True)
class StreamDetails(DataClassDictMixin):
    """Model for streamdetails."""

    # NOTE: the actual provider/itemid of the streamdetails may differ
    # from the connected media_item due to track linking etc.
    # the streamdetails are only used to provide details about the content
    # that is (going to be) streamed.

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

    # stream metadata: radio/live streams can optionally set/use this field
    # to set the metadata of the playing media during the stream
    stream_metadata: StreamMetadata | None = None

    #############################################################################
    # the fields below will only be used server-side and not sent to the client #
    #############################################################################

    # path: url or (local accessible) path to the stream (if not custom stream)
    # this field should be set by the provider when creating the streamdetails
    # unless the stream is a custom stream
    # if the stream consists of multiple parts, this may also be a list of MultiPartPath
    path: str | list[MultiPartPath] | None = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    # data: provider specific data (not exposed externally)
    # this info is for example used to pass along details to the get_audio_stream
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

    # expiration: time in seconds until the streamdetails expire
    expiration: int = field(
        default=600,  # 10 minutes
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )

    # stream metadata update callback
    # optional (async) callback that will be called to update the stream metadata
    # it will be passed the streamdetails object and the elapsed time in seconds
    stream_metadata_update_callback: StreamMetadataUpdateCallback | None = field(
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    # interval in seconds to call the stream metadata update callback
    stream_metadata_update_interval: int = field(
        default=5,  # 5 seconds
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
    buffer: Any = field(  # for in-memory buffering of stream data
        default=None,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    created_at: float = field(
        default_factory=time.time,
        compare=False,
        metadata=field_options(serialize="omit", deserialize=pass_through),
        repr=False,
    )
    stream_metadata_last_updated: float | None = field(
        default=None,
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

    @property
    def stream_title(self) -> str | None:
        """
        Return stream title representation of item.

        Provided for backwards compatibility reasons.
        """
        if self.stream_metadata:
            if self.stream_metadata.artist:
                return f"{self.stream_metadata.artist} - {self.stream_metadata.title}"
            return self.stream_metadata.title
        return None

    @stream_title.setter
    def stream_title(self, value: str) -> None:
        """Set stream title representation of item."""
        if " - " in value:
            artist, title = value.split(" - ", 1)
            self.stream_metadata = StreamMetadata(title=title, artist=artist)
        else:
            self.stream_metadata = StreamMetadata(title=value)

    def __post_serialize__(self, d: dict[Any, Any]) -> dict[Any, Any]:
        """Execute action(s) on serialization."""
        # add alias for stream_title for backwards compatibility
        d["stream_title"] = self.stream_title
        return d
