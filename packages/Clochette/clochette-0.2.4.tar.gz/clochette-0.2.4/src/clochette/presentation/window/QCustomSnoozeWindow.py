from PySide6.QtCore import QObject, QEvent
from PySide6.QtGui import Qt, QKeyEvent, QIcon
from PySide6.QtWidgets import QVBoxLayout
from reactivex import Observable
from typing_extensions import override

from clochette.domain.entity.delta.SnoozeDelta import SnoozeDelta
from clochette.framework.qt.Signal import OutSolidSignal, OutHollowSignal, InHollowSignal
from clochette.presentation.widget.QOkCancelButton import QOkCancelButton
from clochette.presentation.widget.QTimedeltaInput import QTimeDeltaInput
from clochette.presentation.window.QAbstractWindow import QAbstractWindow


class QCustomSnoozeWindow(QAbstractWindow):
    on_submitted: OutSolidSignal[SnoozeDelta]
    on_cancelled: OutHollowSignal
    show_window: InHollowSignal

    _input: QTimeDeltaInput

    def __init__(self, icon_window_observable: Observable[QIcon]) -> None:
        super().__init__(icon_window_observable, self.tr("Clochette - Snooze Selection"))

        self.on_submitted = OutSolidSignal()
        self.on_cancelled = OutHollowSignal()
        self.show_window = InHollowSignal(self._show)

        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self._input = QTimeDeltaInput()
        main_layout.addWidget(self._input)

        ok_cancel_button = QOkCancelButton()
        ok_cancel_button.on_cancel_clicked.link(self._on_cancel_clicked)
        ok_cancel_button.on_ok_clicked.link(self._on_ok_clicked)
        main_layout.addWidget(ok_cancel_button)

        self.installEventFilter(self)

        self.hide()

    @override
    def eventFilter(self, source: QObject, event: QEvent):
        if isinstance(event, QKeyEvent) and event.key() == Qt.Key.Key_Return:
            self._on_ok_clicked()

        return super().eventFilter(source, event)

    def _on_ok_clicked(self) -> None:
        self.on_submitted.send(SnoozeDelta(self._input.get_time_delta()))
        self._input.clear()
        self.hide()

    def _on_cancel_clicked(self) -> None:
        self.on_cancelled.send()
        self._input.clear()
        self.hide()

    def _show(self):
        super().show()
        self._input.setFocus()
