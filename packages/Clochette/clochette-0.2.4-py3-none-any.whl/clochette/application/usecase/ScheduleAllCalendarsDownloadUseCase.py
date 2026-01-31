from dataclasses import dataclass

from clochette import log
from clochette.application.usecase.ScheduleCalendarDownloadUseCase import ScheduleCalendarDownloadUseCase
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration


@dataclass
class ScheduleAllCalendarsDownloadUseCase:
    """Use case to schedule downloads for all calendars."""

    _schedule_calendar_download_usecase: ScheduleCalendarDownloadUseCase

    def schedule_all_calendars(self, calendars: list[CalendarConfiguration]) -> None:
        """Schedule downloads for all calendars."""
        log.info(f"Scheduling downloads for {len(calendars)} calendars")

        for calendar in calendars:
            self._schedule_calendar_download_usecase.schedule_calendar(calendar)
