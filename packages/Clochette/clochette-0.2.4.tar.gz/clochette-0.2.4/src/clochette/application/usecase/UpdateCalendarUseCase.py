from dataclasses import dataclass

from reactivex import operators as ops, Observable, combine_latest

from clochette import log
from clochette.application.store.CalendarConfigurationStore import CalendarConfigurationStore
from clochette.application.usecase.PersistConfigurationUseCase import PersistConfigurationUseCase
from clochette.application.usecase.RescheduleCalendarDownloadUseCase import RescheduleCalendarDownloadUseCase
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.framework.rx.Scheduler import scheduler


@dataclass
class UpdateCalendarUseCase:
    """Use case to update an existing calendar in the configuration store."""

    _calendar_configuration_store: CalendarConfigurationStore
    _persist_configuration_usecase: PersistConfigurationUseCase
    _reschedule_calendar_download_usecase: RescheduleCalendarDownloadUseCase

    def update_calendar(self, calendar: CalendarConfiguration) -> Observable[None]:
        """Update an existing calendar in the configuration store and persist to disk."""

        log.info(f"Updating calendar: {calendar}")

        def update_store(calendars: list[CalendarConfiguration]) -> Observable[None]:
            # Replace the calendar in the list
            updated_calendars = [calendar if cal.id == calendar.id else cal for cal in calendars]
            self._calendar_configuration_store.set_calendars(updated_calendars)
            self._calendar_configuration_store.update_calendar(calendar)

            return combine_latest(
                self._reschedule_calendar_download_usecase.reschedule_calendar(calendar),
                self._persist_configuration_usecase.persist_configuration(),
            ).pipe(
                ops.map(lambda _: None),
            )

        return self._calendar_configuration_store.calendars.pipe(
            ops.take(1),
            ops.flat_map(lambda x: update_store(x)),
            ops.do_action(
                on_error=lambda e: log.error(f"Failed to update calendar named: {calendar.name}", exc_info=e),
            ),
            ops.subscribe_on(scheduler=scheduler),
        )
