from dataclasses import dataclass

from clochette import log
from clochette.application.store.OccurrenceStore import OccurrenceStore
from clochette.domain.entity.Occurrence import Occurrence
from clochette.application.repository.SnoozeRepository import SnoozeRepository


@dataclass
class DismissAllOccurrencesUseCase:
    """Use case for dismissing all occurrences."""

    _occurrence_store: OccurrenceStore
    _snooze_repository: SnoozeRepository

    def dismiss_all(self) -> None:
        """Dismiss all occurrences and remove all associated snoozes."""
        log.info("All occurrences dismissed")

        # Get current occurrences before clearing
        occurrences = self._occurrence_store.get_occurrences()

        # Clear all occurrences from display
        self._occurrence_store.dismiss_all()

        # Delete all snoozes for dismissed occurrences
        self._delete_snoozes(occurrences)

    def _delete_snoozes(self, occurrences: list[Occurrence]) -> None:
        """Delete snoozes for a list of occurrences."""
        event_ids = [occ.event_id for occ in occurrences]
        self._snooze_repository.delete_snoozes(event_ids)
