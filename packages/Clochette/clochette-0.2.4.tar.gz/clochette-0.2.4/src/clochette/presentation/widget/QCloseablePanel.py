from PySide6.QtCore import QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QStyle, QHBoxLayout

from clochette.framework.qt.Signal import OutHollowSignal


class QCloseablePanel(QWidget):
    on_close_clicked: OutHollowSignal

    def __init__(self, hidden: bool) -> None:
        super().__init__()

        self.on_close_clicked = OutHollowSignal()

        self._layout = QVBoxLayout()

        close_button = QPushButton()
        style = self.style()
        if style:
            close_icon = style.standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton)
            close_button.setIcon(close_icon)
            close_button.setIconSize(QSize(16, 16))
            close_button.setFixedSize(QSize(16, 16))

        close_button.clicked.connect(self._on_close_clicked)

        top_panel_layout = QHBoxLayout()
        top_panel_layout.addStretch(1)
        top_panel_layout.addWidget(close_button)

        self._layout.addLayout(top_panel_layout)

        self.setLayout(self._layout)

        if hidden:
            self.hide()

    def _on_close_clicked(self) -> None:
        self.hide()
        self.adjustSize()
        self.on_close_clicked.send()

    def addWidget(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)
