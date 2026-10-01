"""Tests for the PodcastEpisode MediaItem."""

from music_assistant_models.media_items import PodcastEpisode, media_from_dict


def _episode_dict(**extra: int) -> dict:
    return {
        "item_id": "1",
        "provider": "builtin--1",
        "name": "Pilot",
        "media_type": "podcast_episode",
        "position": 1,
        "podcast": {
            "item_id": "2",
            "provider": "builtin--1",
            "name": "Show",
            "media_type": "podcast",
        },
        "provider_mappings": [
            {"item_id": "1", "provider_domain": "builtin", "provider_instance": "builtin--1"}
        ],
        **extra,
    }


def test_episode_number_and_season_default_to_none() -> None:
    """An episode sent without a number or season has neither."""
    episode = media_from_dict(_episode_dict())

    assert isinstance(episode, PodcastEpisode)
    assert episode.episode_number is None
    assert episode.season is None


def test_episode_number_and_season_round_trip() -> None:
    """The publisher's episode and season number survive serialization."""
    episode = media_from_dict(_episode_dict(episode_number=14, season=2))

    assert isinstance(episode, PodcastEpisode)
    restored = media_from_dict(episode.to_dict())
    assert isinstance(restored, PodcastEpisode)
    assert (restored.episode_number, restored.season) == (14, 2)
