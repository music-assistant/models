"""Common/shared (serializable) Models (dataclassses) for Music Assistant."""

from .background_task import BackgroundTask, TaskSchedule
from .enums import TaskScheduleType, TaskStatus
from .statistics import DailyStats, ListeningSummary, TopItem, TopItemResult

__all__ = [
    "BackgroundTask",
    "TaskSchedule",
    "TaskScheduleType",
    "TaskStatus",
    "DailyStats",
    "ListeningSummary",
    "TopItem",
    "TopItemResult",
]
