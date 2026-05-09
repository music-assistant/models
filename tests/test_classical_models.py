"""Tests for classical-music model additions: Credit, Work, and credit-typed properties."""

from music_assistant_models.enums import ArtistRole, ExternalID, MediaType, WorkType
from music_assistant_models.media_items import (
    Album,
    Credit,
    ItemMapping,
    Track,
    Work,
    media_from_dict,
)


def _artist_mapping(name: str, item_id: str = "1") -> ItemMapping:
    """Build a minimal artist ItemMapping for tests."""
    return ItemMapping(
        item_id=item_id,
        provider="test",
        name=name,
        media_type=MediaType.ARTIST,
    )


def test_work_construction_and_mbid_roundtrip() -> None:
    """Work supports MusicBrainz Work MBID via external_ids and the mbid property."""
    work = Work(
        item_id="w1",
        provider="test",
        name="Symphony No. 5 in C minor, Op. 67",
        provider_mappings=set(),
        catalog_numbers=["Op. 67"],
        work_type=WorkType.SYMPHONY,
    )
    work.mbid = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    assert work.mbid == "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    assert (ExternalID.MB_WORK, "f47ac10b-58cc-4372-a567-0e02b2c3d479") in work.external_ids


def test_work_roundtrips_via_media_from_dict() -> None:
    """media_from_dict dispatches MediaType.WORK to Work.from_dict correctly."""
    work = Work(
        item_id="w1",
        provider="test",
        name="Brandenburg Concerto No. 5",
        provider_mappings=set(),
        work_type=WorkType.CONCERTO,
    )
    restored = media_from_dict(work.to_dict())
    assert isinstance(restored, Work)
    assert restored.name == "Brandenburg Concerto No. 5"
    assert restored.work_type == WorkType.CONCERTO


def test_track_credit_convenience_properties() -> None:
    """Track.composers / conductors / performers_with_instruments filter by role."""
    composer = _artist_mapping("Beethoven", "a1")
    conductor = _artist_mapping("Karajan", "a2")
    soloist = _artist_mapping("Heifetz", "a3")
    performer = _artist_mapping("Section Violinist", "a4")

    track = Track(
        item_id="t1",
        provider="test",
        name="Symphony No. 5: I. Allegro con brio",
        provider_mappings=set(),
        credits=[
            Credit(artist=composer, role=ArtistRole.COMPOSER, position=0),
            Credit(artist=conductor, role=ArtistRole.CONDUCTOR, position=0),
            Credit(artist=soloist, role=ArtistRole.SOLOIST, instrument="violin", position=0),
            Credit(artist=performer, role=ArtistRole.PERFORMER, instrument=None, position=1),
        ],
    )

    assert track.composers == [composer]
    assert track.conductors == [conductor]
    assert track.performers_with_instruments == [(soloist, "violin"), (performer, None)]


def test_track_credits_returned_in_position_order() -> None:
    """Credits added out of position order are returned sorted by position within their role."""
    a1 = _artist_mapping("Composer1", "a1")
    a2 = _artist_mapping("Composer2", "a2")
    a3 = _artist_mapping("Composer3", "a3")

    track = Track(
        item_id="t1",
        provider="test",
        name="Some Work",
        provider_mappings=set(),
        credits=[
            Credit(artist=a3, role=ArtistRole.COMPOSER, position=2),
            Credit(artist=a1, role=ArtistRole.COMPOSER, position=0),
            Credit(artist=a2, role=ArtistRole.COMPOSER, position=1),
        ],
    )
    assert track.composers == [a1, a2, a3]


def test_track_classical_fields_default_to_none() -> None:
    """Work / movement_* / credits default sensibly for non-classical tracks."""
    track = Track(
        item_id="t1",
        provider="test",
        name="Pop song",
        provider_mappings=set(),
    )
    assert track.work is None
    assert track.movement_number is None
    assert track.movement_total is None
    assert track.movement_name is None
    assert track.credits == []


def test_album_credit_convenience_properties() -> None:
    """Album.composers / conductors filter credits by role."""
    composer = _artist_mapping("Beethoven", "a1")
    conductor = _artist_mapping("Karajan", "a2")
    album = Album(
        item_id="al1",
        provider="test",
        name="Karajan conducts Beethoven",
        provider_mappings=set(),
        credits=[
            Credit(artist=composer, role=ArtistRole.COMPOSER),
            Credit(artist=conductor, role=ArtistRole.CONDUCTOR),
        ],
    )
    assert album.composers == [composer]
    assert album.conductors == [conductor]


def test_artistrole_unknown_falls_back_to_performer() -> None:
    """ArtistRole._missing_ returns PERFORMER for forward compatibility."""
    assert ArtistRole("not_a_real_role") == ArtistRole.PERFORMER


def test_worktype_unknown_falls_back_to_other() -> None:
    """WorkType._missing_ returns OTHER for forward compatibility."""
    assert WorkType("not_a_real_type") == WorkType.OTHER
