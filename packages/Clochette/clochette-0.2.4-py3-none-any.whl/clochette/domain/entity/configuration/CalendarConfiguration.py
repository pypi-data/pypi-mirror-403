from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from clochette.domain.entity.delta.AlarmDelta import AlarmDelta
from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.configuration.HttpTimeout import HttpTimeout
from clochette.domain.entity.ISourceCalendar import ISourceCalendar


@dataclass(frozen=True, eq=True)
class CalendarConfiguration:
    id: CalendarID
    name: str
    source: ISourceCalendar
    force_alarms: list[AlarmDelta]
    force_alarms_dates: list[AlarmDelta]
    default_alarms: list[AlarmDelta]
    default_alarms_dates: list[AlarmDelta]
    download_interval: timedelta
    missed_reminders_past_window: timedelta
    http_timeout: HttpTimeout

    def __post_init__(self):
        if self.download_interval.total_seconds() <= 0:
            raise ValueError(f"download_interval cannot be null or negative, calendar: {self.name}")

        if self.missed_reminders_past_window.total_seconds() > 0:
            raise ValueError(f"missed_reminders_past_window cannot be positive, calendar: {self.name}")

    def __hash__(self) -> int:
        return hash(self.id)
