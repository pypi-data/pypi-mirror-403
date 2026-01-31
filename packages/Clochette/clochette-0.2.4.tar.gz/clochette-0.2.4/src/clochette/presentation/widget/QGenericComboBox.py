from typing import Generic, TypeVar

from PySide6.QtWidgets import QComboBox

_T = TypeVar("_T")


class QGenericComboBox(QComboBox, Generic[_T]):
    """
    A generic combo box that manages items by key, allowing type-safe key-based access.
    Similar to QDynamicWidgetContainer but for combo box items.
    """

    _key_to_index: dict[_T, int]
    _index_to_key: dict[int, _T]

    def __init__(self):
        super().__init__()
        self._key_to_index = {}
        self._index_to_key = {}

    def add_item(self, key: _T, label: str) -> None:
        """Add an item with the given key and display label"""
        index = self.count()
        self._key_to_index[key] = index
        self._index_to_key[index] = key
        self.addItem(label)

    def clear_items(self) -> None:
        """Clear all items from the combo box"""
        self.clear()
        self._key_to_index.clear()
        self._index_to_key.clear()

    def set_items(self, items: list[tuple[_T, str]]) -> None:
        """Set all items at once, clearing existing items first"""
        self.clear_items()
        for key, label in items:
            self.add_item(key, label)

    def set_current_by_key(self, key: _T) -> None:
        """Set the current item by key"""
        if key in self._key_to_index:
            index = self._key_to_index[key]
            self.setCurrentIndex(index)

    def current_key(self) -> _T | None:
        """Get the key of the currently selected item, or None if no items"""
        if self.count() == 0:
            return None
        current_index = self.currentIndex()
        if current_index not in self._index_to_key:
            return None
        return self._index_to_key[current_index]
