from datetime import datetime, date

from PySide6.QtWidgets import QTabWidget, QLineEdit, QTextEdit, QWidget, QFormLayout, QVBoxLayout

from clochette.domain.entity.Contact import Contact
from clochette.domain.entity.EventDetails import EventDetails
from clochette.domain.entity.Occurrence import Occurrence
from clochette.infrastructure.clock.DateTimeUtils import DateTimeUtils
from clochette.framework.qt.Signal import InSolidSignal


class QEventDetailsView(QTabWidget):
    display: InSolidSignal[tuple[Occurrence, EventDetails]]

    _summary_field: QLineEdit
    _start_field: QLineEdit
    _end_field: QLineEdit
    _description_field: QTextEdit
    _location_field: QLineEdit
    _organizer_field: QLineEdit
    _attendees_field: QTextEdit
    _raw_event_field: QTextEdit

    def __init__(self) -> None:
        super().__init__()

        self.display = InSolidSignal(self._display)

        # tabs
        tab1 = QWidget()
        tab2 = QWidget()

        self.addTab(tab1, self.tr("Event Details"))
        self.addTab(tab2, self.tr("Raw Event"))

        # tab 1
        self._form_layout = QFormLayout()

        self._summary_field = self._make_readonly_line_edit()
        self._form_layout.addRow(self.tr("Summary:"), self._summary_field)

        self._start_field = self._make_readonly_line_edit()
        self._form_layout.addRow(self.tr("Start:"), self._start_field)

        self._end_field = self._make_readonly_line_edit()
        self._form_layout.addRow(self.tr("End:"), self._end_field)

        self._description_field = self._make_readonly_text_edit()
        self._form_layout.addRow(self.tr("Description:"), self._description_field)

        self._location_field = self._make_readonly_line_edit()
        self._form_layout.addRow(self.tr("Location:"), self._location_field)

        self._organizer_field = self._make_readonly_line_edit()
        self._form_layout.addRow(self.tr("Organizer:"), self._organizer_field)

        self._attendees_field = self._make_readonly_text_edit()
        self._form_layout.addRow(self.tr("Attendees:"), self._attendees_field)

        # tab 2
        self._raw_event_field = QTextEdit()
        self._raw_event_field.setReadOnly(True)

        raw_event_layout = QVBoxLayout()
        raw_event_layout.addWidget(self._raw_event_field)

        tab1.setLayout(self._form_layout)
        tab2.setLayout(raw_event_layout)

    def _display(self, value: tuple[Occurrence, EventDetails]) -> None:
        occurrence, event_details = value
        # tab 1
        self._summary_field.setText(event_details.summary)

        start = self._format_date_or_time(occurrence.trigger.start)
        self._start_field.setText(start)

        # Calculate end date by adding duration to start
        end = self._format_date_or_time(occurrence.trigger.start + event_details.duration)
        self._end_field.setText(end)

        if event_details.description is not None:
            self._description_field.setText(event_details.description)
            self._form_layout.setRowVisible(3, True)
        else:
            self._form_layout.setRowVisible(3, False)

        if event_details.location is not None:
            self._location_field.setText(event_details.location)
            self._form_layout.setRowVisible(4, True)
        else:
            self._location_field.hide()
            self._form_layout.setRowVisible(4, False)

        if event_details.organizer is not None:
            content = self._format_contact(event_details.organizer)
            self._organizer_field.setText(content)
            self._form_layout.setRowVisible(5, True)
        else:
            self._form_layout.setRowVisible(5, False)

        if event_details.attendees:
            formatted_attendees = [self._format_contact(attendee) for attendee in event_details.attendees]
            content = "\n".join(formatted_attendees)
            self._attendees_field.setText(content)
            self._form_layout.setRowVisible(6, True)
        else:
            self._form_layout.setRowVisible(6, False)

        # tab 2
        self._raw_event_field.setPlainText(event_details.raw)
        self.adjustSize()

    def _format_date_or_time(self, value: date | datetime) -> str:
        if DateTimeUtils.is_date(value):
            return DateTimeUtils.format_date_locale(value)
        elif DateTimeUtils.is_datetime(value):
            return DateTimeUtils.format_date_time_locale(value)
        else:
            raise Exception("Value is neither of type date or time")

    def _format_contact(self, contact: Contact) -> str:
        return f"{contact.cn} <{contact.mailto}>"

    def _make_readonly_line_edit(self) -> QLineEdit:
        widget = QLineEdit()
        widget.setReadOnly(True)
        return widget

    def _make_readonly_text_edit(self) -> QTextEdit:
        widget = QTextEdit()
        widget.setReadOnly(True)
        return widget
