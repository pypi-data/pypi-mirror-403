from dataclasses import dataclass

from clochette import log
from clochette.application.service.SnoozeModel import SnoozeModel
from clochette.application.store.RestoreSnoozeStore import RestoreSnoozeStore
from clochette.domain.entity.CalendarID import CalendarID
from clochette.application.repository.SnoozeRepository import SnoozeRepository


@dataclass
class RestoreSnoozeUseCase:
    """Use case for restoring persisted snoozes from the database into the application state."""

    _restore_snooze_store: RestoreSnoozeStore
    _snooze_repository: SnoozeRepository
    _snooze_model: SnoozeModel

    def restore_snooze(self, calendar_id: CalendarID) -> None:
        """Restore snoozed events for a calendar from the database.

        Only restores snoozes once per calendar to avoid duplicates.
        Subsequent calls for the same calendar_id are no-ops.
        """
        # Check if we've already restored snoozes for this calendar
        already_restored = self._restore_snooze_store.mark_restored(calendar_id)

        if not already_restored:
            log.info(f"Restoring snoozed events for calendar: {calendar_id}")
            snoozes = self._snooze_repository.get_snoozes_by_calendar(calendar_id)

            if snoozes:
                log.debug(f"Snoozed events found at startup, ids: {[snooze.event_id for snooze in snoozes]}")
            else:
                log.debug("No Snoozed events found at startup")

            for snooze in snoozes:
                self._snooze_model.add_snooze(snooze)
