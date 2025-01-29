"""All enums used by the Music Assistant models."""

from __future__ import annotations

import contextlib
from enum import EnumType, IntEnum, StrEnum


class MediaTypeMeta(EnumType):
    """Class properties for MediaType."""

    @property
    def ALL(cls) -> list[MediaType]:  # noqa: N802
        """All MediaTypes."""
        return [
            MediaType.ARTIST,
            MediaType.ALBUM,
            MediaType.TRACK,
            MediaType.PLAYLIST,
            MediaType.RADIO,
            MediaType.AUDIOBOOK,
            MediaType.PODCAST,
        ]


class MediaType(StrEnum, metaclass=MediaTypeMeta):
    """Enum for MediaType."""

    ARTIST = "artist"
    ALBUM = "album"
    TRACK = "track"
    PLAYLIST = "playlist"
    RADIO = "radio"
    AUDIOBOOK = "audiobook"
    PODCAST = "podcast"
    PODCAST_EPISODE = "podcast_episode"
    FOLDER = "folder"
    ANNOUNCEMENT = "announcement"
    FLOW_STREAM = "flow_stream"
    PLUGIN_SOURCE = "plugin_source"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> MediaType:  # noqa: ARG003
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN


class ExternalID(StrEnum):
    """Enum with External ID types."""

    MB_ARTIST = "musicbrainz_artistid"  # MusicBrainz Artist ID (or AlbumArtist ID)
    MB_ALBUM = "musicbrainz_albumid"  # MusicBrainz Album ID
    MB_RELEASEGROUP = "musicbrainz_releasegroupid"  # MusicBrainz ReleaseGroupID
    MB_TRACK = "musicbrainz_trackid"  # MusicBrainz Track ID
    MB_RECORDING = "musicbrainz_recordingid"  # MusicBrainz Recording ID

    ISRC = "isrc"  # used to identify unique recordings
    BARCODE = "barcode"  # EAN-13 barcode for identifying albums
    ACOUSTID = "acoustid"  # unique fingerprint (id) for a recording
    ASIN = "asin"  # amazon unique number to identify albums
    DISCOGS = "discogs"  # id for media item on discogs
    TADB = "tadb"  # the audio db id
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> ExternalID:  # noqa: ARG003
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN

    @property
    def is_unique(self) -> bool:
        """Return if the ExternalID is unique."""
        return self.is_musicbrainz or self in (
            ExternalID.ACOUSTID,
            ExternalID.DISCOGS,
            ExternalID.TADB,
        )

    @property
    def is_musicbrainz(self) -> bool:
        """Return if the ExternalID is a MusicBrainz identifier."""
        return self in (
            ExternalID.MB_RELEASEGROUP,
            ExternalID.MB_ALBUM,
            ExternalID.MB_TRACK,
            ExternalID.MB_ARTIST,
            ExternalID.MB_RECORDING,
        )


class LinkType(StrEnum):
    """Enum with link types."""

    WEBSITE = "website"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    LASTFM = "lastfm"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    SNAPCHAT = "snapchat"
    TIKTOK = "tiktok"
    DISCOGS = "discogs"
    WIKIPEDIA = "wikipedia"
    ALLMUSIC = "allmusic"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> LinkType:  # noqa: ARG003
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN


class ImageType(StrEnum):
    """Enum with image types."""

    THUMB = "thumb"
    LANDSCAPE = "landscape"
    FANART = "fanart"
    LOGO = "logo"
    CLEARART = "clearart"
    BANNER = "banner"
    CUTOUT = "cutout"
    BACK = "back"
    DISCART = "discart"
    OTHER = "other"

    @classmethod
    def _missing_(cls, value: object) -> ImageType:  # noqa: ARG003
        """Set default enum member if an unknown value is provided."""
        return cls.OTHER


class AlbumType(StrEnum):
    """Enum for Album type."""

    ALBUM = "album"
    SINGLE = "single"
    COMPILATION = "compilation"
    EP = "ep"
    UNKNOWN = "unknown"


