from typing import Generic, TypeVar

from PySide6.QtCore import QObject

_T = TypeVar("_T", bound="QObject")


class QComponent(Generic[_T]):
    __view: _T

    def __init__(self, view: _T):
        self.__view = view

    def view(self) -> _T:
        return self.__view
