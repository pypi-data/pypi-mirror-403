import configparser
from dataclasses import dataclass
from typing import Any, Sequence, TypeAlias

from isodate import duration_isoformat
from reactivex import Observable, empty, from_iterable, operators as ops

from clochette import log
from clochette.application.service.configurartion.SourceConfigurationMapperStrategy import (
    SourceConfigurationMapperStrategy,
)
from clochette.domain.entity.delta.Delta import Delta
from clochette.domain.entity.configuration.ThemeEnum import ThemeEnum
from clochette.framework.rx.Scheduler import scheduler
from clochette.persist.configuration.PlatformConfigurationService import PlatformConfigurationService
from clochette.persist.configuration.dto.CalendarConfigurationDTO import CalendarConfigurationDTO
from clochette.persist.configuration.dto.GlobalConfigurationDTO import GlobalConfigurationDTO

CalendarParameters: TypeAlias = dict[str, Any]
CalendarConfig: TypeAlias = tuple[str, CalendarParameters]

_CONFIG_SECTION = "Config"


@dataclass
class ConfigurationWriterService:
    _platform_config: PlatformConfigurationService
    _source_configuration_mapper_strategy: SourceConfigurationMapperStrategy

    def write(self, global_configuration: GlobalConfigurationDTO) -> Observable[None]:
        """Write configuration to file, returning an Observable."""
        log.info("Writing Configuration")

        return self._get_all_calendars(global_configuration.calendars).pipe(
            ops.map(lambda calendar_dicts: self._write_config_file(global_configuration, calendar_dicts)),
        )

    def _get_all_calendars(self, calendars: list[CalendarConfigurationDTO]) -> Observable[list[CalendarConfig]]:
        """Get all calendar configurations as an observable list of tuples (id, config)."""
        return from_iterable(calendars, scheduler=scheduler).pipe(
            ops.flat_map(lambda calendar: self._get_calendar_dict(calendar)),
            ops.to_list(),
        )

    def _get_calendar_dict(self, calendar: CalendarConfigurationDTO) -> Observable[CalendarConfig]:
        """Get calendar configuration dict with error handling."""

        return self._source_configuration_mapper_strategy.write(calendar.source).pipe(
            ops.map(lambda x: self._build_calendar_dict(calendar, x)),
            ops.catch(lambda error, _src: self._handle_write_error(calendar, error)),
        )

    def _build_calendar_dict(
        self, calendar: CalendarConfigurationDTO, authentication: dict[str, str]
    ) -> CalendarConfig:
        """Build calendar configuration dictionary from authentication and calendar data."""
        calendar_dict = authentication | {
            "name": calendar.name,
            "download.interval.minutes": int(calendar.download_interval.total_seconds() / 60),
            "missed.reminders.past_window": duration_isoformat(calendar.missed_reminders_past_window),
            "force_alarms": self._get_timedelta_list(calendar.force_alarms),
            "force_alarms_dates": self._get_timedelta_list(calendar.force_alarms_dates),
            "default_alarms": self._get_timedelta_list(calendar.default_alarms),
            "default_alarms_dates": self._get_timedelta_list(calendar.default_alarms_dates),
            "timeout.connection": calendar.http_timeout.connection_timeout,
            "timeout.read": calendar.http_timeout.read_timeout,
        }
        return (calendar.id.id, calendar_dict)

    def _handle_write_error(
        self, calendar: CalendarConfigurationDTO, error: Exception
    ) -> Observable[tuple[str, dict[str, str]]]:
        """Handle errors from writing calendar configuration by logging and returning empty."""
        log.warning(f"Failed to write calendar configuration: {calendar.id.id}", exc_info=error)
        return empty()

    def _write_config_file(
        self, global_configuration: GlobalConfigurationDTO, calendar_dicts: list[CalendarConfig]
    ) -> None:
        """Write the complete configuration file with global settings and all calendars."""
        config = configparser.RawConfigParser()

        snoozes_str = self._get_timedelta_list(global_configuration.snoozes)
        theme_icon_window = self._get_theme(global_configuration.theme.window_icon_theme)
        systray_icon_theme = self._get_theme(global_configuration.theme.systray_icon_theme)

        config[_CONFIG_SECTION] = {
            "snooze": snoozes_str,
            "theme.icon.window": theme_icon_window,
            "theme.icon.systray": systray_icon_theme,
        }

        for calendar_id, calendar_config in calendar_dicts:
            config[calendar_id] = calendar_config

        configuration_file = self._platform_config.application_configuration_file()

        with open(configuration_file, "w") as configfile:
            config.write(configfile)

    def _get_theme(self, theme: ThemeEnum) -> str:
        if theme == ThemeEnum.DARK:
            return "DARK"
        if theme == ThemeEnum.LIGHT:
            return "LIGHT"
        return "GENERIC"

    def _get_timedelta(self, value: Delta) -> str:
        return duration_isoformat(value.get_timedelta())

    def _get_timedelta_list(self, values: Sequence[Delta]) -> str:
        return ",".join(list(map(self._get_timedelta, values)))