class ContentType(StrEnum):
    """Enum with audio content/container types supported by ffmpeg."""

    # --- Containers ---
    OGG = "ogg"  # Ogg container (Vorbis/Opus/FLAC)
    WAV = "wav"  # WAV container (usually PCM)
    AIFF = "aiff"  # AIFF container
    MPEG = "mpeg"  # MPEG-PS/MPEG-TS container
    M4A = "m4a"  # MPEG-4 Audio (AAC/ALAC)
    MP4 = "mp4"  # MPEG-4 container
    M4B = "m4b"  # MPEG-4 Audiobook
    DSF = "dsf"  # DSD Stream File

    # --- Can both be a container and codec ---
    FLAC = "flac"  # FLAC lossless audio
    MP3 = "mp3"  # MPEG-1 Audio Layer III
    WMA = "wma"  # Windows Media Audio
    WMAV2 = "wmav2"  # Windows Media Audio v2
    WMAPRO = "wmapro"  # Windows Media Audio Professional
    WAVPACK = "wavpack"  # WavPack lossless
    TAK = "tak"  # Tom's Lossless Audio Kompressor
    APE = "ape"  # Monkey's Audio
    MUSEPACK = "mpc"  # MusePack

    # --- Codecs ---
    AAC = "aac"  # Advanced Audio Coding
    ALAC = "alac"  # Apple Lossless Audio Codec
    OPUS = "opus"  # Opus audio codec
    VORBIS = "vorbis"  # Ogg Vorbis compression
    AC3 = "ac3"  # Dolby Digital (common in DVDs)
    EAC3 = "eac3"  # Dolby Digital Plus (streaming/4K)
    DTS = "dts"  # Digital Theater System
    TRUEHD = "truehd"  # Dolby TrueHD (lossless)
    DTSHD = "dtshd"  # DTS-HD Master Audio
    DTSX = "dtsx"  # DTS:X immersive audio
    COOK = "cook"  # RealAudio Cook Codec
    RA_144 = "ralf"  # RealAudio Lossless
    MP2 = "mp2"  # MPEG-1 Audio Layer II
    MP1 = "mp1"  # MPEG-1 Audio Layer I
    DRA = "dra"  # Chinese Digital Rise Audio
    ATRAC3 = "atrac3"  # Sony MiniDisc format

    # --- PCM Codecs ---
    PCM_S16LE = "s16le"  # PCM 16-bit little-endian
    PCM_S24LE = "s24le"  # PCM 24-bit little-endian
    PCM_S32LE = "s32le"  # PCM 32-bit little-endian
    PCM_F32LE = "f32le"  # PCM 32-bit float
    PCM_F64LE = "f64le"  # PCM 64-bit float
    PCM_S16BE = "s16be"  # PCM 16-bit big-endian
    PCM_S24BE = "s24be"  # PCM 24-bit big-endian
    PCM_S32BE = "s32be"  # PCM 32-bit big-endian
    PCM_BLURAY = "pcm_bluray"  # Blu-ray specific PCM
    PCM_DVD = "pcm_dvd"  # DVD specific PCM

    # --- ADPCM Codecs ---
    ADPCM_IMA = "adpcm_ima_qt"  # QuickTime variant
    ADPCM_MS = "adpcm_ms"  # Microsoft variant
    ADPCM_SWF = "adpcm_swf"  # Flash audio

    # --- PDM Codecs ---
    DSD_LSBF = "dsd_lsbf"  # DSD least-significant-bit first
    DSD_MSBF = "dsd_msbf"  # DSD most-significant-bit first
    DSD_LSBF_PLANAR = "dsd_lsbf_planar"  # DSD planar least-significant-bit first
    DSD_MSBF_PLANAR = "dsd_msbf_planar"  # DSD planar most-significant-bit first

    # --- Voice Codecs ---
    AMR = "amr_nb"  # Adaptive Multi-Rate Narrowband, voice codec
    AMR_WB = "amr_wb"  # Adaptive Multi-Rate Wideband, voice codec
    SPEEX = "speex"  # Open-source voice codec, voice codec
    PCM_ALAW = "alaw"  # G.711 A-law, voice codec
    PCM_MULAW = "mulaw"  # G.711 µ-law, voice codec
    G722 = "g722"  # ITU-T 7 kHz audio
    G726 = "g726"  # ADPCM telephone quality

    # --- Special ---
    PCM = "pcm"  # PCM generic (details determined later)
    UNKNOWN = "?"  # Unknown type

    @classmethod
    def _missing_(cls, value: object) -> ContentType:  # noqa: ARG003
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN

    @classmethod
    def try_parse(cls, string: str) -> ContentType:
        """Try to parse ContentType from (url)string/extension."""
        tempstr = string.lower()
        if "audio/" in tempstr:
            tempstr = tempstr.split("/")[1]
        for splitter in (".", ","):
            if splitter in tempstr:
                for val in tempstr.split(splitter):
                    with contextlib.suppress(ValueError):
                        parsed = cls(val.strip())
                    if parsed != ContentType.UNKNOWN:
                        return parsed
        tempstr = tempstr.split("?")[0]
        tempstr = tempstr.split("&")[0]
        tempstr = tempstr.split(";")[0]
        tempstr = tempstr.replace("mp4", "m4a")
        tempstr = tempstr.replace("mp4a", "m4a")
        tempstr = tempstr.replace("wv", "wavpack")
        tempstr = tempstr.replace("pcm_", "")
        try:
            return cls(tempstr)
        except ValueError:
            return cls.UNKNOWN

    def is_pcm(self) -> bool:
        """Return if contentype is PCM."""
        return self.name.startswith("PCM")

    def is_lossless(self) -> bool:
        """Return if format is lossless."""
        return self.is_pcm() or self in (
            ContentType.DSF,
            ContentType.FLAC,
            ContentType.AIFF,
            ContentType.WAV,
            ContentType.ALAC,
            ContentType.WAVPACK,
            ContentType.TAK,
            ContentType.APE,
            ContentType.TRUEHD,
            ContentType.DSD_LSBF,
            ContentType.DSD_MSBF,
            ContentType.DSD_LSBF_PLANAR,
            ContentType.DSD_MSBF_PLANAR,
            ContentType.RA_144,
        )

    @classmethod
    def from_bit_depth(cls, bit_depth: int, floating_point: bool = False) -> ContentType:
        """Return (PCM) Contenttype from PCM bit depth."""
        if floating_point and bit_depth > 32:
            return cls.PCM_F64LE
        if floating_point:
            return cls.PCM_F32LE
        if bit_depth == 16:
            return cls.PCM_S16LE
        if bit_depth == 24:
            return cls.PCM_S24LE
        return cls.PCM_S32LE


