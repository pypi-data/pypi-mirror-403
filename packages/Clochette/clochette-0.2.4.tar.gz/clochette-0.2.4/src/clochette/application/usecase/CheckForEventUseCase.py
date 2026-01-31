from dataclasses import dataclass

from clochette import log
from clochette.application.service.EventModel import EventModel
from clochette.application.store.OccurrenceStore import OccurrenceStore
from clochette.infrastructure.clock.ClockService import ClockService


@dataclass
class CheckForEventUseCase:
    """Use case to check for event reminders that need to be displayed."""

    _event_model: EventModel
    _occurrence_store: OccurrenceStore
    _clock_service: ClockService

    def check_for_events(self) -> None:
        """Check for event reminders and add them to the occurrence store."""
        now = self._clock_service.utc_now()
        occurrences = self._event_model.query_occurrences(now)

        if occurrences:
            log.debug(f"Found new occurrences to display: {occurrences}")

        for occurrence in occurrences:
            log.info(f"Adding new occurrence to display: {occurrence}")
            self._occurrence_store.add_occurrence(occurrence)
