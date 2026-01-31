from dataclasses import dataclass
from typing import TypeVar, Generic

from PySide6.QtWidgets import QCheckBox, QFormLayout, QGroupBox

_T = TypeVar("_T")


@dataclass(frozen=True, eq=True)
class CheckBoxItem(Generic[_T]):
    display: str
    id: _T


class QCheckBoxForm(QGroupBox, Generic[_T]):
    _layout: QFormLayout
    _checkboxes: dict[CheckBoxItem[_T], QCheckBox]

    def __init__(self, title: str):
        super().__init__(title)

        self._checkboxes = {}

        self._layout = QFormLayout()
        self.setLayout(self._layout)

    def get_checkbox_states(self) -> dict[CheckBoxItem[_T], bool]:
        return {item: checkbox.isChecked() for item, checkbox in self._checkboxes.items()}

    def set_checkbox_states(self, checkbox_states: dict[CheckBoxItem[_T], bool]) -> None:
        self._clear()

        for item, state in checkbox_states.items():
            checkbox = QCheckBox(item.display)
            checkbox.setChecked(state)
            self._layout.addRow(checkbox)
            self._checkboxes[item] = checkbox

        self.adjustSize()

    def _clear(self):
        for _ in self._checkboxes:
            self._layout.removeItem(self._layout.itemAt(0))
