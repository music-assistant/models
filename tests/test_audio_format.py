"""Tests for the AudioFormat model."""

from unittest.mock import ANY

from music_assistant_models.enums import ContentType
from music_assistant_models.media_items import AudioFormat


def _pcm(content_type: ContentType, bit_depth: int = 32) -> AudioFormat:
    return AudioFormat(
        content_type=content_type,
        sample_rate=44100,
        bit_depth=bit_depth,
        channels=2,
    )


def test_pcm_encodings_of_equal_depth_are_not_equal() -> None:
    """Integer and float PCM of the same depth describe different bytes."""
    s32 = _pcm(ContentType.PCM_S32LE)
    f32 = _pcm(ContentType.PCM_F32LE)
    assert s32 != f32
    assert len({s32, f32}) == 2


def test_pcm_companding_is_not_equal_to_linear_pcm() -> None:
    """A-law/mu-law are PCM content types but not interchangeable with linear PCM."""
    assert _pcm(ContentType.PCM_ALAW, bit_depth=16) != _pcm(ContentType.PCM_S16LE, bit_depth=16)


def test_generic_pcm_is_not_equal_to_a_concrete_encoding() -> None:
    """Generic PCM has no defined sample encoding, so it matches no concrete one."""
    assert _pcm(ContentType.PCM, bit_depth=16) != _pcm(ContentType.PCM_S16LE, bit_depth=16)


def test_identical_formats_are_equal_and_hash_alike() -> None:
    """The same content type, sample rate, bit depth and channel count compare equal."""
    assert _pcm(ContentType.PCM_S24LE) == _pcm(ContentType.PCM_S24LE)
    assert hash(_pcm(ContentType.PCM_S24LE)) == hash(_pcm(ContentType.PCM_S24LE))


def test_differing_sample_rate_bit_depth_or_channels_are_not_equal() -> None:
    """Sample rate, bit depth and channel count are all part of the identity."""
    base = AudioFormat(content_type=ContentType.FLAC, sample_rate=44100, bit_depth=16, channels=2)
    assert base != AudioFormat(
        content_type=ContentType.FLAC, sample_rate=48000, bit_depth=16, channels=2
    )
    assert base != AudioFormat(
        content_type=ContentType.FLAC, sample_rate=44100, bit_depth=24, channels=2
    )
    assert base != AudioFormat(
        content_type=ContentType.FLAC, sample_rate=44100, bit_depth=16, channels=1
    )


def test_descriptive_fields_do_not_affect_equality() -> None:
    """codec_type, bit_rate and output_format_str are excluded, and so is the hash."""
    probed = AudioFormat(content_type=ContentType.OGG, codec_type=ContentType.VORBIS, bit_rate=320)
    unprobed = AudioFormat(content_type=ContentType.OGG)
    assert probed == unprobed
    assert hash(probed) == hash(unprobed)

    renamed = AudioFormat(content_type=ContentType.FLAC, output_format_str="custom")
    assert renamed == AudioFormat(content_type=ContentType.FLAC)
    assert hash(renamed) == hash(AudioFormat(content_type=ContentType.FLAC))


def test_a_serialization_round_trip_stays_equal() -> None:
    """A format survives to_dict/from_dict as an equal format."""
    original = AudioFormat(content_type=ContentType.MP3, sample_rate=48000, channels=2)
    assert AudioFormat.from_dict(original.to_dict()) == original


def test_not_equal_to_other_types() -> None:
    """Unsupported operands can provide reflected equality behavior."""
    audio_format = _pcm(ContentType.PCM_S16LE, bit_depth=16)
    assert audio_format != "pcm"
    assert audio_format == ANY
