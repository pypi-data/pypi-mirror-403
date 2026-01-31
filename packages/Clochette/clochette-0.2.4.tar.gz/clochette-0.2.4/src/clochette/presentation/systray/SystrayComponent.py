from dataclasses import dataclass

from clochette.infrastructure.shutdown.ShutdownService import ShutdownService
from clochette.framework.qt.Link import Link
from clochette.framework.qt.QComponent import QComponent
from clochette.presentation.settings.global_settings.QGlobalSettingsComponent import (
    QGlobalSettingsComponent,
)
from clochette.presentation.systray.QSystray import QSystray
from clochette.presentation.theme.ThemeService import ThemeService


@dataclass
class SystrayComponent(QComponent[QSystray]):
    _systray: QSystray
    _shutdown_service: ShutdownService
    _global_settings_component: QGlobalSettingsComponent
    _theme_service: ThemeService

    def __post_init__(self):
        super().__init__(self._systray)
        self._systray.on_exit_clicked.link(self._shutdown_service.close)
        self._systray.on_settings_clicked.link(self._show_settings)
        self._systray.on_icon_clicked.link(self._toggle_settings)

        Link(
            observable=self._theme_service.icon_systray,
            handler=self._systray.set_icon,
            widget=self._systray,
        )

    def _show_settings(self):
        self._global_settings_component.show_window()

    def _toggle_settings(self):
        """Toggle settings window visibility: show if hidden, hide if shown"""
        if self._global_settings_component.view().isVisible():
            self._global_settings_component.view().hide()
        else:
            self._global_settings_component.show_window()

    def show(self):
        self._systray.show()
