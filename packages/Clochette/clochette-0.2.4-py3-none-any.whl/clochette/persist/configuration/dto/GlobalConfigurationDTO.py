from __future__ import annotations

from dataclasses import dataclass

from clochette.domain.entity.delta.SnoozeDelta import SnoozeDelta
from clochette.domain.entity.configuration.ThemeConfiguration import ThemeConfiguration
from clochette.persist.configuration.dto.CalendarConfigurationDTO import CalendarConfigurationDTO


@dataclass
class GlobalConfigurationDTO:
    snoozes: list[SnoozeDelta]
    calendars: list[CalendarConfigurationDTO]
    theme: ThemeConfiguration

    @staticmethod
    def default() -> GlobalConfigurationDTO:
        return GlobalConfigurationDTO(
            snoozes=[],
            calendars=[],
            theme=ThemeConfiguration.default(),
        )
