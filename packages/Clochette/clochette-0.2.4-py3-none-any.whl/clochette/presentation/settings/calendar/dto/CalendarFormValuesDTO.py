from dataclasses import dataclass
from datetime import timedelta

from clochette.domain.entity.delta.AlarmDelta import AlarmDelta
from clochette.domain.entity.ISourceCalendar import ISourceCalendar
from clochette.domain.entity.configuration.HttpTimeout import HttpTimeout


@dataclass(frozen=True)
class CalendarFormValuesDTO:
    """Simple DTO containing form values from the calendar configuration view"""

    name: str
    source: ISourceCalendar
    download_interval: timedelta
    missed_reminders_past_window: timedelta
    http_timeout: HttpTimeout
    force_alarms: list[AlarmDelta]
    force_alarms_dates: list[AlarmDelta]
    default_alarms: list[AlarmDelta]
    default_alarms_dates: list[AlarmDelta]
