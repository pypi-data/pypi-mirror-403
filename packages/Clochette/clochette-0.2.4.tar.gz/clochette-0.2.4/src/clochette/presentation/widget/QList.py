from dataclasses import dataclass
from typing import Generic, TypeVar

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QListWidget, QListWidgetItem

_T = TypeVar("_T")


@dataclass
class ListItem(Generic[_T]):
    display: str
    value: _T


class QList(QListWidget, Generic[_T]):
    def add(self, item: ListItem[_T]) -> None:
        list_item = QListWidgetItem(item.display)
        list_item.setData(Qt.ItemDataRole.UserRole, item)
        self.addItem(list_item)

    def add_all(self, items: list[ListItem[_T]]) -> None:
        self.clear()
        for item in items:
            self.add(item)

    def values(self) -> list[_T]:
        return [self.item(i).data(Qt.ItemDataRole.UserRole).value for i in range(self.count())]

    def get_selected_item(self) -> _T | None:
        current_row = self.currentRow()
        if current_row >= 0:
            return self.item(current_row).data(Qt.ItemDataRole.UserRole).value
        return None

    def delete_selected_item(self) -> None:
        current_row = self.currentRow()
        if current_row >= 0:
            self.takeItem(current_row)

    def sort_by_value(self):
        items_display = self._get_items_display()
        sorted_items = sorted(  # if the user passes values that cannot be sorted, it will fail
            items_display, key=lambda x: x.value  # pyright: ignore [reportArgumentType, reportCallIssue]
        )

        self.add_all(sorted_items)

    def unique(self):
        items_display = self._get_items_display()
        unique_data_dict = {}
        for item in items_display:
            unique_data_dict[item.value] = item

        self.add_all(list(unique_data_dict.values()))

    def _get_items_display(self) -> list[ListItem[_T]]:
        items = [self.item(i) for i in range(self.count())]
        return [item.data(Qt.ItemDataRole.UserRole) for item in items]
