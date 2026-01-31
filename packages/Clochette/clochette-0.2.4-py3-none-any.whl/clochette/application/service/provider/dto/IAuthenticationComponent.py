from abc import ABC, abstractmethod
from typing import Generic, Type, TypeVar

from PySide6.QtWidgets import QWidget

from clochette.domain.entity.CalendarID import CalendarID

_T = TypeVar("_T")
_U = TypeVar("_U")


class IAuthenticationComponent(ABC, Generic[_T, _U]):
    """Generic interface for authentication components"""

    @abstractmethod
    def view(self) -> QWidget:
        """Get the widget view for this component"""
        pass

    @abstractmethod
    def set_values(self, calendar_id: CalendarID, source: _T) -> None:
        """Set values in the component from the source"""
        pass

    @abstractmethod
    def get_values(self) -> _U:
        """Get values from the component"""
        pass

    @abstractmethod
    def get_source(self) -> _T:
        """Get the calendar source from the component values"""
        pass

    @property
    @abstractmethod
    def source_type(self) -> Type[_T]:
        """Get the source type this component handles"""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate the component's values"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear the component's values"""
        pass
