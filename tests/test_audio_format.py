"""Tests for the AudioFormat model."""

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
    assert _pcm(ContentType.PCM_S32LE) != _pcm(ContentType.PCM_F32LE)
    assert hash(_pcm(ContentType.PCM_S32LE)) != hash(_pcm(ContentType.PCM_F32LE))


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


def test_differing_sample_rate_or_channels_are_not_equal() -> None:
    """Sample rate and channel count are part of the identity."""
    base = AudioFormat(content_type=ContentType.FLAC, sample_rate=44100, bit_depth=16, channels=2)
    assert base != AudioFormat(
        content_type=ContentType.FLAC, sample_rate=48000, bit_depth=16, channels=2
    )
    assert base != AudioFormat(
        content_type=ContentType.FLAC, sample_rate=44100, bit_depth=16, channels=1
    )


def test_bit_rate_and_codec_type_are_ignored() -> None:
    """
    Informational fields do not affect equality.

    codec_type in particular is filled in later, once ffmpeg has probed the input.
    """
    assert AudioFormat(content_type=ContentType.MP3, bit_rate=128) == AudioFormat(
        content_type=ContentType.MP3, bit_rate=320
    )
    assert AudioFormat(content_type=ContentType.OGG) == AudioFormat(
        content_type=ContentType.OGG, codec_type=ContentType.VORBIS
    )


def test_not_equal_to_other_types() -> None:
    """Comparing against a non-AudioFormat returns False rather than raising."""
    assert _pcm(ContentType.PCM_S16LE, bit_depth=16) != "pcm"
