from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton

from clochette.framework.qt.Signal import OutHollowSignal


class QOkCancelButton(QWidget):
    on_ok_clicked: OutHollowSignal
    on_cancel_clicked: OutHollowSignal

    _ok_button: QPushButton
    _cancel_button: QPushButton

    def __init__(self, ok_title: str | None = None):
        super().__init__()

        self.on_ok_clicked = OutHollowSignal()
        self.on_cancel_clicked = OutHollowSignal()

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self._ok_button = QPushButton(ok_title or self.tr("OK"))
        self._ok_button.clicked.connect(self.on_ok_clicked.send)

        self._cancel_button = QPushButton(self.tr("Cancel"))
        self._cancel_button.clicked.connect(self.on_cancel_clicked.send)

        main_layout.addStretch()
        main_layout.addWidget(self._cancel_button)
        main_layout.addWidget(self._ok_button)

    def set_enabled_ok(self, enable: bool):
        self._ok_button.setEnabled(enable)

    def set_text_ok(self, text: str):
        self._ok_button.setText(text)
