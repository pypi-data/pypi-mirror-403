from dataclasses import dataclass

from reactivex import operators as ops, Observable

from clochette import log
from clochette.application.usecase.ScheduleCalendarDownloadUseCase import ScheduleCalendarDownloadUseCase
from clochette.application.usecase.UnscheduleCalendarDownloadUseCase import UnscheduleCalendarDownloadUseCase
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.framework.rx.Scheduler import scheduler


@dataclass
class RescheduleCalendarDownloadUseCase:
    """Use case to reschedule downloads for a calendar."""

    _unschedule_calendar_download_usecase: UnscheduleCalendarDownloadUseCase
    _schedule_calendar_download_usecase: ScheduleCalendarDownloadUseCase

    def reschedule_calendar(self, calendar: CalendarConfiguration) -> Observable[None]:
        """Reschedule downloads for a calendar (unschedule old, schedule new)."""
        log.info(f"Rescheduling downloads for calendar: {calendar.name}")

        # Unschedule the old task
        return self._unschedule_calendar_download_usecase.unschedule_calendar(calendar).pipe(
            ops.map(lambda _: None),
            ops.do_action(
                on_next=lambda _: self._schedule_calendar_download_usecase.schedule_calendar(calendar),
                on_error=lambda e: log.error(
                    f"Failed to reschedule downloads for calendar named: {calendar.name}", exc_info=e
                ),
            ),
            ops.subscribe_on(scheduler=scheduler),
        )
