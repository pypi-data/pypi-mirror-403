from reactivex import Observable
from reactivex.subject import BehaviorSubject

from clochette import log
from clochette.application.service.SnoozeModel import SnoozeModel
from clochette.domain.entity.Occurrence import Occurrence


class OccurrenceStore:
    """Store for managing active occurrences (events to be displayed to the user)."""

    _occurrences: BehaviorSubject[list[Occurrence]]
    _snooze_model: SnoozeModel

    def __init__(self, snooze_model: SnoozeModel) -> None:
        self._occurrences = BehaviorSubject([])
        self._snooze_model = snooze_model

    @property
    def occurrences(self) -> Observable[list[Occurrence]]:
        """Observable stream of occurrences."""
        return self._occurrences

    def add_occurrence(self, occurrence: Occurrence) -> None:
        """Add an occurrence to be displayed.

        Maintains unique occurrences per event (replaces existing occurrence for the same event).
        """
        log.info(f"New occurrence to display: {occurrence}")

        # unique list of occurrence per event
        occurrences_dict = {occ.event_id: occ for occ in self._occurrences.value}
        occurrences_dict[occurrence.event_id] = occurrence

        updated_occurrences = list(occurrences_dict.values())
        self._occurrences.on_next(updated_occurrences)

    def dismiss_occurrence(self, occurrence: Occurrence) -> None:
        """Remove a specific occurrence from display."""
        events = [occ for occ in self._occurrences.value if occ.event_id != occurrence.event_id]
        self._occurrences.on_next(events)

    def dismiss_all(self) -> None:
        """Remove all occurrences from display."""
        self._occurrences.on_next([])

    def get_occurrences(self) -> list[Occurrence]:
        """Get current list of occurrences."""
        return self._occurrences.value
