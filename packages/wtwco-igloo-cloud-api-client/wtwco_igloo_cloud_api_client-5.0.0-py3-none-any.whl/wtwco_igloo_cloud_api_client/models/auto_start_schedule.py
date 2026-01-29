from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.day_of_week import DayOfWeek

T = TypeVar("T", bound="AutoStartSchedule")


@_attrs_define
class AutoStartSchedule:
    """
    Attributes:
        start_time_utc (str): The UTC time at which the tasks should start, measured as a number of hours from the start
            of the day.
            This must be below 24 hours
        duration (str): The amount of time that the tasks should run for.
            This must be below 24 hours
        day_of_week (DayOfWeek):
        tasks_to_start (int): The number of tasks that should be run
    """

    start_time_utc: str
    duration: str
    day_of_week: DayOfWeek
    tasks_to_start: int

    def to_dict(self) -> dict[str, Any]:
        start_time_utc = self.start_time_utc

        duration = self.duration

        day_of_week = self.day_of_week.value

        tasks_to_start = self.tasks_to_start

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "startTimeUtc": start_time_utc,
                "duration": duration,
                "dayOfWeek": day_of_week,
                "tasksToStart": tasks_to_start,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        start_time_utc = d.pop("startTimeUtc")

        duration = d.pop("duration")

        day_of_week = DayOfWeek(d.pop("dayOfWeek"))

        tasks_to_start = d.pop("tasksToStart")

        auto_start_schedule = cls(
            start_time_utc=start_time_utc,
            duration=duration,
            day_of_week=day_of_week,
            tasks_to_start=tasks_to_start,
        )

        return auto_start_schedule
