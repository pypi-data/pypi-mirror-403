from datetime import timedelta
from typing import TypeVar, Generic, Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QSizePolicy,
)

from clochette.application.utils.DeltaHelper import make_timedelta, delta_display
from clochette.domain.entity.delta.Delta import Delta
from clochette.framework.qt.Signal import OutSolidSignal
from clochette.presentation.widget.QIntLineEdit import QIntLineEdit
from clochette.presentation.widget.QTimeUnitComboBox import QTimeUnitCombobox

_T = TypeVar("_T", bound=Delta)


class QTimedeltaListWidget(QWidget, Generic[_T]):
    """Simple generic widget for managing a list of Delta objects. Uses signals for communication."""

    _list_widget: QListWidget
    _value_input: QIntLineEdit
    _unit_combo: QTimeUnitCombobox
    _delta_factory: Callable[[timedelta], _T]

    # Outbound: emit when user adds/removes deltas
    on_delta_updated: OutSolidSignal[list[_T]]

    def __init__(self, delta_factory: Callable[[timedelta], _T]):
        super().__init__()

        self._delta_factory = delta_factory

        self.on_delta_updated = OutSolidSignal()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(main_layout)

        # Set size policy to prevent vertical expansion
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # Input section at the top
        input_layout = QHBoxLayout()

        self._value_input = QIntLineEdit("0")
        self._value_input.setMaximumWidth(100)

        self._unit_combo = QTimeUnitCombobox()

        add_button = QPushButton(self.tr("Add"))
        add_button.setMaximumWidth(80)
        add_button.clicked.connect(self._add_timedelta)

        input_layout.addWidget(self._value_input)
        input_layout.addWidget(self._unit_combo)
        input_layout.addStretch()
        input_layout.addWidget(add_button)

        main_layout.addLayout(input_layout)

        # List section below
        self._list_widget = QListWidget()
        self._list_widget.setFixedHeight(120)
        main_layout.addWidget(self._list_widget)

    def set_deltas(self, deltas: list[_T]) -> None:
        """Handle incoming delta list update - repopulate the widget."""
        self._list_widget.clear()
        for delta in deltas:
            self._add_delta_row(delta)

    def _add_timedelta(self):
        """Add a new Delta from the input fields"""
        try:
            value = int(self._value_input.text())
            unit = self._unit_combo.time_unit()
            td = make_timedelta(value, unit)
            delta = self._delta_factory(td)
            self._add_delta_row(delta)

            # Reset input to default
            self._value_input.set_value(0)
            self._unit_combo.set_current_unit("minutes")

            self._emit_update()
        except (ValueError, AttributeError):
            pass  # Ignore invalid input

    def _add_delta_row(self, delta: _T):
        """Add a Delta row to the list"""
        item = QListWidgetItem()
        row_widget = self._create_delta_row_widget(delta)
        item.setSizeHint(row_widget.sizeHint())
        self._list_widget.addItem(item)
        self._list_widget.setItemWidget(item, row_widget)

    def _create_delta_row_widget(self, delta: _T) -> QWidget:
        """Create a widget for displaying a Delta with a delete button"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)

        display_text = delta_display(delta)
        display_label = QLabel(display_text)

        # Delete button
        delete_button = QPushButton(self.tr("Delete"))
        delete_button.setMaximumWidth(80)
        delete_button.clicked.connect(lambda checked=False, w=widget: self._delete_row_by_widget(w))

        layout.addWidget(display_label)
        layout.addStretch()
        layout.addWidget(delete_button)

        # Store the delta for retrieval
        widget.setProperty("delta", delta)

        return widget

    def _delete_row_by_widget(self, widget: QWidget):
        """Delete the row containing the given widget"""
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if self._list_widget.itemWidget(item) == widget:
                self._list_widget.takeItem(i)
                self._emit_update()
                break

    def _emit_update(self):
        """Collect all Deltas and emit update signal"""
        deltas = self.get_deltas()
        self.on_delta_updated.send(deltas)

    def get_deltas(self) -> list[_T]:
        """Get all Delta objects from the list"""
        deltas = []
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            widget = self._list_widget.itemWidget(item)
            if widget:
                delta = widget.property("delta")
                if delta is not None:
                    deltas.append(delta)
        return deltas
