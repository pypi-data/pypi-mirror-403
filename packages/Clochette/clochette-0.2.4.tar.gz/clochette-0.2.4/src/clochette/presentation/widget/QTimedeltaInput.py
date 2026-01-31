from datetime import timedelta

from PySide6.QtWidgets import QWidget, QHBoxLayout

from clochette.application.utils.DeltaHelper import make_timedelta
from clochette.presentation.widget.QIntLineEdit import QIntLineEdit
from clochette.presentation.widget.QTimeUnitComboBox import QTimeUnitCombobox


class QTimeDeltaInput(QWidget):

    _time_value: QIntLineEdit
    _time_unit: QTimeUnitCombobox

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.setContentsMargins(0, 0, 0, 0)

        self._time_value = QIntLineEdit(self.tr("Enter a number"))
        layout.addWidget(self._time_value)

        self._time_unit = QTimeUnitCombobox()
        layout.addWidget(self._time_unit)

    def get_time_delta(self) -> timedelta:
        return make_timedelta(int(self._time_value.text()), self._time_unit.time_unit())

    def set_timedelta(self, delta: timedelta):
        seconds = delta.total_seconds()
        if seconds % 86400 == 0:
            self._time_value.set_value(int(seconds / 86400))
            self._time_unit.set_current_unit("days")
        elif seconds % 1440 == 0:
            self._time_value.set_value(int(seconds / 1440))
            self._time_unit.set_current_unit("hours")
        elif seconds % 60 == 0:
            self._time_value.set_value(int(seconds / 60))
            self._time_unit.set_current_unit("minutes")

    def clear(self):
        self._time_value.setText("")
        self._time_unit.clear()

    def setFocus(self, /) -> None:  # pyright: ignore [reportIncompatibleMethodOverride]
        self._time_value.setFocus()
