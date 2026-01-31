from typing import override

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QVBoxLayout

from clochette.presentation.settings.about.QAboutClochette import QAboutClochette
from clochette.presentation.settings.calendar.QCalendarSettingsComponent import (
    QCalendarSettingsComponent,
)
from clochette.presentation.settings.global_settings.QGeneralSettingsComponent import (
    QGeneralSettingsComponent,
)
from clochette.presentation.theme.ThemeService import ThemeService
from clochette.presentation.widget.QSettingsPanel import QSettingsPanel
from clochette.presentation.window.QAbstractWindow import QAbstractWindow


class QGlobalSettingsWindow(QAbstractWindow):
    def __init__(
        self,
        theme_service: ThemeService,
        general_settings_component: QGeneralSettingsComponent,
        calendar_setting_component: QCalendarSettingsComponent,
    ) -> None:
        super().__init__(theme_service.icon_window, self.tr("Clochette - Settings"))

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._settings_panel = QSettingsPanel()

        self._settings_panel.add_item(
            self.tr("General Settings"), general_settings_component.view()
        )
        self._settings_panel.add_item(
            self.tr("Calendars"), calendar_setting_component.view()
        )
        self._settings_panel.add_item(self.tr("About Clochette"), QAboutClochette())

        layout.addWidget(self._settings_panel)

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        # don't close the settings window, only hide it
        # if you don't do this, you can only open the settings once from the systray, after that you cannot re-open it
        event.ignore()
        self.hide()
