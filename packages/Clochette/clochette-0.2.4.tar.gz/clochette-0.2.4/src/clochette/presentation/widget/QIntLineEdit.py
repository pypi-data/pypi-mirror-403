from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QLineEdit


class QIntLineEdit(QLineEdit):

    def __init__(self, placeholder: str | None = None, default_value: int | None = None):
        super().__init__()

        self.setValidator(QIntValidator())

        if placeholder is not None:
            self.setPlaceholderText(placeholder)

        if default_value is not None:
            self.setText(str(default_value))

    def get_value(self) -> int:
        return int(self.text())

    def set_value(self, value: int):
        self.setText(str(value))
