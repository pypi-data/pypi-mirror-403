from dataclasses import dataclass

from clochette.application.service.provider.dto.ProviderType import ProviderType
from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.ISourceCalendar import ISourceCalendar
from clochette.framework.qt.QComponent import QComponent
from clochette.presentation.settings.calendar.provider.QAuthenticationSourceView import QAuthenticationSourceView


@dataclass
class QAuthenticationSourceComponent(QComponent[QAuthenticationSourceView]):
    """Component that handles provider-specific authentication logic"""

    _view: QAuthenticationSourceView

    def __post_init__(self):
        super().__init__(self._view)

    def set_values_from_source(self, calendar_id: CalendarID, source: ISourceCalendar) -> None:
        """Set values in the appropriate provider panel based on source type"""
        self._view.set_values_from_source(calendar_id, source)

    def get_source(self) -> ISourceCalendar:
        """Get the calendar source from the selected provider panel"""
        return self._view.get_source()

    def clear(self) -> None:
        """Clear all provider panels"""
        self._view.clear()

    def set_provider_type(self, provider_type: ProviderType) -> None:
        """Set the selected provider type"""
        self._view.set_selected_provider_type(provider_type)
