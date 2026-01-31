from enum import Enum

from PySide6.QtWidgets import QWidget, QVBoxLayout

from clochette.domain.entity.configuration.CalendarConfiguration import (
    CalendarConfiguration,
)
from clochette.presentation.settings.calendar.tabs.QCalendarConfigurationComponent import (
    QCalendarConfigurationComponent,
)
from clochette.presentation.widget.QCalendarList import QCalendarList
from clochette.presentation.widget.QDynamicWidgetContainer import (
    QDynamicWidgetContainer,
)
from clochette.presentation.widget.QTitle import QTitle
from clochette.presentation.widget.QWidgetLayout import QWidgetLayout


class CalendarView(Enum):
    """Enum for the different calendar setting views"""

    LIST = "list"
    CONFIGURATION = "configuration"


class QCalendarSettingsView(QWidget):
    """Simple view widget for calendar settings with list and configuration panels"""

    _container: QDynamicWidgetContainer[CalendarView]
    _calendar_list: QCalendarList

    def __init__(
        self,
        calendar_configuration_component: QCalendarConfigurationComponent,
        calendar_list: QCalendarList,
    ):
        super().__init__()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self._container = QDynamicWidgetContainer[CalendarView]()
        main_layout.addWidget(self._container)

        # calendar list
        calendar_widget = QVBoxLayout()
        calendar_widget.addWidget(
            QTitle(
                self.tr("Calendars Source"),
                self.tr("Tell Clochette how to access your calendars"),
            )
        )

        self._calendar_list = calendar_list
        calendar_widget.addWidget(self._calendar_list)
        calendar_widget.addStretch()

        cal_list_widget = QWidget()
        cal_list_widget.setContentsMargins(0, 0, 0, 0)
        cal_list_widget.setLayout(calendar_widget)
        self._container.add_widget(CalendarView.LIST, cal_list_widget)

        # unified configuration panel (authentication + settings)
        configuration_widget = QWidgetLayout(QVBoxLayout())
        configuration_widget.add_widget(calendar_configuration_component.view())
        self._container.add_widget(CalendarView.CONFIGURATION, configuration_widget)

        main_layout.addStretch()

    def show_calendar_list(self):
        """Show the calendar list view"""
        self._container.show_widget(CalendarView.LIST)

    def add_calendar(self):
        """Show the add calendar configuration view"""
        self._container.show_widget(CalendarView.CONFIGURATION)

    def edit_calendar(self):
        """Show the edit calendar configuration view"""
        self._container.show_widget(CalendarView.CONFIGURATION)

    def selected_calendar(self) -> CalendarConfiguration | None:
        return self._calendar_list.selected_calendar()

    @property
    def calendar_list(self) -> QCalendarList:
        """Expose the calendar list widget for component access"""
        return self._calendar_list
