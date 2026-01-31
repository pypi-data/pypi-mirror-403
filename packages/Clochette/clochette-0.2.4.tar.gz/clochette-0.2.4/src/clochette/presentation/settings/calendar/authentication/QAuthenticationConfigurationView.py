from PySide6.QtWidgets import QWidget, QGroupBox, QLineEdit, QFormLayout, QVBoxLayout

from clochette.application.service.provider.dto.ProviderDTO import ProviderDTO
from clochette.application.service.provider.dto.ProviderType import ProviderType
from clochette.application.store.ProviderStore import ProviderStore
from clochette.framework.qt.Link import Link
from clochette.framework.qt.Signal import InHollowSignal, InSolidSignal
from clochette.presentation.widget.QGenericComboBox import QGenericComboBox
from clochette.presentation.widget.QOkCancelButton import QOkCancelButton
from clochette.presentation.settings.calendar.provider.QAuthenticationSourceComponent import (
    QAuthenticationSourceComponent,
)


class QAuthenticationConfigurationView(QWidget):
    """Panel for configuring calendar authentication (calendar name + authentication source)"""

    set_selected_provider_type: InSolidSignal[ProviderType]
    update_panel: InSolidSignal[ProviderType]
    set_calendar_name: InSolidSignal[str]
    clear: InHollowSignal

    _calendar_name: QLineEdit
    _auth_combo: QGenericComboBox[ProviderType]
    _authentication_source_component: QAuthenticationSourceComponent
    _ok_cancel_button: QOkCancelButton

    def __init__(
        self,
        authentication_source_component: QAuthenticationSourceComponent,
        provider_store: ProviderStore,
    ):
        super().__init__()

        self.set_selected_provider_type = InSolidSignal(
            self._set_selected_provider_type
        )
        self.update_panel = InSolidSignal(self._update_panel)
        self.set_calendar_name = InSolidSignal(self._set_calendar_name)
        self.clear = InHollowSignal(self._clear)

        self._authentication_source_component = authentication_source_component

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Calendar name and authentication type selector
        auth_group = QGroupBox(self.tr("Authentication"))
        auth_layout = QFormLayout()

        self._calendar_name = QLineEdit()
        self._calendar_name.setPlaceholderText(self.tr("Type a name"))
        auth_layout.addRow(self.tr("Calendar Name"), self._calendar_name)

        self._auth_combo = QGenericComboBox[ProviderType]()
        self._auth_combo.currentIndexChanged.connect(self._on_combo_changed)
        auth_layout.addRow(self.tr("Authentication Type"), self._auth_combo)

        Link(
            observable=provider_store.providers,
            handler=self._on_providers_loaded,
            widget=self,
        )

        auth_group.setLayout(auth_layout)
        layout.addWidget(auth_group)

        # Provider-specific authentication panels
        layout.addWidget(self._authentication_source_component.view())

        layout.addStretch()

        self._ok_cancel_button = QOkCancelButton()
        layout.addWidget(self._ok_cancel_button)

    def _on_providers_loaded(self, providers_list: list[ProviderDTO]) -> None:
        """Subscribe to provider store to populate combo box and set default"""
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

    def _update_panel(self, provider_type: ProviderType) -> None:
        self._authentication_source_component.set_provider_type(provider_type)

    def _set_selected_provider_type(self, provider_type: ProviderType) -> None:
        self._auth_combo.set_current_by_key(provider_type)
        self._authentication_source_component.set_provider_type(provider_type)

    def _set_calendar_name(self, name: str) -> None:
        self._calendar_name.setText(name)

    def _clear(self):
        self._calendar_name.setText("")

    def get_selected_provider_type(self) -> ProviderType:
        return self._authentication_source_component.view().get_selected_provider_type()

    @property
    def calendar_name(self) -> str:
        return self._calendar_name.text()

    @property
    def ok_cancel_button(self) -> QOkCancelButton:
        return self._ok_cancel_button

    @property
    def authentication_source_component(self) -> QAuthenticationSourceComponent:
        return self._authentication_source_component
