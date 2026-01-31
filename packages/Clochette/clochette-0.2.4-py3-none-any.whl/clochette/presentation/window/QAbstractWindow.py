from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget
from reactivex import Observable

from clochette.framework.qt.Link import Link


class QAbstractWindow(QWidget):
    def __init__(self, icon_window_observable: Observable[QIcon], title: str):
        super().__init__()

        # Subscribe to icon changes with thread-safe signal
        Link(
            observable=icon_window_observable,
            handler=lambda icon: self.setWindowIcon(icon),
            widget=self,
        )

        self.setWindowTitle(title)
