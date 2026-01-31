from dataclasses import dataclass

from reactivex import operators as ops, Observable

from clochette import log
from clochette.application.repository.CalendarRepository import CalendarRepository
from clochette.application.store.CalendarConfigurationStore import CalendarConfigurationStore
from clochette.application.usecase.PersistConfigurationUseCase import PersistConfigurationUseCase
from clochette.application.usecase.ScheduleCalendarDownloadUseCase import ScheduleCalendarDownloadUseCase
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.framework.rx.Scheduler import scheduler


@dataclass
class AddCalendarUseCase:
    """Use case to add a new calendar to the configuration store."""

    _calendar_configuration_store: CalendarConfigurationStore
    _persist_configuration_usecase: PersistConfigurationUseCase
    _schedule_calendar_download_usecase: ScheduleCalendarDownloadUseCase
    _calendar_repository: CalendarRepository

    def add_calendar(self, calendar: CalendarConfiguration) -> Observable[None]:
        """Add a new calendar to the configuration store and persist to disk."""

        log.info(f"Adding new calendar: {calendar}")

        def update_store(calendars: list[CalendarConfiguration]) -> Observable[None]:
            # Add new calendar to the list
            updated_calendars = calendars + [calendar]
            self._calendar_configuration_store.set_calendars(updated_calendars)
            self._calendar_configuration_store.add_calendar(calendar)

            # Persist to disk
            return self._persist_configuration_usecase.persist_configuration().pipe(
                ops.do_action(on_next=lambda _: self._schedule_calendar_download_usecase.schedule_calendar(calendar)),
            )

        return self._calendar_configuration_store.calendars.pipe(
            ops.take(1),
            ops.do_action(
                on_next=lambda _: self._calendar_repository.add_calendar(calendar),
            ),
            ops.flat_map(lambda x: update_store(x)),
            ops.do_action(
                on_error=lambda e: log.error(f"Error while adding calendar named: {calendar.name}", exc_info=e)
            ),
            ops.subscribe_on(scheduler=scheduler),
        )