class QueueOption(StrEnum):
    """Enum representation of the queue (play) options.

    - PLAY -> Insert new item(s) in queue at the current position and start playing.
    - REPLACE -> Replace entire queue contents with the new items and start playing from index 0.
    - NEXT -> Insert item(s) after current playing/buffered item.
    - REPLACE_NEXT -> Replace item(s) after current playing/buffered item.
    - ADD -> Add new item(s) to the queue (at the end if shuffle is not enabled).
    """

    PLAY = "play"
    REPLACE = "replace"
    NEXT = "next"
    REPLACE_NEXT = "replace_next"
    ADD = "add"


class RepeatMode(StrEnum):
    """Enum with repeat modes."""

    OFF = "off"  # no repeat at all
    ONE = "one"  # repeat one/single track
    ALL = "all"  # repeat entire queue


class PlayerState(StrEnum):
    """Enum for the (playback)state of a player."""

    IDLE = "idle"
    PAUSED = "paused"
    PLAYING = "playing"


class PlayerType(StrEnum):
    """Enum with possible Player Types.

    player: A regular player.
    stereo_pair: Same as player but a dedicated stereo pair of 2 speakers.
    group: A (dedicated) (sync)group player or (universal) playergroup.
    """

    PLAYER = "player"
    STEREO_PAIR = "stereo_pair"
    GROUP = "group"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> PlayerType:  # noqa: ARG003
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN


class PlayerFeature(StrEnum):
    """Enum with possible Player features.

    power: The player has a native/dedicated power control.
    volume: The player supports adjusting the volume.
    mute: The player supports muting the volume.
    set_members: The player supports grouping with other players.
    multi_device_dsp: The player supports per-device DSP when grouped.
    accurate_time: The player provides millisecond accurate timing information.
    seek: The player supports seeking to a specific.
    enqueue: The player supports (en)queuing of media items natively.
    select_source: The player has native support for selecting a source.
    """

    POWER = "power"
    VOLUME_SET = "volume_set"
    VOLUME_MUTE = "volume_mute"
    PAUSE = "pause"
    SET_MEMBERS = "set_members"
    MULTI_DEVICE_DSP = "multi_device_dsp"
    SEEK = "seek"
    NEXT_PREVIOUS = "next_previous"
    PLAY_ANNOUNCEMENT = "play_announcement"
    ENQUEUE = "enqueue"
    SELECT_SOURCE = "select_source"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> PlayerFeature:
        """Set default enum member if an unknown value is provided."""
        if value == "sync":
            # sync is deprecated, use set_members instead
            return cls.SET_MEMBERS
        return cls.UNKNOWN


class EventType(StrEnum):
    """Enum with possible Events."""

    PLAYER_ADDED = "player_added"
    PLAYER_UPDATED = "player_updated"
    PLAYER_REMOVED = "player_removed"
    PLAYER_SETTINGS_UPDATED = "player_settings_updated"
    QUEUE_ADDED = "queue_added"
    QUEUE_UPDATED = "queue_updated"
    QUEUE_ITEMS_UPDATED = "queue_items_updated"
    QUEUE_TIME_UPDATED = "queue_time_updated"
    MEDIA_ITEM_PLAYED = "media_item_played"
    SHUTDOWN = "application_shutdown"
    MEDIA_ITEM_ADDED = "media_item_added"
    MEDIA_ITEM_UPDATED = "media_item_updated"
    MEDIA_ITEM_DELETED = "media_item_deleted"
    PROVIDERS_UPDATED = "providers_updated"
    PLAYER_CONFIG_UPDATED = "player_config_updated"
    SYNC_TASKS_UPDATED = "sync_tasks_updated"
    AUTH_SESSION = "auth_session"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> EventType:  # noqa: ARG003
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN


