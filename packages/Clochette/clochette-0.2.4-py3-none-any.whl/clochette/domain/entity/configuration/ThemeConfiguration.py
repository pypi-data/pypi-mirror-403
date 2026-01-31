from __future__ import annotations

from dataclasses import dataclass

from clochette.domain.entity.configuration.ThemeEnum import ThemeEnum


@dataclass(eq=True, frozen=True)
class ThemeConfiguration:
    window_icon_theme: ThemeEnum
    systray_icon_theme: ThemeEnum

    @staticmethod
    def default():
        return ThemeConfiguration(window_icon_theme=ThemeEnum.GENERIC, systray_icon_theme=ThemeEnum.GENERIC)
