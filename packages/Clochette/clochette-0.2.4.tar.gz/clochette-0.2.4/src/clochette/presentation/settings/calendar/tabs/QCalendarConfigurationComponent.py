from dataclasses import dataclass

from clochette.application.store.ProviderStore import ProviderStore
from clochette.application.usecase.AddCalendarUseCase import AddCalendarUseCase
from clochette.application.usecase.UpdateCalendarUseCase import UpdateCalendarUseCase
from clochette.domain.entity.configuration.CalendarConfiguration import (
    CalendarConfiguration,
)
from clochette.domain.factory.CalendarConfigurationFactory import (
    CalendarConfigurationFactory,
)
from clochette.framework.qt.Link import Link
from clochette.framework.qt.QComponent import QComponent
from clochette.presentation.settings.calendar.CalendarNavigationModel import (
    CalendarNavigationModel,
)
from clochette.presentation.settings.calendar.CalendarSettingsModel import (
    CalendarSettingsModel,
)
from clochette.presentation.settings.calendar.authentication.AuthenticationConfigurationModel import (
    AuthenticationConfigurationModel,
)
from clochette.presentation.settings.calendar.tabs.QCalendarTabPanelView import (
    QCalendarTabPanelView,
)
from clochette.provider.public.dto.PublicProviderType import PublicProviderType


@dataclass
class QCalendarConfigurationComponent(QComponent[QCalendarTabPanelView]):
    """Coordinator for calendar configuration that wires navigation and use cases"""

    _view: QCalendarTabPanelView
    _provider_store: ProviderStore
    _auth_model: AuthenticationConfigurationModel
    _settings_model: CalendarSettingsModel
    _navigation_model: CalendarNavigationModel
    _add_calendar_usecase: AddCalendarUseCase
    _update_calendar_usecase: UpdateCalendarUseCase
    _calendar_configuration_factory: CalendarConfigurationFactory

    def __post_init__(self):
        super().__init__(self._view)

        # Wire: ProviderStore → View InSignal
        Link(
            observable=self._provider_store.providers,
            handler=self._view.set_providers,
            widget=self._view,
        )

        # Connect OK/Cancel buttons
        self._view.on_ok.link(self._save_calendar)
        self._view.on_cancel.link(lambda: self._navigation_model.show_calendar_list.on_next(True))

        # Wire: Navigation add_calendar → handler (Link wraps in signal for thread-safety)
        Link(
            observable=self._navigation_model.add_calendar,
            handler=lambda _: self._on_add_calendar(),
            widget=self._view,
        )

        # Wire: Navigation edit_calendar → handler (Link wraps in signal for thread-safety)
        Link(
            observable=self._navigation_model.edit_calendar,
            handler=self._on_edit_calendar,
            widget=self._view,
        )

    def _on_add_calendar(self):
        """Handle add calendar navigation event"""
        self._clear()
        self._auth_model.edit_calendar = None
        self._settings_model.edit_calendar = None
        self._view.set_selected_provider_type(PublicProviderType())

    def _on_edit_calendar(self, calendar: CalendarConfiguration):
        """Handle edit calendar navigation event (authentication tab)"""
        self._clear()
        self._auth_model.edit_calendar = calendar
        self._settings_model.edit_calendar = calendar
        self._view.set_configuration(calendar)
        self._view.set_selected_provider_type(calendar.source.provider_type)

    def _clear(self):
        """Clear all form fields"""
        self._view.clear()

    def _save_calendar(self):
        """Save the calendar (add or update)"""
        # Get form values from the view (presentation layer DTO)
        form_values = self._view.get_form_values()

        # Check if we're editing or adding
        existing_calendar = self._auth_model.edit_calendar or self._settings_model.edit_calendar

        if existing_calendar is not None:
            # Update existing calendar using factory
            calendar = self._calendar_configuration_factory.update_from_form_values(existing_calendar, form_values)
            self._update_calendar_usecase.update_calendar(calendar).subscribe()
        else:
            # Add new calendar using factory
            calendar = self._calendar_configuration_factory.create_from_form_values(form_values)
            self._add_calendar_usecase.add_calendar(calendar).subscribe()

        self._navigation_model.show_calendar_list.on_next(True)
