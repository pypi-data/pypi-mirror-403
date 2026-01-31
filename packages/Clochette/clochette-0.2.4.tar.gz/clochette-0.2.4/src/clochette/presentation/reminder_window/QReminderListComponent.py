from dataclasses import dataclass

from clochette.domain.entity.EventDetails import EventDetails
from clochette.domain.entity.Occurrence import Occurrence
from clochette.framework.qt.QComponent import QComponent
from clochette.framework.qt.Signal import InSolidSignal
from clochette.presentation.reminder_window.QReminderListView import QReminderListView


@dataclass
class QReminderListComponent(QComponent[QReminderListView]):
    """Component that manages the reminder list view with business logic."""

    _view: QReminderListView
    update_occurrences: InSolidSignal[list[tuple[Occurrence, EventDetails]]]

    def __post_init__(self) -> None:
        super().__init__(self._view)
        self.update_occurrences = InSolidSignal(self._on_update_occurrences)

    def _on_update_occurrences(self, occurrences: list[tuple[Occurrence, EventDetails]]) -> None:
        """Called when occurrences are updated - forwards to view in thread-safe manner."""
        self._view.set_occurrences(occurrences)
