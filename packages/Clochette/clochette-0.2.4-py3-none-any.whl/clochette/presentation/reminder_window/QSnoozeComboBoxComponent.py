from clochette.application.store.GeneralConfigurationStore import GeneralConfigurationStore
from clochette.domain.entity.delta.SnoozeDelta import SnoozeDelta
from clochette.framework.qt.Link import Link
from clochette.framework.qt.Signal import OutSolidSignal
from clochette.presentation.reminder_window.QSnoozeComboBoxView import QSnoozeComboBoxView
from clochette.presentation.theme.ThemeService import ThemeService
from clochette.presentation.window.QCustomSnoozeWindow import QCustomSnoozeWindow


class QSnoozeComboBoxComponent:
    """Component that wires QSnoozeComboBoxView to QCustomSnoozeWindow and global configuration."""

    on_snooze_selected: OutSolidSignal[SnoozeDelta]

    _view: QSnoozeComboBoxView
    _custom_snooze_window: QCustomSnoozeWindow

    def __init__(
        self,
        theme_service: ThemeService,
        general_configuration_store: GeneralConfigurationStore,
        is_date: bool,
    ) -> None:
        # Create view with empty snoozes initially - will be populated via Link
        self._view = QSnoozeComboBoxView([], is_date)
        self._custom_snooze_window = QCustomSnoozeWindow(theme_service.icon_window)

        # Use Link to subscribe to snoozes and update them in view
        Link(
            observable=general_configuration_store.snoozes,
            handler=lambda snoozes: self._view.set_snoozes(snoozes),
            widget=self._view,
        )

        # Forward snooze selection from view
        self.on_snooze_selected = self._view.on_snooze_selected

        # Wire: view custom snooze request -> show window
        self._view.on_custom_snooze_requested.link(self._on_custom_snooze_requested)

        # Wire: window submission -> forward selection and hide view
        self._custom_snooze_window.on_submitted.link(self._on_custom_snooze_submitted)

    def _on_custom_snooze_requested(self) -> None:
        """Handle custom snooze request by showing the window."""
        self._custom_snooze_window.show_window()

    def _on_custom_snooze_submitted(self, delta: SnoozeDelta) -> None:
        """Handle custom snooze submission."""
        self.on_snooze_selected.send(delta)
        self._view.hide()

    def view(self) -> QSnoozeComboBoxView:
        """Get the view widget."""
        return self._view
