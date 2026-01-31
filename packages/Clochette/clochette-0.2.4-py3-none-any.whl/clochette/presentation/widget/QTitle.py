from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

from clochette.presentation.widget.QHLine import QHLine


class QTitle(QWidget):

    _title_label: QLabel

    def __init__(self, title: str, subtitle: str | None = None):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 5, 0, 0)

        self._title_label = QLabel(title)

        title_font = QFont()
        title_font.setPointSize(12)
        self._title_label.setFont(title_font)

        layout.addWidget(self._title_label)

        if subtitle is not None:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("color: #555555;")
            layout.addWidget(subtitle_label)

        layout.addWidget(QHLine())

    def set_title(self, title: str) -> None:
        """Update the title text dynamically"""
        self._title_label.setText(title)
