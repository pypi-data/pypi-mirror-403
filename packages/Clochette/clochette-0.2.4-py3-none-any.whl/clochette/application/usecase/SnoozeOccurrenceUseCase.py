from dataclasses import dataclass

from clochette import log
from clochette.application.service.SnoozeModel import SnoozeModel
from clochette.application.store.OccurrenceStore import OccurrenceStore
from clochette.domain.entity.Occurrence import Occurrence
from clochette.domain.entity.Snooze import Snooze
from clochette.domain.entity.delta.SnoozeDelta import SnoozeDelta
from clochette.domain.entity.Trigger import Trigger
from clochette.application.repository.SnoozeRepository import SnoozeRepository


@dataclass
class SnoozeOccurrenceUseCase:
    """Use case for snoozing an occurrence."""

    _occurrence_store: OccurrenceStore
    _snooze_model: SnoozeModel
    _snooze_repository: SnoozeRepository

    def snooze(self, occurrence: Occurrence, delta: SnoozeDelta) -> None:
        """Snooze an occurrence by dismissing it and scheduling it for later.

        Args:
            occurrence: The occurrence to snooze
            delta: How long to snooze for
        """
        log.info(f"Snoozed occurrence: {occurrence.event_id}")

        # Dismiss the current occurrence
        self._occurrence_store.dismiss_occurrence(occurrence)

        # Delete any existing snooze for this event
        self._snooze_repository.delete_snoozes([occurrence.event_id])

        # Create new snooze with updated trigger time
        trigger = Trigger(occurrence.trigger.trigger + delta.get_timedelta(), occurrence.trigger.start)
        snooze = Snooze(-1, occurrence.event_id, trigger)

        # Add to both model (in-memory) and repository (database)
        self._snooze_model.add_snooze(snooze)
        self._snooze_repository.add_snooze(snooze)
