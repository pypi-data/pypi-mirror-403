from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from wtwco_igloo.extensions.utils.types.calculation_pool_types import AutoStartSchedule, DayOfWeek


@dataclass
class CalculationPool:
    """Represents a calculation pool for running Igloo computations.

    Attributes:
        id: Id of the calculation pool.
        name: Name of the pool.
        auto_start_schedules: List of automatic startup schedules.
        igloo_version: Version of Igloo software running on the pool.
        cores: Number of CPU cores per machine.
        memory_in_gib: Memory allocation per machine in GiB.
        maximum_machines: Maximum number of machines in the pool.
        tasks_per_machine: Number of concurrent tasks per machine.
    """

    id: int
    name: str
    auto_start_schedules: list[AutoStartSchedule]
    igloo_version: str
    cores: int
    memory_in_gib: int
    maximum_machines: int
    tasks_per_machine: int

    def __getitem__(self, key: str):
        """Enable dictionary-style access to attributes. This is added for backwards compatibility.

        Args:
            key: The attribute name to access.

        Returns:
            The value of the requested attribute.

        Raises:
            KeyError: If the attribute doesn't exist.
        """
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key) from None

    @classmethod
    def from_dict(cls: type[CalculationPool], pool_dict: dict) -> CalculationPool:
        """Create a CalculationPool instance from a dictionary.

        Args:
            pool_dict: Dictionary containing pool configuration data from the API.

        Returns:
            A new CalculationPool instance populated with the provided data.
        """
        id = pool_dict["id"]
        name = pool_dict["name"]
        auto_start_schedules = [
            AutoStartSchedule(
                start_time_utc=cls._parse_timedelta(schedule["startTimeUtc"]),
                duration=cls._parse_timedelta(schedule["duration"]),
                day_of_week=DayOfWeek(schedule["dayOfWeek"]),
                tasks_to_start=schedule["tasksToStart"],
            )
            for schedule in pool_dict["autoStartConfiguration"]["autoStartSchedules"]
        ]
        igloo_version = pool_dict["iglooVersion"]
        cores = pool_dict["cores"]
        memory_in_gib = pool_dict["memoryInGiB"]
        maximum_machines = pool_dict["maximumMachines"]
        tasks_per_machine = pool_dict["tasksPerMachine"]
        return cls(
            id, name, auto_start_schedules, igloo_version, cores, memory_in_gib, maximum_machines, tasks_per_machine
        )

    @staticmethod
    def _parse_timedelta(time_str: str) -> timedelta:
        """Parse time string in HH:MM:SS format to timedelta."""
        time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
        return timedelta(hours=time_obj.hour, minutes=time_obj.minute, seconds=time_obj.second)
