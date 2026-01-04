"""Serialization strategies for mashumaro."""

from datetime import UTC, datetime

from mashumaro.types import SerializationStrategy


class DatetimeToUnixTimestampStrategy(SerializationStrategy):
    """(De)Serialize a datetime to an integer unix timestamp."""

    def serialize(self, value: datetime) -> int:
        """Serialize datetime."""
        return int(value.timestamp())

    def deserialize(self, value: int) -> datetime:
        """Deserialize integer."""
        return datetime.fromtimestamp(value, tz=UTC)
