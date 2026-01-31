from PySide6.QtWidgets import QFormLayout, QLineEdit, QCheckBox, QPushButton, QLabel, QHBoxLayout, QGroupBox

from clochette.framework.qt.Signal import OutHollowSignal, InHollowSignal, InSolidSignal
from clochette.presentation.widget.QWidgetLayout import QWidgetLayout


class QBasicAuthView(QGroupBox):

    on_authenticate: OutHollowSignal

    set_authentication_failed: InSolidSignal[Exception]
    set_authentication_success: InHollowSignal
    clear: InHollowSignal
    set_url: InSolidSignal[str]
    set_username: InSolidSignal[str]
    set_password: InSolidSignal[str]
    set_error: InSolidSignal[str]

    _url: QLineEdit
    _username: QLineEdit
    _password: QLineEdit
    _auth_button: QPushButton
    _error_label: QLabel

    def __init__(self):
        super().__init__(self.tr("Basic Authentication Options"))

        self.on_authenticate = OutHollowSignal()

        self.set_authentication_failed = InSolidSignal(self._authentication_failed)
        self.set_authentication_success = InHollowSignal(self._authentication_success)
        self.clear = InHollowSignal(self._clear)
        self.set_url = InSolidSignal(self._set_url)
        self.set_username = InSolidSignal(self._set_username)
        self.set_password = InSolidSignal(self._set_password)
        self.set_error = InSolidSignal(self._set_error)

        layout = QFormLayout()
        self.setLayout(layout)

        self._url = QLineEdit()
        self._url.setPlaceholderText(self.tr("Enter URL"))
        layout.addRow(self.tr("URL:"), self._url)

        self._username = QLineEdit()
        self._username.setPlaceholderText(self.tr("Enter username"))
        layout.addRow(self.tr("Username:"), self._username)

        self._password = QLineEdit()
        self._password.setPlaceholderText(self.tr("Enter password"))
        layout.addRow(self.tr("Password:"), self._password)
        self._password.setEchoMode(QLineEdit.EchoMode.Password)

        show_password_checkbox = QCheckBox(self.tr("Show Password"))
        show_password_checkbox.stateChanged.connect(
            lambda state: (
                self._password.setEchoMode(QLineEdit.EchoMode.Normal)
                if state
                else self._password.setEchoMode(QLineEdit.EchoMode.Password)
            )
        )

        layout.addRow("", show_password_checkbox)

        button_layout = QWidgetLayout(QHBoxLayout())
        button_layout.add_stretch()

        self._auth_button = QPushButton(self.tr("Authenticate"))
        self._auth_button.clicked.connect(self._authenticate)
        button_layout.add_widget(self._auth_button)

        layout.addRow(button_layout)

        self._error_label = QLabel()
        self._error_label.setWordWrap(True)
        layout.addRow(self._error_label)

    def _authenticate(self):
        self._auth_button.setText(self.tr("Authenticating..."))
        self._auth_button.setEnabled(False)
        self.on_authenticate.send()

    def _authentication_failed(self, e: Exception):
        self._error_label.setStyleSheet("color: red;")
        self._error_label.setText(self.tr("Failed to authenticate: %s") % e)
        self._auth_button.setText(self.tr("Authenticate"))
        self._auth_button.setEnabled(True)

    def _authentication_success(self):
        self._error_label.setStyleSheet("color: green;")
        self._error_label.setText(self.tr("Authentication successful"))
        self._auth_button.setText(self.tr("Authenticate"))
        self._auth_button.setEnabled(True)

    def _set_url(self, url: str) -> None:
        self._url.setText(url)

    def _set_username(self, username: str) -> None:
        self._username.setText(username)

    def _set_password(self, password: str) -> None:
        self._password.setText(password)

    def _set_error(self, error: str) -> None:
        self._error_label.setText(error)

    def _clear(self):
        self._url.setText("")
        self._username.setText("")
        self._password.setText("")
        self._error_label.setText("")

    @property
    def url(self) -> str:
        return self._url.text()

    @property
    def username(self) -> str:
        return self._username.text()

    @property
    def password(self) -> str:
        return self._password.text()

    @property
    def error(self) -> str:
        return self._error_label.text()
