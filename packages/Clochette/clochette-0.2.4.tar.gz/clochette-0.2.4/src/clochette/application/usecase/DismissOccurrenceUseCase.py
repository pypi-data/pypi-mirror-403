from dataclasses import dataclass

from clochette import log
from clochette.application.store.OccurrenceStore import OccurrenceStore
from clochette.domain.entity.Occurrence import Occurrence
from clochette.application.repository.SnoozeRepository import SnoozeRepository


@dataclass
class DismissOccurrenceUseCase:
    """Use case for dismissing a single occurrence."""

    _occurrence_store: OccurrenceStore
    _snooze_repository: SnoozeRepository

    def dismiss(self, occurrence: Occurrence) -> None:
        """Dismiss an occurrence and remove any associated snoozes.

        Args:
            occurrence: The occurrence to dismiss
        """
        log.info(f"Occurrence dismissed: {occurrence}")
        self._occurrence_store.dismiss_occurrence(occurrence)
        self._snooze_repository.delete_snoozes([occurrence.event_id])
