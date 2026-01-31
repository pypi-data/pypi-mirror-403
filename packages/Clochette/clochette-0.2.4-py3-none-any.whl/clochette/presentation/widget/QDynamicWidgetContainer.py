from typing import Generic, TypeVar

from PySide6.QtWidgets import QWidget, QVBoxLayout

_T = TypeVar("_T")


class QDynamicWidgetContainer(QWidget, Generic[_T]):
    """
    A generic container that manages widgets by key, displaying only one at a time.
    When showing a widget, it removes the previous one from the display.
    """

    _widgets: dict[_T, QWidget]
    _current_key: _T | None
    _layout: QVBoxLayout

    def __init__(self):
        super().__init__()
        self._widgets = {}
        self._current_key = None

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

    def add_widget(self, key: _T, widget: QWidget) -> None:
        """Register a widget with the given key. If this is the first widget, show it automatically."""
        self._widgets[key] = widget

        # Show the first widget automatically
        if len(self._widgets) == 1:
            self._current_key = key
            self.show_widget(key)

    def show_widget(self, key: _T) -> None:
        """Show the widget associated with the given key, hiding the current one"""
        if key not in self._widgets:
            return

        # Remove current widget if exists
        if self._current_key is not None:
            current_widget = self._widgets[self._current_key]
            self._layout.removeWidget(current_widget)
            current_widget.setParent(None)

        # Add and show new widget
        new_widget = self._widgets[key]
        self._layout.addWidget(new_widget)
        self._current_key = key

    def current_key(self) -> _T:
        """Get the key of the currently displayed widget"""
        if self._current_key is None:
            raise Exception("No widget was added")
        return self._current_key
