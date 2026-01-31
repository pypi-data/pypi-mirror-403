from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QLineEdit,
    QFormLayout,
    QGroupBox,
)

from clochette.application.service.provider.dto.ProviderDTO import ProviderDTO
from clochette.application.service.provider.dto.ProviderType import ProviderType
from clochette.domain.entity.configuration.CalendarConfiguration import (
    CalendarConfiguration,
)
from clochette.framework.qt.Signal import OutHollowSignal
from clochette.presentation.settings.calendar.dto.CalendarFormValuesDTO import CalendarFormValuesDTO
from clochette.presentation.settings.calendar.provider.QAuthenticationSourceComponent import (
    QAuthenticationSourceComponent,
)
from clochette.presentation.settings.calendar.tabs.QCalendarAlarmsView import (
    QCalendarAlarmsView,
)
from clochette.presentation.settings.calendar.tabs.QCalendarGeneralSettingsView import (
    QCalendarGeneralSettingsView,
)
from clochette.presentation.widget.QGenericComboBox import QGenericComboBox
from clochette.presentation.widget.QOkCancelButton import QOkCancelButton
from clochette.presentation.widget.QVScrollArea import QVScrollArea


class QCalendarTabPanelView(QWidget):
    """Simple view widget for configuring calendar: authentication, general settings, and alarms"""

    # Out signals
    on_ok = OutHollowSignal()
    on_cancel = OutHollowSignal()

    _current_configuration: CalendarConfiguration | None
    _tab_widget: QTabWidget
    _calendar_name: QLineEdit
    _auth_combo: QGenericComboBox[ProviderType]
    _authentication_source_component: QAuthenticationSourceComponent
    _general_settings_widget: QCalendarGeneralSettingsView
    _alarms_widget: QCalendarAlarmsView
    _ok_cancel_button: QOkCancelButton

    def __init__(self, authentication_source_component: QAuthenticationSourceComponent):
        super().__init__()

        self._current_configuration = None

        self._authentication_source_component = authentication_source_component

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create tab widget
        self._tab_widget = QTabWidget()
        layout.addWidget(self._tab_widget)

        # Tab 1: Authentication
        auth_tab = QWidget()
        auth_layout = QVBoxLayout()
        auth_tab.setLayout(auth_layout)

        auth_group = QGroupBox(self.tr("Authentication"))
        auth_form_layout = QFormLayout()

        self._calendar_name = QLineEdit()
        self._calendar_name.setPlaceholderText(self.tr("Type a name"))
        auth_form_layout.addRow(self.tr("Calendar Name"), self._calendar_name)

        self._auth_combo = QGenericComboBox[ProviderType]()
        self._auth_combo.currentIndexChanged.connect(self._on_combo_changed)
        auth_form_layout.addRow(self.tr("Authentication Type"), self._auth_combo)

        auth_group.setLayout(auth_form_layout)
        auth_layout.addWidget(auth_group)

        auth_layout.addWidget(self._authentication_source_component.view())
        auth_layout.addStretch()

        self._tab_widget.addTab(auth_tab, self.tr("Authentication"))

        # Tab 2: General Settings
        self._general_settings_widget = QCalendarGeneralSettingsView()
        self._tab_widget.addTab(self._general_settings_widget, self.tr("General"))

        # Tab 3: Alarms (with scrollbar)
        alarms_scroll = QVScrollArea()
        self._alarms_widget = QCalendarAlarmsView()
        alarms_scroll.setWidget(self._alarms_widget)
        self._tab_widget.addTab(alarms_scroll, self.tr("Override Alarms"))

        # make the background transparent
        alarms_scroll.viewport().setAutoFillBackground(False)
        alarms_scroll.setStyleSheet("QCalendarAlarmsView { background: transparent; }")

        # OK/Cancel buttons at the bottom
        self._ok_cancel_button = QOkCancelButton()
        self._ok_cancel_button.on_ok_clicked.link(self._on_ok_clicked)
        self._ok_cancel_button.on_cancel_clicked.link(self._on_cancel_clicked)
        layout.addWidget(self._ok_cancel_button)

    def set_providers(self, providers_list: list[ProviderDTO]) -> None:
        """Populate provider combo box with available providers and set default"""
        items = [(p.provider_type, p.display_name) for p in providers_list]
        self._auth_combo.set_items(items)
        # Set default to first provider if items exist
        if items:
            self.update_panel(items[0][0])

    def _on_combo_changed(self) -> None:
        """Handle combo box selection change"""
        current_key = self._auth_combo.current_key()
        if current_key is not None:
            self.update_panel(current_key)

    def set_configuration(self, config: CalendarConfiguration) -> None:
        """Update all tabs from a CalendarConfiguration"""
        self._current_configuration = config

        # Update authentication tab
        self._calendar_name.setText(config.name)
        self._authentication_source_component.set_values_from_source(config.id, config.source)

        # Update general settings tab
        self._general_settings_widget.set_from_configuration(config)

        # Update alarms tab
        self._alarms_widget.set_from_configuration(config)

    def update_panel(self, provider_type: ProviderType) -> None:
        """Update authentication panel based on selected provider type"""
        self._authentication_source_component.set_provider_type(provider_type)

    def set_selected_provider_type(self, provider_type: ProviderType) -> None:
        """Set the selected provider type"""
        self._auth_combo.set_current_by_key(provider_type)
        self._authentication_source_component.set_provider_type(provider_type)

    def set_calendar_name(self, name: str) -> None:
        """Set the calendar name"""
        self._calendar_name.setText(name)

    def clear(self) -> None:
        """Clear all form fields"""
        self._current_configuration = None
        self._calendar_name.setText("")
        self._general_settings_widget.clear()
        self._alarms_widget.clear()
        self._authentication_source_component.clear()

    def _on_ok_clicked(self) -> None:
        """Handle OK button click"""
        self.on_ok.send()

    def _on_cancel_clicked(self) -> None:
        """Handle Cancel button click"""
        self.on_cancel.send()

    def get_form_values(self) -> CalendarFormValuesDTO:
        """Get all form values as a simple DTO (no business logic)"""
        return CalendarFormValuesDTO(
            name=self._calendar_name.text(),
            source=self._authentication_source_component.get_source(),
            download_interval=self._general_settings_widget.get_download_interval(),
            missed_reminders_past_window=self._general_settings_widget.get_missed_reminders_past_window(),
            http_timeout=self._general_settings_widget.get_http_timeout(),
            force_alarms=self._alarms_widget.get_force_alarms(),
            force_alarms_dates=self._alarms_widget.get_force_alarms_dates(),
            default_alarms=self._alarms_widget.get_default_alarms(),
            default_alarms_dates=self._alarms_widget.get_default_alarms_dates(),
        )

    @property
    def calendar_name(self) -> str:
        """Get the calendar name"""
        return self._calendar_name.text()

    @property
    def authentication_source_component(self) -> QAuthenticationSourceComponent:
        """Get the authentication source component"""
        return self._authentication_source_component
