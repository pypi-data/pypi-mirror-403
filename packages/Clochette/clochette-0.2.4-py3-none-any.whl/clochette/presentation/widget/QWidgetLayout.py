from PySide6.QtWidgets import QWidget, QLayout, QBoxLayout

from clochette import log


class QWidgetLayout(QWidget):

    _layout: QLayout

    def __init__(self, layout: QLayout):
        super().__init__()
        self._layout = layout

        self.setLayout(layout)

    def add_widget(self, widget: QWidget):
        self._layout.addWidget(widget)

    def add_layout(self, layout: QLayout):
        if isinstance(self._layout, QBoxLayout):
            self._layout.addLayout(layout)
        else:
            log.error("Cannot add a layout to a non QBoxLayout")

    def add_stretch(self, stretch: int | None = None):
        if isinstance(self._layout, QBoxLayout):
            if stretch is None:
                self._layout.addStretch()
            else:
                self._layout.addStretch(stretch)
        else:
            log.error("Cannot add a spacer to a non QBoxLayout")
