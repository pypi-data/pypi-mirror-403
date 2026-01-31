from typing import Generic, TypeVar

from PySide6.QtWidgets import QComboBox

_T = TypeVar("_T")


class QTypedComboBox(QComboBox, Generic[_T]):
    """
    A generic combobox that stores typed values alongside display text.
    Each item has a display value (shown to user) and a typed value (stored data).
    """

    def __init__(self):
        super().__init__()

    def add_item(self, display_value: str, value: _T) -> None:
        """Add an item with display text and associated typed value"""
        self.addItem(display_value, value)

    def add_items(self, items: list[tuple[str, _T]]) -> None:
        """Add multiple items at once. Each item is a tuple of (display_value, value)"""
        for display_value, value in items:
            self.add_item(display_value, value)

    def get_current_value(self) -> _T | None:
        """Get the typed value of the currently selected item"""
        return self.currentData()

    def set_current_by_value(self, value: _T) -> bool:
        """
        Set the current item by its typed value.
        Returns True if found and set, False otherwise.
        """
        for i in range(self.count()):
            if self.itemData(i) == value:
                self.setCurrentIndex(i)
                return True
        return False

    def set_current_by_display(self, display_value: str) -> bool:
        """
        Set the current item by its display text.
        Returns True if found and set, False otherwise.
        """
        for i in range(self.count()):
            if self.itemText(i) == display_value:
                self.setCurrentIndex(i)
                return True
        return False
