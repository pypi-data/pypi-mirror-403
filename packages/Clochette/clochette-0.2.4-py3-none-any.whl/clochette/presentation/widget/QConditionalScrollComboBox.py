from PySide6.QtGui import QWheelEvent, Qt
from PySide6.QtWidgets import QComboBox


class QConditionalScrollComboBox(QComboBox):
    """
    https://stackoverflow.com/questions/3241830/qt-how-to-disable-mouse-scrolling-of-qcombobox
    """

    def __init__(self) -> None:
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, e: QWheelEvent) -> None:
        if self.hasFocus():
            return QComboBox.wheelEvent(self, e)
        return None
