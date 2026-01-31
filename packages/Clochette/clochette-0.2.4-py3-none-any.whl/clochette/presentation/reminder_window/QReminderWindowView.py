from typing import override

from PySide6.QtGui import QCloseEvent
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QVBoxLayout, QLayout, QHBoxLayout, QPushButton

from clochette import log
from clochette.domain.entity.EventDetails import EventDetails
from clochette.domain.entity.Occurrence import Occurrence
from clochette.domain.entity.delta.SnoozeDelta import SnoozeDelta
from clochette.framework.qt.Signal import OutSolidSignal, OutHollowSignal
from clochette.presentation.reminder_window.QEventDetailsView import QEventDetailsView
from clochette.presentation.reminder_window.QReminderListComponent import (
    QReminderListComponent,
)
from clochette.presentation.theme.ThemeService import ThemeService
from clochette.presentation.widget.QCloseablePanel import QCloseablePanel
from clochette.presentation.window.QAbstractWindow import QAbstractWindow


class QReminderWindowView(QAbstractWindow):
    on_dismiss_clicked: OutSolidSignal[Occurrence]
    on_dismiss_all_clicked: OutHollowSignal
    on_snooze_clicked: OutSolidSignal[tuple[Occurrence, SnoozeDelta]]

    _reminder_list: QReminderListComponent
    _closeable_details_panel: QCloseablePanel
    _details_panel: QEventDetailsView

    def __init__(
        self, theme_service: ThemeService, reminder_list: QReminderListComponent
    ) -> None:
        super().__init__(theme_service.icon_window, self.tr("Clochette - New Event"))

        self.on_dismiss_clicked = OutSolidSignal()
        self.on_dismiss_all_clicked = OutHollowSignal()
        self.on_snooze_clicked = OutSolidSignal()

        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        self._reminder_list = reminder_list

        self._details_panel = QEventDetailsView()
        self._closeable_details_panel = QCloseablePanel(True)
        self._closeable_details_panel.addWidget(self._details_panel)
        self._closeable_details_panel.on_close_clicked.link(
            self._on_details_panel_closed
        )

        self._reminder_list.view().on_snoozed_clicked.link(
            lambda o: self.on_snooze_clicked.send(o)
        )
        self._reminder_list.view().on_dismiss_clicked.link(
            lambda o: self.on_dismiss_clicked.send(o)
        )
        self._reminder_list.view().on_details_clicked.link(self._on_details_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self._reminder_list.view())
        layout.addLayout(self._make_button_layout())
        layout.addWidget(self._closeable_details_panel)

        self.setLayout(layout)

    def _make_button_layout(self) -> QLayout:
        button_layout = QHBoxLayout()

        dismiss_all_button = QPushButton(self.tr("Dismiss All Reminders"))
        dismiss_all_button.clicked.connect(self._dismiss_all)

        button_layout.addWidget(dismiss_all_button)
        button_layout.addStretch(1)

        return button_layout

    def update_occurrences(
        self, occurrences_with_details: list[tuple[Occurrence, EventDetails]]
    ) -> None:
        if occurrences_with_details:
            self._reminder_list.update_occurrences(occurrences_with_details)
            self.adjustSize()

    def display_window(self, should_show: bool) -> None:
        """Show or hide the reminder window. Thread-safe when called via Link."""
        if should_show:
            log.info("Showing the reminder window")
            self.show()
        else:
            log.debug("Hiding the reminder window")
            self.hide()

    def _dismiss_all(self) -> None:
        self.on_dismiss_all_clicked.send()

    def _on_details_panel_closed(self) -> None:
        self.adjustSize()

    def _on_details_clicked(self, value: tuple[Occurrence, EventDetails]) -> None:
        self._details_panel.display(value)
        self._closeable_details_panel.show()
        self._closeable_details_panel.adjustSize()
        self.adjustSize()

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
