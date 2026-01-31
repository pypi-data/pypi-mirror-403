from PySide6.QtWidgets import QWidget

from clochette.presentation.widget.QVTabBar import QWestTabWidget


class QSettingsPanel(QWestTabWidget):

    def add_item(self, title: str, widget: QWidget):
        """Add a new item to the settings panel"""
        widget.setContentsMargins(5, 0, 5, 0)
        self.addTab(widget, title)
