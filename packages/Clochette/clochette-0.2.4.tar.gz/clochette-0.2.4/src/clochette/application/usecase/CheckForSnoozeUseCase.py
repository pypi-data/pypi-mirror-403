from dataclasses import dataclass

from clochette import log
from clochette.application.service.SnoozeModel import SnoozeModel
from clochette.application.store.OccurrenceStore import OccurrenceStore
from clochette.infrastructure.clock.ClockService import ClockService


@dataclass
class CheckForSnoozeUseCase:
    """Use case to check for snooze reminders that need to be displayed."""

    _snooze_model: SnoozeModel
    _occurrence_store: OccurrenceStore
    _clock_service: ClockService

    def check_for_snoozes(self) -> None:
        """Check for snooze reminders and add them to the occurrence store."""
        now = self._clock_service.utc_now()
        occurrences = self._snooze_model.query_occurrences(now)

        if occurrences:
            log.debug(f"Found new snoozed occurrences to display: {occurrences}")

        for occurrence in occurrences:
            self._occurrence_store.add_occurrence(occurrence)
