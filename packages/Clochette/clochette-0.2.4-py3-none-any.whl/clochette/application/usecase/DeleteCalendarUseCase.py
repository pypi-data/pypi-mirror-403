from dataclasses import dataclass
from typing import Any

from reactivex import operators as ops, Observable, combine_latest
from reactivex.operators import do_action

from clochette import log
from clochette.application.repository.CalendarRepository import CalendarRepository
from clochette.application.store.CalendarConfigurationStore import CalendarConfigurationStore
from clochette.application.usecase.PersistConfigurationUseCase import PersistConfigurationUseCase
from clochette.application.usecase.UnscheduleCalendarDownloadUseCase import UnscheduleCalendarDownloadUseCase
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.framework.rx.Scheduler import scheduler


@dataclass
class DeleteCalendarUseCase:
    """Use case to delete a calendar from the configuration store."""

    _calendar_configuration_store: CalendarConfigurationStore
    _persist_configuration_usecase: PersistConfigurationUseCase
    _unschedule_calendar_download_usecase: UnscheduleCalendarDownloadUseCase
    _calendar_repository: CalendarRepository

    def delete_calendar(self, calendar: CalendarConfiguration) -> Observable[None]:
        """Delete a calendar from the configuration store and persist to disk."""

        log.info(f"Deleting calendar: {calendar}")

        def update_store(calendars: list[CalendarConfiguration]) -> Observable[Any]:
            # Remove the calendar from the list
            updated_calendars = [cal for cal in calendars if cal.id != calendar.id]
            self._calendar_configuration_store.set_calendars(updated_calendars)
            self._calendar_configuration_store.delete_calendar(calendar)

            # Persist to disk
            return combine_latest(
                self._unschedule_calendar_download_usecase.unschedule_calendar(calendar),
                self._persist_configuration_usecase.persist_configuration(),
            )

        return self._calendar_configuration_store.calendars.pipe(
            ops.take(1),
            ops.do_action(lambda _: self._calendar_repository.delete_calendar(calendar)),
            ops.flat_map(lambda x: update_store(x)),
            do_action(on_error=lambda e: log.error(f"Error deleting calendar named: {calendar.name}", exc_info=e)),
            ops.map(lambda _: None),
            ops.subscribe_on(scheduler=scheduler),
        )
