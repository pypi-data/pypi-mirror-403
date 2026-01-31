from PySide6.QtWidgets import QWidget, QVBoxLayout

from clochette.application.service.provider.dto.IAuthenticationComponent import IAuthenticationComponent
from clochette.application.service.provider.dto.ProviderDTO import ProviderDTO
from clochette.application.service.provider.dto.ProviderType import ProviderType
from clochette.application.store.ProviderStore import ProviderStore
from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.ISourceCalendar import ISourceCalendar
from clochette.framework.qt.Link import Link
from clochette.framework.qt.Signal import InSolidSignal, InHollowSignal
from clochette.presentation.widget.QDynamicWidgetContainer import QDynamicWidgetContainer


class QAuthenticationSourceView(QWidget):
    """Panel that displays provider-specific authentication UI based on selected provider type"""

    set_selected_provider_type: InSolidSignal[ProviderType]
    clear: InHollowSignal

    _container: QDynamicWidgetContainer[ProviderType]
    _provider_component_map: dict[ProviderType, IAuthenticationComponent]

    def __init__(self, provider_store: ProviderStore):
        super().__init__()

        self.set_selected_provider_type = InSolidSignal(self._set_selected_provider_type)
        self.clear = InHollowSignal(self._clear)

        self._provider_component_map = {}

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._container = QDynamicWidgetContainer[ProviderType]()
        layout.addWidget(self._container)

        Link(
            observable=provider_store.providers,
            handler=self._on_providers_loaded,
            widget=self,
        )

    def _on_providers_loaded(self, providers_list: list[ProviderDTO]) -> None:
        """Subscribe to provider store to populate authentication panels"""
        # Clear existing mappings
        self._provider_component_map.clear()

        # Add each provider's authentication component
        for provider_dto in providers_list:
            provider_type = provider_dto.provider_type
            self._provider_component_map[provider_type] = provider_dto.authentication_component

            # Add the component's view to the container
            self._container.add_widget(provider_type, provider_dto.authentication_component.view())

    def _set_selected_provider_type(self, provider_type: ProviderType) -> None:
        self._container.show_widget(provider_type)

    def _clear(self):
        """Clear all provider-specific panels"""
        for component in self._provider_component_map.values():
            component.clear()

    def get_selected_provider_type(self) -> ProviderType:
        return self._container.current_key()

    def get_component_by_provider_type(self, provider_type: ProviderType) -> IAuthenticationComponent:
        """Get the authentication component for a specific provider type"""
        return self._provider_component_map[provider_type]

    def get_source(self) -> ISourceCalendar:
        """Get the calendar source from the selected provider panel"""
        provider_type = self.get_selected_provider_type()
        component = self._provider_component_map[provider_type]
        if not component.validate():
            raise ValueError(f"{provider_type.get_id()} authentication validation failed")
        return component.get_source()

    def set_values_from_source(self, calendar_id: CalendarID, source: ISourceCalendar) -> None:
        """Set values in the appropriate provider panel based on source type"""
        for provider_type, component in self._provider_component_map.items():
            if source.provider_type == provider_type:
                component.set_values(calendar_id, source)
                self.set_selected_provider_type(provider_type)
                return
        raise ValueError(f"No provider found for provider type: {source.provider_type}")
