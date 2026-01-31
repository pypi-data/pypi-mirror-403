from PySide6.QtWidgets import QGroupBox, QFormLayout, QLineEdit, QPushButton, QLabel, QHBoxLayout

from clochette.framework.qt.Signal import OutHollowSignal, InHollowSignal, InSolidSignal
from clochette.presentation.widget.QWidgetLayout import QWidgetLayout


class QPublicAuthPanel(QGroupBox):

    on_authenticate: OutHollowSignal

    set_authentication_failed: InSolidSignal[Exception]
    set_authentication_success: InHollowSignal
    clear: InHollowSignal
    set_url: InSolidSignal[str]
    set_error: InSolidSignal[str]

    _url: QLineEdit
    _auth_button: QPushButton
    _error_label: QLabel

    def __init__(self):
        super().__init__(self.tr("Public URL Options"))

        self.on_authenticate = OutHollowSignal()

        self.set_authentication_failed = InSolidSignal(self._authentication_failed)
        self.set_authentication_success = InHollowSignal(self._authentication_success)
        self.clear = InHollowSignal(self._clear)
        self.set_url = InSolidSignal(self._set_url)
        self.set_error = InSolidSignal(self._set_error)

        layout = QFormLayout()
        self.setLayout(layout)

        self._url = QLineEdit()
        self._url.setPlaceholderText(self.tr("Enter URL"))
        layout.addRow(self.tr("URL:"), self._url)

        button_layout = QWidgetLayout(QHBoxLayout())
        button_layout.add_stretch()

        self._auth_button = QPushButton(self.tr("Test"))
        self._auth_button.clicked.connect(self._authenticate)
        button_layout.add_widget(self._auth_button)

        layout.addRow(button_layout)

        self._error_label = QLabel()
        self._error_label.setWordWrap(True)
        layout.addRow(self._error_label)

    def _authenticate(self):
        self._auth_button.setText(self.tr("Downloading..."))
        self._auth_button.setEnabled(False)
        self.on_authenticate.send()

    def _authentication_failed(self, e: Exception):
        self._error_label.setStyleSheet("color: red;")
        self._error_label.setText(self.tr("Failed to access: %s") % e)
        self._auth_button.setText(self.tr("Test"))
        self._auth_button.setEnabled(True)

    def _authentication_success(self):
        self._error_label.setStyleSheet("color: green;")
        self._error_label.setText(self.tr("Access successful"))
        self._auth_button.setText(self.tr("Test"))
        self._auth_button.setEnabled(True)

    def _set_url(self, url: str) -> None:
        self._url.setText(url)

    def _set_error(self, error: str) -> None:
        self._error_label.setText(error)

    def _clear(self):
        self._url.setText("")
        self._auth_button.setText(self.tr("Test"))
        self._error_label.setText("")

    @property
    def url(self) -> str:
        return self._url.text()

    @property
    def error(self) -> str:
        return self._error_label.text()
