from PySide6.QtGui import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout

from clochette.application.store.CalendarConfigurationStore import CalendarConfigurationStore
from clochette.application.usecase.DeleteCalendarUseCase import DeleteCalendarUseCase
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.framework.qt.Link import Link
from clochette.presentation.settings.calendar.CalendarNavigationModel import CalendarNavigationModel
from clochette.presentation.widget.QList import QList, ListItem


class QCalendarList(QWidget):

    _list_calendar: QList[CalendarConfiguration]
    _calendar_configuration_store: CalendarConfigurationStore
    _calendar_navigation_model: CalendarNavigationModel
    _delete_calendar_usecase: DeleteCalendarUseCase

    def __init__(
        self,
        calendar_configuration_store: CalendarConfigurationStore,
        calendar_navigation_model: CalendarNavigationModel,
        delete_calendar_usecase: DeleteCalendarUseCase,
    ) -> None:
        super().__init__()

        self._calendar_configuration_store = calendar_configuration_store
        self._calendar_navigation_model = calendar_navigation_model
        self._delete_calendar_usecase = delete_calendar_usecase

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        self._list_calendar = QList()

        # Create the buttons layout
        buttons_layout = QVBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Create the Add button
        add_button = QPushButton(self.tr("Add"))
        add_button.clicked.connect(lambda: calendar_navigation_model.add_calendar.on_next(True))
        buttons_layout.addWidget(add_button)

        # Create the Edit button
        edit_button = QPushButton(self.tr("Edit"))
        edit_button.clicked.connect(self._edit_calendar)
        buttons_layout.addWidget(edit_button)

        # Create the Delete button
        delete_button = QPushButton(self.tr("Delete"))
        delete_button.clicked.connect(self._delete_calendar)
        buttons_layout.addWidget(delete_button)

        # Add the list widget and the buttons layout to the main layout
        main_layout.addWidget(self._list_calendar)
        main_layout.addLayout(buttons_layout)
        main_layout.addStretch()

        Link(
            observable=calendar_configuration_store.calendars,
            handler=self._set_calendars,
            widget=self,
        )

    def _set_calendars(self, calendars: list[CalendarConfiguration]):
        self._list_calendar.clear()
        for calendar in calendars:
            self._list_calendar.add(ListItem(calendar.name, calendar))

        calendar = self._list_calendar.get_selected_item()
        if calendars and calendar is None:
            self._list_calendar.setCurrentRow(0)

    def selected_calendar(self) -> CalendarConfiguration | None:
        return self._list_calendar.get_selected_item()

    def _edit_calendar(self):
        calendar = self._list_calendar.get_selected_item()
        if calendar is not None:
            self._calendar_navigation_model.edit_calendar.on_next(calendar)

    def _delete_calendar(self):
        calendar = self._list_calendar.get_selected_item()
        if calendar is not None:
            self._delete_calendar_usecase.delete_calendar(calendar).subscribe()
