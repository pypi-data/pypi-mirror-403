from typing import TypeVar, Generic

from PySide6.QtWidgets import QGroupBox, QFormLayout, QPushButton, QLabel, QHBoxLayout

from clochette import log
from clochette.framework.qt.Signal import OutHollowSignal, InHollowSignal, InSolidSignal
from clochette.presentation.widget.QCheckBoxForm import QCheckBoxForm, CheckBoxItem
from clochette.presentation.widget.QWidgetLayout import QWidgetLayout
from clochette.provider.shared.dto.AuthCalendar import AuthCalendar

_T = TypeVar("_T", bound=AuthCalendar)


class QOAuth2Panel(QGroupBox, Generic[_T]):
    on_authenticate: OutHollowSignal

    set_authentication_failed: InSolidSignal[Exception]
    set_authentication_success: InHollowSignal
    clear: InHollowSignal
    set_error: InSolidSignal[str]
    set_selected_calendars: InSolidSignal[dict[_T, bool]]

    _auth_button: QPushButton
    _checkbox_form: QCheckBoxForm[_T]
    _error_label: QLabel

    def __init__(self):
        super().__init__("")

        self.on_authenticate = OutHollowSignal()
        self.set_authentication_failed = InSolidSignal(self._on_authentication_failed)
        self.set_authentication_success = InHollowSignal(self._on_authentication_success)
        self.clear = InHollowSignal(self._on_clear)
        self.set_error = InSolidSignal(self._on_set_error)
        self.set_selected_calendars = InSolidSignal(self._on_set_selected_calendars)

        layout = QFormLayout()
        self.setLayout(layout)

        button_layout = QWidgetLayout(QHBoxLayout())
        button_layout.add_stretch()

        self._auth_button = QPushButton(self.tr("Authenticate"))
        self._auth_button.clicked.connect(self._authenticate)
        button_layout.add_widget(self._auth_button)

        self._checkbox_form = QCheckBoxForm(self.tr("Calendars"))
        layout.addRow(self._checkbox_form)

        layout.addRow(button_layout)

        self._error_label = QLabel()
        self._error_label.setWordWrap(True)
        layout.addRow(self._error_label)

    def _authenticate(self):
        self._auth_button.setText(self.tr("Authenticating..."))
        self._auth_button.setEnabled(False)
        self.on_authenticate.send()

    def _on_authentication_failed(self, e: Exception):
        self._error_label.setStyleSheet("color: red;")
        self._error_label.setText(self.tr("Failed to authenticate: %s") % e)
        self._auth_button.setText(self.tr("Authenticate"))
        self._auth_button.setEnabled(True)
        log.error("Failed to authenticate", exc_info=e)

    def _on_authentication_success(self):
        self._error_label.setStyleSheet("color: green;")
        self._error_label.setText(self.tr("Authentication successful"))
        self._auth_button.setText(self.tr("Authenticate"))
        self._auth_button.setEnabled(True)

    def _on_clear(self):
        self._auth_button.setText(self.tr("Authenticate"))
        self._error_label.setText("")

    def _on_set_error(self, error: str) -> None:
        self._error_label.setStyleSheet("color: red;")
        self._error_label.setText(error)

    def _on_set_selected_calendars(self, calendars: dict[_T, bool]) -> None:
        items = {CheckBoxItem(cal.summary, cal): checked for cal, checked in calendars.items()}
        self._checkbox_form.set_checkbox_states(items)

    @property
    def selected_calendars(self) -> dict[CheckBoxItem[_T], bool]:
        return self._checkbox_form.get_checkbox_states()
