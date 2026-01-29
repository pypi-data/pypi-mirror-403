from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum


@dataclass
class AutoStartSchedule:
    """Configuration for automatic pool startup scheduling.

    Attributes:
        day_of_week: The day of the week when the pool should auto-start.
        start_time_utc: The time of day (UTC) when the pool should start.
        duration: How long the pool should remain active.
        tasks_to_start: Number of tasks to initiate on startup.
    """

    start_time_utc: timedelta
    duration: timedelta
    day_of_week: DayOfWeek
    tasks_to_start: int


class DayOfWeek(str, Enum):
    """Enumeration of days of the week."""

    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"
