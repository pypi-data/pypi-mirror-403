from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QLabel

from clochette.framework.qt.Signal import OutHollowSignal


class QClickableLabel(QLabel):
    on_clicked: OutHollowSignal

    def __init__(self, title: str):
        super().__init__(title)
        self.on_clicked = OutHollowSignal()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.on_clicked.send()
        QLabel.mousePressEvent(self, event)
