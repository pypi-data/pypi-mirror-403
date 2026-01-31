from dataclasses import dataclass

from clochette import log
from clochette.application.service.EventModel import EventModel
from clochette.application.service.ical.ICalendarService import ICalendarService
from clochette.application.store.OccurrenceStore import OccurrenceStore
from clochette.application.usecase.DismissAllOccurrencesUseCase import DismissAllOccurrencesUseCase
from clochette.application.usecase.DismissOccurrenceUseCase import DismissOccurrenceUseCase
from clochette.application.usecase.SnoozeOccurrenceUseCase import SnoozeOccurrenceUseCase
from clochette.domain.entity.EventDetails import EventDetails
from clochette.domain.entity.Occurrence import Occurrence
from clochette.domain.entity.delta.SnoozeDelta import SnoozeDelta
from clochette.framework.qt.Link import Link
from clochette.framework.qt.QComponent import QComponent
from clochette.application.repository.CalendarRepository import CalendarRepository
from clochette.presentation.reminder_window.QReminderWindowView import QReminderWindowView


@dataclass
class ReminderWindowComponent(QComponent[QReminderWindowView]):
    _view: QReminderWindowView
    _event_model: EventModel
    _occurrence_store: OccurrenceStore
    _icalendar_service: ICalendarService
    _icalendar_repository: CalendarRepository
    _snooze_occurrence_use_case: SnoozeOccurrenceUseCase
    _dismiss_occurrence_use_case: DismissOccurrenceUseCase
    _dismiss_all_occurrences_use_case: DismissAllOccurrencesUseCase

    def __post_init__(self) -> None:
        super().__init__(self._view)

        # Wire view signals to use cases
        self._view.on_snooze_clicked.link(self._on_snooze_clicked)
        self._view.on_dismiss_clicked.link(self._on_dismiss_clicked)
        self._view.on_dismiss_all_clicked.link(self._on_dismiss_all_clicked)

    def start(self) -> None:
        """
        Start listening to occurrence updates.
        Should be called by InitializeReminderWindowUseCase after application startup.
        """
        # Subscribe to occurrences and update view with Link for thread safety
        Link(
            observable=self._occurrence_store.occurrences,
            handler=self._update_occurrences,
            widget=self._view,
        )

    def _update_occurrences(self, occurrences: list[Occurrence]) -> None:
        """
        Handle new occurrence updates from the store.
        This is called via Link, so it's already thread-safe for the view calls.
        """
        log.debug(f"New event occurrences received: {[occurrence.event_id for occurrence in occurrences]}")

        # Show/hide window based on whether there are occurrences
        if occurrences:
            self._view.display_window(True)
        else:
            self._view.display_window(False)

        # Update the occurrences list with details
        occurrences_with_info = self._get_occurrences_with_details(occurrences)
        self._view.update_occurrences(occurrences_with_info)

    def _get_occurrences_with_details(self, occurrences: list[Occurrence]) -> list[tuple[Occurrence, EventDetails]]:
        res: list[tuple[Occurrence, EventDetails]] = []

        for occurrence in occurrences:
            event = self._event_model.get_event(occurrence.event_id)
            if event:
                info = self._icalendar_service.parse_event_details(event.raw)
                res.append((occurrence, info))
            else:
                log.error(f"Trying to get an event which has been deleted, id: {occurrence.event_id} ")

        return res

    def _on_snooze_clicked(self, value: tuple[Occurrence, SnoozeDelta]) -> None:
        occurrence, delta = value
        self._snooze_occurrence_use_case.snooze(occurrence, delta)

    def _on_dismiss_clicked(self, occurrence: Occurrence) -> None:
        self._dismiss_occurrence_use_case.dismiss(occurrence)

    def _on_dismiss_all_clicked(self) -> None:
        self._dismiss_all_occurrences_use_case.dismiss_all()
