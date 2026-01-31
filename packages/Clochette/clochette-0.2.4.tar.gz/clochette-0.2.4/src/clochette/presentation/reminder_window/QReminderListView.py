from PySide6.QtGui import QFont, Qt
from PySide6.QtWidgets import QWidget, QTableWidget, QVBoxLayout, QPushButton, QLabel, QHeaderView

from clochette.application.store.GeneralConfigurationStore import GeneralConfigurationStore
from clochette.domain.entity.EventDetails import EventDetails
from clochette.domain.entity.Occurrence import Occurrence
from clochette.domain.entity.delta.SnoozeDelta import SnoozeDelta
from clochette.framework.qt.Signal import OutSolidSignal, InSolidSignal
from clochette.infrastructure.clock.DateTimeUtils import DateTimeUtils
from clochette.application.i18n.LangHelper import natural_day
from clochette.presentation.reminder_window.QSnoozeComboBoxComponent import QSnoozeComboBoxComponent
from clochette.presentation.theme.ThemeService import ThemeService
from clochette.presentation.widget.QClickableLabel import QClickableLabel


class QReminderListView(QWidget):
    """Pure view component for displaying a list of reminders."""

    on_dismiss_clicked: OutSolidSignal[Occurrence]
    on_snoozed_clicked: OutSolidSignal[tuple[Occurrence, SnoozeDelta]]
    on_details_clicked: OutSolidSignal[tuple[Occurrence, EventDetails]]

    set_occurrences: InSolidSignal[list[tuple[Occurrence, EventDetails]]]

    _table: QTableWidget
    _theme_service: ThemeService
    _general_configuration_store: GeneralConfigurationStore

    def __init__(self, theme_service: ThemeService, general_configuration_store: GeneralConfigurationStore) -> None:
        super().__init__()

        self.on_dismiss_clicked = OutSolidSignal()
        self.on_snoozed_clicked = OutSolidSignal()
        self.on_details_clicked = OutSolidSignal()

        self.set_occurrences = InSolidSignal(self._set_occurrences)

        self._theme_service = theme_service
        self._general_configuration_store = general_configuration_store

        self._table = self._make_table()
        layout = QVBoxLayout()
        layout.addWidget(self._table)
        self.setLayout(layout)
        self.setMinimumHeight(240)

    def _make_table(self) -> QTableWidget:
        table = QTableWidget(3, 1)

        horizontal_header = table.horizontalHeader()
        vertical_header = table.verticalHeader()

        horizontal_header.setVisible(False)
        vertical_header.setVisible(False)

        table.setShowGrid(False)
        table.setMinimumWidth(580)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return table

    def _refresh_table(self) -> None:
        self._table.resizeColumnsToContents()
        self._table.resizeRowsToContents()

        horizontal_header = self._table.horizontalHeader()
        horizontal_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

    def _remove_all(self) -> None:
        self._table.setRowCount(0)

    def _set_occurrences(self, occurrences: list[tuple[Occurrence, EventDetails]]) -> None:
        self._remove_all()
        for index, (occurrence, event_details) in enumerate(occurrences):
            self._add_occurrence(index, occurrence, event_details)

        self._refresh_table()

    def _add_occurrence(self, index: int, occurrence: Occurrence, event_details: EventDetails) -> None:
        self._table.setRowCount(index + 1)
        self._table.setColumnCount(3)

        summary_widget = self._make_summary_cell(occurrence, event_details)
        self._table.setCellWidget(index, 0, summary_widget)
        self._table.setCellWidget(index, 1, self._make_snooze_button(occurrence))
        self._table.setCellWidget(index, 2, self._make_dismiss_button(occurrence))

    def _make_snooze_button(self, occurrence: Occurrence) -> QWidget:
        widget = QWidget()
        vbox = QVBoxLayout()
        widget.setLayout(vbox)

        is_date = DateTimeUtils.is_date(occurrence.trigger.start)
        snooze_component = QSnoozeComboBoxComponent(self._theme_service, self._general_configuration_store, is_date)
        snooze_component.on_snooze_selected.link(lambda delta: self.on_snoozed_clicked.send((occurrence, delta)))
        vbox.addWidget(snooze_component.view())
        return widget

    def _make_dismiss_button(self, occurrence: Occurrence) -> QWidget:
        widget = QWidget()
        vbox = QVBoxLayout()
        widget.setLayout(vbox)

        dismiss = QPushButton(self.tr("Dismiss"))
        dismiss.clicked.connect(lambda: self.on_dismiss_clicked.send(occurrence))

        vbox.addWidget(dismiss)
        return widget

    def _make_summary_cell(self, occurrence: Occurrence, event_details: EventDetails) -> QWidget:
        vbox_layout = QVBoxLayout()

        if DateTimeUtils.is_date(occurrence.trigger.start):
            date = natural_day(occurrence.trigger.start)
            time = self.tr("%s all day") % date
        elif DateTimeUtils.is_datetime(occurrence.trigger.start):
            date = natural_day(occurrence.trigger.start.date())
            formated_time = DateTimeUtils.format_time_locale(occurrence.trigger.start)
            time = f"{date} {formated_time}"
        else:
            raise Exception("Occurrence trigger start is neither of type date or time")

        # Create the summary label
        summary_label = QLabel(event_details.summary)
        bold_font = QFont()
        bold_font.setBold(True)
        summary_label.setFont(bold_font)

        # Create the time label
        time_label = QLabel(time)

        # Create the details label
        details_label = QClickableLabel(self.tr("Details"))
        details_label.setStyleSheet("color: blue; text-decoration: underline;")
        details_label.setCursor(Qt.CursorShape.PointingHandCursor)

        details_label.on_clicked.link(lambda: self.on_details_clicked.send((occurrence, event_details)))

        # Add the labels to the layout
        vbox_layout.addWidget(summary_label)
        vbox_layout.addWidget(time_label)
        vbox_layout.addWidget(details_label)

        # Create a widget to hold the layout
        container = QWidget()
        container.setLayout(vbox_layout)
        return container
