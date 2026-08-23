"""Tests for background task serialization."""

from music_assistant_models.background_task import BackgroundTask


def test_report_defaults_to_none() -> None:
    """A task has no report until its work produces one."""
    task = BackgroundTask(name="Test task")

    assert task.report is None
    assert task.to_dict()["report"] is None


def test_markdown_report_roundtrip() -> None:
    """Markdown reports survive serialization without transformation."""
    report = "## Migration complete\n\n- Imported: **12**\n- Skipped: `2`"
    task = BackgroundTask(
        name="Import playlists",
        metadata={"imported": 12, "skipped": 2},
        report=report,
    )

    restored = BackgroundTask.from_dict(task.to_dict())

    assert restored.report == report
    assert restored.metadata == {"imported": 12, "skipped": 2}


def test_payload_without_report_deserializes() -> None:
    """Payloads created before report support retain the default."""
    payload = {"name": "Legacy task", "id": "legacy-task", "status": "pending"}

    assert BackgroundTask.from_dict(payload).report is None