class ProviderFeature(StrEnum):
    """Enum with features for a Provider."""

    #
    # MUSICPROVIDER FEATURES
    #

    # browse/explore/recommendations
    BROWSE = "browse"
    SEARCH = "search"
    RECOMMENDATIONS = "recommendations"

    # library feature per mediatype
    LIBRARY_ARTISTS = "library_artists"
    LIBRARY_ALBUMS = "library_albums"
    LIBRARY_TRACKS = "library_tracks"
    LIBRARY_PLAYLISTS = "library_playlists"
    LIBRARY_RADIOS = "library_radios"
    LIBRARY_AUDIOBOOKS = "library_audiobooks"
    LIBRARY_PODCASTS = "library_podcasts"

    # additional library features
    ARTIST_ALBUMS = "artist_albums"
    ARTIST_TOPTRACKS = "artist_toptracks"

    # library edit (=add/remove) feature per mediatype
    LIBRARY_ARTISTS_EDIT = "library_artists_edit"
    LIBRARY_ALBUMS_EDIT = "library_albums_edit"
    LIBRARY_TRACKS_EDIT = "library_tracks_edit"
    LIBRARY_PLAYLISTS_EDIT = "library_playlists_edit"
    LIBRARY_RADIOS_EDIT = "library_radios_edit"
    LIBRARY_AUDIOBOOKS_EDIT = "library_audiobooks_edit"
    LIBRARY_PODCASTS_EDIT = "library_podcasts_edit"

    # if we can grab 'similar tracks' from the music provider
    # used to generate dynamic playlists
    SIMILAR_TRACKS = "similar_tracks"

    # playlist-specific features
    PLAYLIST_TRACKS_EDIT = "playlist_tracks_edit"
    PLAYLIST_CREATE = "playlist_create"

    #
    # PLAYERPROVIDER FEATURES
    #
    SYNC_PLAYERS = "sync_players"
    REMOVE_PLAYER = "remove_player"

    #
    # METADATAPROVIDER FEATURES
    #
    ARTIST_METADATA = "artist_metadata"
    ALBUM_METADATA = "album_metadata"
    TRACK_METADATA = "track_metadata"

    #
    # PLUGIN FEATURES
    #
    AUDIO_SOURCE = "audio_source"

    # fallback
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> ProviderFeature:  # noqa: ARG003
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN


class ProviderType(StrEnum):
    """Enum with supported provider types."""

    MUSIC = "music"
    PLAYER = "player"
    METADATA = "metadata"
    PLUGIN = "plugin"
    CORE = "core"


class ConfigEntryType(StrEnum):
    """Enum for the type of a config entry."""

    BOOLEAN = "boolean"
    STRING = "string"
    SECURE_STRING = "secure_string"
    INTEGER = "integer"
    FLOAT = "float"
    LABEL = "label"
    INTEGER_TUPLE = "integer_tuple"
    DIVIDER = "divider"
    ACTION = "action"
    ICON = "icon"
    ALERT = "alert"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> ConfigEntryType:  # noqa: ARG003
        """Set default enum member if an unknown value is provided."""
        return cls.UNKNOWN


class StreamType(StrEnum):
    """Enum for the type of streamdetails."""

    HTTP = "http"  # regular http stream
    ENCRYPTED_HTTP = "encrypted_http"  # encrypted http stream
    HLS = "hls"  # http HLS stream
    ICY = "icy"  # http stream with icy metadata
    LOCAL_FILE = "local_file"
    CUSTOM = "custom"


class CacheCategory(IntEnum):
    """Enum with predefined cache categories."""

    DEFAULT = 0
    MUSIC_SEARCH = 1
    MUSIC_ALBUM_TRACKS = 2
    MUSIC_ARTIST_TRACKS = 3
    MUSIC_ARTIST_ALBUMS = 4
    MUSIC_PLAYLIST_TRACKS = 5
    MUSIC_PROVIDER_ITEM = 6
    PLAYER_QUEUE_STATE = 7
    MEDIA_INFO = 8
    LIBRARY_ITEMS = 9


class VolumeNormalizationMode(StrEnum):
    """Enum with possible VolumeNormalization modes."""

    DISABLED = "disabled"
    DYNAMIC = "dynamic"
    MEASUREMENT_ONLY = "measurement_only"
    FALLBACK_FIXED_GAIN = "fallback_fixed_gain"
    FIXED_GAIN = "fixed_gain"
    FALLBACK_DYNAMIC = "fallback_dynamic"
