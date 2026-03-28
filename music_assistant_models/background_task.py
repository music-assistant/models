"""Models for long running background tasks in Music Assistant."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from mashumaro import DataClassDictMixin

from .enums import TaskScheduleType, TaskStatus

type TaskMetadataValue = (
    None
    | bool
    | int
    | float
    | str
    | list[TaskMetadataValue]
    | dict[str, TaskMetadataValue]
)
type TaskMetadata = dict[str, TaskMetadataValue]


@dataclass
class TaskSchedule(DataClassDictMixin):
    """
    Recurring schedule details for a background task.

    All clock-based fields use UTC. `days_of_week` uses Python's weekday numbering:
    Monday is `0` and Sunday is `6`. `every` means:
    - every N hours for hourly schedules
    - every N days for daily schedules
    """

    type: TaskScheduleType = TaskScheduleType.HOURLY
    # Whether automatic recurring runs are active for this task.
    enabled: bool = True
    # Repeat interval count for hourly/daily schedules.
    every: int | None = None
    # Weekdays for weekly schedules, using Monday=0 ... Sunday=6.
    days_of_week: list[int] | None = None
    # UTC hour for daily/weekly schedules.
    hour: int | None = None
    # UTC minute for daily/weekly schedules.
    minute: int | None = None

    def __post_init__(self) -> None:
        """Validate schedule fields."""
        if self.type == TaskScheduleType.UNKNOWN:
            return
        if self.type == TaskScheduleType.HOURLY:
            self._validate_every("Hourly schedule")
            self.days_of_week = None
            self.hour = None
            self.minute = None
            return
        if self.type == TaskScheduleType.DAILY:
            self._validate_every("Daily schedule")
            self._validate_clock_time()
            self.days_of_week = None
            return
        if self.type == TaskScheduleType.WEEKLY:
            self._validate_clock_time()
            if not self.days_of_week:
                raise ValueError("Weekly schedule requires at least one day_of_week")
            normalized_days = sorted(set(self.days_of_week))
            if any(day < 0 or day > 6 for day in normalized_days):
                raise ValueError("days_of_week must only contain values between 0 and 6")
            self.days_of_week = normalized_days
            self.every = None
            return

    @classmethod
    def hourly(
        cls,
        *,
        every: int = 1,
    ) -> TaskSchedule:
        """Create an hourly schedule."""
        return cls(
            type=TaskScheduleType.HOURLY,
            every=every,
        )

    @classmethod
    def daily(
        cls,
        *,
        every: int = 1,
        hour: int,
        minute: int = 0,
    ) -> TaskSchedule:
        """Create a daily UTC schedule."""
        return cls(
            type=TaskScheduleType.DAILY,
            every=every,
            hour=hour,
            minute=minute,
        )

    @classmethod
    def weekly(
        cls,
        *,
        days_of_week: list[int],
        hour: int,
        minute: int = 0,
    ) -> TaskSchedule:
        """Create a weekly UTC schedule."""
        return cls(
            type=TaskScheduleType.WEEKLY,
            days_of_week=days_of_week,
            hour=hour,
            minute=minute,
        )

    def _validate_clock_time(self) -> None:
        """Validate hour/minute fields for daily/weekly schedules."""
        if self.hour is None or not 0 <= self.hour <= 23:
            raise ValueError("Schedule hour must be between 0 and 23")
        if self.minute is None or not 0 <= self.minute <= 59:
            raise ValueError("Schedule minute must be between 0 and 59")

    def _validate_every(self, prefix: str) -> None:
        """Validate the `every` interval field."""
        if self.every is None or self.every <= 0:
            raise ValueError(f"{prefix} requires every > 0")


@dataclass
class BackgroundTask(DataClassDictMixin):
    """Serializable representation of a long running background task."""

    name: str
    id: str = field(default_factory=lambda: uuid4().hex)
    status: TaskStatus = TaskStatus.PENDING
    # Optional translation key for rendering the task name in the UI.
    translation_key: str | None = None
    # Positional translation args for `translation_key`.
    translation_args: list[Any] = field(default_factory=list)
    # In-memory tail of recent log lines for the current/last run.
    logs: list[str] = field(default_factory=list)
    # Recurring schedule for automatic runs; `None` for ad hoc tasks.
    schedule: TaskSchedule | None = None
    # UTC timestamp of the last started run.
    last_run: datetime | None = None
    # UTC timestamp of the next automatic run, if one is scheduled.
    next_run: datetime | None = None
    # User who manually queued the task, if applicable.
    user_id: str | None = None
    # User that last triggered the task run; `None` for automatic/system runs.
    last_run_user_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    last_error: str | None = None
    # Count of non-fatal issues reported during the current/last run.
    failure_count: int = 0
    # In-memory tail of recent non-fatal failure messages for the current/last run.
    failure_messages: list[str] = field(default_factory=list)
    # Extra JSON-serializable context used for filtering and UI display.
    metadata: TaskMetadata = field(default_factory=dict)
    # Integer completion percentage. `None` means indeterminate.
    progress: int | None = None
    # Human-readable phase text for the current run.
    progress_text: str | None = None
    # Whether a failed/cancelled run is safe to retry from the UI.
    allow_retry: bool = False
    # Whether queued/running work can be interrupted from the UI.
    allow_cancel: bool = True

    def __post_init__(self) -> None:
        """Validate background task fields."""
        if self.progress is not None and not 0 <= self.progress <= 100:
            raise ValueError("BackgroundTask progress must be between 0 and 100")
        if self.failure_count < 0:
            raise ValueError("BackgroundTask failure_count must be >= 0")
