from dataclasses import dataclass

from reactivex import operators as ops

from clochette.application.store.GeneralConfigurationStore import GeneralConfigurationStore
from clochette.application.usecase.UpdateSnoozesUseCase import UpdateSnoozesUseCase
from clochette.application.usecase.UpdateThemeUseCase import UpdateThemeUseCase
from clochette.domain.entity.delta.SnoozeDelta import SnoozeDelta
from clochette.domain.entity.configuration.ThemeConfiguration import ThemeConfiguration
from clochette.framework.qt.Link import Link
from clochette.framework.qt.QComponent import QComponent
from clochette.presentation.settings.global_settings.QGeneralSettingsView import QGeneralSettingsView


@dataclass
class QGeneralSettingsComponent(QComponent[QGeneralSettingsView]):
    """Component that wires general settings view to stores and use cases."""

    _view: QGeneralSettingsView
    _general_configuration_store: GeneralConfigurationStore
    _update_snoozes_usecase: UpdateSnoozesUseCase
    _update_theme_usecase: UpdateThemeUseCase

    def __post_init__(self):
        super().__init__(self._view)

        # Wire store -> view (snoozes)
        Link(
            observable=self._general_configuration_store.snoozes,
            handler=self._view.set_snoozes,
            widget=self._view,
        )

        # Wire store -> view (window theme)
        Link(
            observable=self._general_configuration_store.theme.pipe(
                ops.map(lambda theme: theme.window_icon_theme),
            ),
            handler=self._view.set_window_theme,
            widget=self._view,
        )

        # Wire store -> view (systray theme)
        Link(
            observable=self._general_configuration_store.theme.pipe(
                ops.map(lambda theme: theme.systray_icon_theme),
            ),
            handler=self._view.set_systray_theme,
            widget=self._view,
        )

        self._view.on_snoozes_changed.link(self._on_snoozes_changed)
        self._view.on_theme_changed.link(self._on_theme_changed)

    def _on_snoozes_changed(self, snoozes: list[SnoozeDelta]):
        self._update_snoozes_usecase.update_snoozes(snoozes).subscribe()

    def _on_theme_changed(self, theme: ThemeConfiguration) -> None:
        """Handle theme change - unpack tuple and call use case."""
        self._update_theme_usecase.update_theme(theme).subscribe()
