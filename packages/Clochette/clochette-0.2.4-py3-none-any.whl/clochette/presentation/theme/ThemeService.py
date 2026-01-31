from dataclasses import dataclass

from PySide6.QtGui import QIcon
from reactivex import Observable
from reactivex import operators as ops

from clochette.application.store.GeneralConfigurationStore import GeneralConfigurationStore
from clochette.domain.entity.configuration.ThemeEnum import ThemeEnum


@dataclass
class ThemeService:
    _general_configuration_store: GeneralConfigurationStore

    def _icon(self, theme: ThemeEnum) -> QIcon:
        if theme == ThemeEnum.DARK:
            return QIcon(":/icon-dark.svg")
        if theme == ThemeEnum.LIGHT:
            return QIcon(":/icon-light.svg")
        if theme == ThemeEnum.GENERIC:
            return QIcon(":/icon-generic.svg")
        raise ValueError(f"Unexpected theme value: {theme}")

    @property
    def icon_window(self) -> Observable[QIcon]:
        return self._general_configuration_store.theme.pipe(
            ops.map(lambda theme_config: self._icon(theme_config.window_icon_theme))
        )

    @property
    def icon_systray(self) -> Observable[QIcon]:
        return self._general_configuration_store.theme.pipe(
            ops.map(lambda theme_config: self._icon(theme_config.systray_icon_theme))
        )

    def _browser_icon(self, icon_name: str, theme: ThemeEnum) -> QIcon:
        if theme == ThemeEnum.DARK:
            return QIcon(f":/browser/{icon_name}-dark.svg")
        if theme == ThemeEnum.LIGHT:
            return QIcon(f":/browser/{icon_name}-light.svg")
        if theme == ThemeEnum.GENERIC:
            return QIcon(f":/browser/{icon_name}-generic.svg")
        raise ValueError(f"Unexpected theme value: {theme}")

    @property
    def icon_browser_back(self) -> Observable[QIcon]:
        return self._general_configuration_store.theme.pipe(
            ops.map(lambda theme_config: self._browser_icon("arrow-big-left", theme_config.window_icon_theme))
        )

    @property
    def icon_browser_forward(self) -> Observable[QIcon]:
        return self._general_configuration_store.theme.pipe(
            ops.map(lambda theme_config: self._browser_icon("arrow-big-right", theme_config.window_icon_theme))
        )

    @property
    def icon_browser_reload(self) -> Observable[QIcon]:
        return self._general_configuration_store.theme.pipe(
            ops.map(lambda theme_config: self._browser_icon("refresh-cw", theme_config.window_icon_theme))
        )
