from PySide6.QtCore import QSize, QPoint, QRect
from PySide6.QtGui import QPaintEvent
from PySide6.QtWidgets import QTabBar, QStylePainter, QStyle, QStyleOptionTab, QTabWidget


class _QStyleOptionTab(QStyleOptionTab):
    # https://stackoverflow.com/questions/50578661/how-to-implement-vertical-tabs-in-qt
    rect: QRect


class QWestTabBar(QTabBar):
    """Custom tab bar for vertical tabs with horizontal text"""

    def tabSizeHint(self, index: int) -> QSize:
        s = super().tabSizeHint(index)
        s.transpose()
        return s

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QStylePainter(self)
        opt = _QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QStyle.ControlElement.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            s.transpose()
            r = QRect(QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QStyle.ControlElement.CE_TabBarTabLabel, opt)
            painter.restore()


class QWestTabWidget(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setTabBar(QWestTabBar())
        self.setTabPosition(QTabWidget.TabPosition.West)
