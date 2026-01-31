from typing import Callable, TypeVar, Generic

from PySide6.QtCore import Signal, QObject

_T = TypeVar("_T")


class _SolidSignal(QObject):
    _signal = Signal(object)


class _HollowSignal(QObject):
    _signal = Signal()


class InHollowSignal:
    _signal: _HollowSignal

    def __init__(self, slot: Callable[[], None] | None = None):
        self._signal = _HollowSignal()
        if slot is not None:
            self.link(slot)

    def __call__(self) -> None:
        self._signal._signal.emit()

    def link(self, slot: Callable[[], None]) -> None:
        self._signal._signal.connect(slot)

    def unlink(self, slot: Callable[[], None] | None = None) -> None:
        if slot is None:
            self._signal._signal.disconnect()
        else:
            self._signal._signal.disconnect(slot)


class OutHollowSignal:
    _signal: _HollowSignal

    def __init__(self, slot: Callable[[], None] | None = None):
        self._signal = _HollowSignal()
        if slot is not None:
            self.link(slot)

    def send(self) -> None:
        self._signal._signal.emit()

    def link(self, slot: Callable[[], None]) -> None:
        self._signal._signal.connect(slot)

    def unlink(self, slot: Callable[[], None] | None = None) -> None:
        if slot is None:
            self._signal._signal.disconnect()
        else:
            self._signal._signal.disconnect(slot)


class InSolidSignal(Generic[_T]):
    _signal: _SolidSignal

    def __init__(self, slot: Callable[[_T], None] | None = None):
        self._signal = _SolidSignal()
        if slot is not None:
            self.link(slot)

    def __call__(self, arg: _T) -> None:
        self._signal._signal.emit(arg)

    def link(self, slot: Callable[[_T], None]) -> None:
        self._signal._signal.connect(slot)

    def unlink(self, slot: Callable[[_T], None] | None = None) -> None:
        if slot is None:
            self._signal._signal.disconnect()
        else:
            self._signal._signal.disconnect(slot)


class OutSolidSignal(Generic[_T]):
    _signal: _SolidSignal

    def __init__(self, slot: Callable[[_T], None] | None = None):
        self._signal = _SolidSignal()
        if slot is not None:
            self.link(slot)

    def send(self, arg: _T) -> None:
        self._signal._signal.emit(arg)

    def link(self, slot: Callable[[_T], None]) -> None:
        self._signal._signal.connect(slot)

    def unlink(self, slot: Callable[[_T], None] | None = None) -> None:
        if slot is None:
            self._signal._signal.disconnect()
        else:
            self._signal._signal.disconnect(slot)
