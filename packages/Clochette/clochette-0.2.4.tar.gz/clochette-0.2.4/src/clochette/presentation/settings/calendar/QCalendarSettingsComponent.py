from dataclasses import dataclass

from clochette.framework.qt.Link import Link
from clochette.framework.qt.QComponent import QComponent
from clochette.presentation.settings.calendar.CalendarNavigationModel import CalendarNavigationModel
from clochette.presentation.settings.calendar.QCalendarSettings import QCalendarSettingsView


@dataclass
class QCalendarSettingsComponent(QComponent[QCalendarSettingsView]):
    """Component that wires CalendarNavigationModel to QCalendarSettingsView"""

    _view: QCalendarSettingsView
    _calendar_navigation_model: CalendarNavigationModel

    def __post_init__(self):
        super().__init__(self._view)

        # Wire: CalendarNavigationModel → View methods (Link wraps them in InSignals)
        Link(
            observable=self._calendar_navigation_model.show_calendar_list,
            handler=lambda _: self._view.show_calendar_list(),
            widget=self._view,
        )
        Link(
            observable=self._calendar_navigation_model.add_calendar,
            handler=lambda _: self._view.add_calendar(),
            widget=self._view,
        )
        Link(
            observable=self._calendar_navigation_model.edit_calendar,
            handler=lambda _: self._view.edit_calendar(),
            widget=self._view,
        )
