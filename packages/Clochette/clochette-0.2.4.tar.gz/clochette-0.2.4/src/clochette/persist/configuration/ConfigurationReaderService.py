import configparser
from configparser import SectionProxy
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import isodate
from reactivex import Observable, empty, from_iterable, operators as ops, defer

from clochette import log
from clochette.application.service.configurartion.SourceConfigurationMapperStrategy import (
    SourceConfigurationMapperStrategy,
)
from clochette.domain.entity.delta.AlarmDelta import AlarmDelta
from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.ISourceCalendar import ISourceCalendar
from clochette.domain.entity.delta.SnoozeDelta import SnoozeDelta
from clochette.domain.entity.configuration.HttpTimeout import HttpTimeout
from clochette.domain.entity.configuration.ThemeConfiguration import ThemeConfiguration
from clochette.domain.entity.configuration.ThemeEnum import ThemeEnum
from clochette.persist.configuration.ConfigurationMigrationService import ConfigurationMigrationService
from clochette.persist.configuration.ConfigurationReadUtils import read_str, read_int
from clochette.persist.configuration.PlatformConfigurationService import PlatformConfigurationService
from clochette.persist.configuration.dto.CalendarConfigurationDTO import CalendarConfigurationDTO
from clochette.persist.configuration.dto.GlobalConfigurationDTO import GlobalConfigurationDTO

_CONFIG_SECTION = "Config"


@dataclass
class ConfigurationReaderService:
    _platform_config: PlatformConfigurationService
    _configuration_migration_service: ConfigurationMigrationService
    _source_configuration_mapper_strategy: SourceConfigurationMapperStrategy

    def read(self) -> Observable[GlobalConfigurationDTO]:
        return defer(lambda _: self._parse_config_file(self._platform_config.application_configuration_file())).pipe(
            ops.do_action(
                on_error=lambda error: log.error(
                    f"Failed to parse config file: {self._platform_config.application_configuration_file()}",
                    exc_info=error,
                )
            ),
        )

    def _parse_config_file(self, configuration_file: Path) -> Observable[GlobalConfigurationDTO]:
        """Parse configuration file and return GlobalConfigurationDTO observable."""
        self._configuration_migration_service.init_application_configuration()
        log.info(f"Start parsing configuration file: {configuration_file}")

        config_parser = configparser.RawConfigParser(
            inline_comment_prefixes=("#", ";"),
        )
        config_parser.read(configuration_file)
        section = config_parser[_CONFIG_SECTION]

        snoozes = self._get_snoozes(section)
        theme = self._get_theme(section)

        return self._get_calendars(config_parser).pipe(
            ops.map(lambda calendars: GlobalConfigurationDTO(snoozes, calendars, theme))
        )

    def _get_theme(self, section: SectionProxy) -> ThemeConfiguration:
        window_icon_theme: ThemeEnum
        systray_icon_theme: ThemeEnum

        window_icon_theme = self._read_theme(section, "theme.icon.window", ThemeEnum.GENERIC)
        systray_icon_theme = self._read_theme(section, "theme.icon.systray", ThemeEnum.GENERIC)

        return ThemeConfiguration(window_icon_theme, systray_icon_theme)

    def _get_calendars(self, config: configparser.RawConfigParser) -> Observable[list[CalendarConfigurationDTO]]:
        sections = [section for section in config.sections() if section != _CONFIG_SECTION]

        return from_iterable(sections).pipe(
            ops.flat_map(lambda calendar_section: self._parse_calendar_section(config, calendar_section)),
            ops.to_list(),
        )

    def _parse_calendar_section(
        self, config: configparser.RawConfigParser, calendar_section: str
    ) -> Observable[CalendarConfigurationDTO]:
        """Parse a single calendar section and return an Observable."""

        log.debug(f"Parsing calendar config section: {calendar_section}")
        section = config[calendar_section]

        return self._read_source(section).pipe(
            ops.map(lambda source: self._build_calendar_dto(section, source, calendar_section)),
            ops.catch(lambda error, _src: self._handle_parse_error(calendar_section, error)),
        )

    def _build_calendar_dto(
        self, section: SectionProxy, source: ISourceCalendar, calendar_section: str
    ) -> CalendarConfigurationDTO:
        """Parse section data and build CalendarConfigurationDTO with the given source."""
        name = read_str(section, "name", "unknown")
        force_alarms = self._get_alarms(section, "force_alarms", [])
        force_alarm_dates = self._get_alarms(section, "force_alarms_dates", [])
        default_alarms = self._get_alarms(section, "default_alarms", [timedelta(minutes=-15)])
        default_alarms_date = self._get_alarms(section, "default_alarms_dates", [])

        download_interval_int = read_int(section, "download.interval.minutes", 5)
        download_interval = timedelta(minutes=download_interval_int)

        missed_reminders_past_window = self._read_iso_duration(
            section, "missed.reminders.past_window", timedelta(hours=-24)
        )

        read_timeout = read_int(section, "timeout.read", 30)
        connection_timeout = read_int(section, "timeout.connection", 30)

        return CalendarConfigurationDTO(
            CalendarID(calendar_section),
            name,
            source,
            force_alarms,
            force_alarm_dates,
            default_alarms,
            default_alarms_date,
            download_interval,
            missed_reminders_past_window,
            HttpTimeout(connection_timeout, read_timeout),
        )

    def _handle_parse_error(self, calendar_section: str, error: Exception) -> Observable[CalendarConfigurationDTO]:
        """Handle errors from parsing a calendar section by logging and returning empty."""
        log.warning(f"Failed to parse section: {calendar_section}", exc_info=error)
        return empty()

    def _read_source(self, section: SectionProxy) -> Observable[ISourceCalendar]:
        return self._source_configuration_mapper_strategy.read(section)

    def _get_snoozes(self, section: SectionProxy) -> list[SnoozeDelta]:
        timedeltas = self._read_duration_array(section, "snooze", [])
        return [SnoozeDelta(td) for td in timedeltas]

    def _get_alarms(self, section: SectionProxy, key_name: str, fallback: list[timedelta]) -> list[AlarmDelta]:
        timedeltas = self._read_duration_array(section, key_name, fallback)
        return [AlarmDelta(td) for td in timedeltas]

    def _read_duration_array(self, section: SectionProxy, key_name: str, fallback: list[timedelta]) -> list[timedelta]:
        values = self._read_array(section, key_name)
        if values is None:
            return fallback

        res = []
        for value in values:
            duration = self._parse_iso_duration(value)
            if duration is not None:
                res.append(duration)

        return res

    def _read_array(self, section: SectionProxy, key_name: str) -> list[str] | None:
        value = section.get(key_name, None)
        if value:
            return list(map(lambda x: x.strip(), value.split(",")))
        else:
            return None

    def _read_iso_duration(self, section: SectionProxy, key_name: str, fallback: timedelta) -> timedelta:
        delta = self._read_iso_duration_strict(section, key_name)
        if delta is None:
            log.warning(f"Failed to parse config item: {key_name}, using fallback: {fallback}")
            return fallback
        else:
            return delta

    def _read_iso_duration_strict(self, section: SectionProxy, key_name: str) -> timedelta | None:
        try:
            value = section.get(key_name, None)
            if value is not None:
                delta = self._parse_iso_duration(value.upper())
                if delta is None:
                    log.warning(f"Failed to parse config item: {key_name}")
                return delta
            else:
                return None
        except Exception:
            log.warning(f"Failed to parse config item: {key_name}", exc_info=True)
            return None

    def _parse_iso_duration(self, duration: str) -> timedelta | None:
        try:
            delta = isodate.parse_duration(duration)
            if isinstance(delta, timedelta):
                return delta
            else:
                return None
        except Exception:
            log.warning(f"Failed to parse config item: {duration}", exc_info=True)
            return None

    def _read_theme(self, section: SectionProxy, key_name: str, fallback: ThemeEnum) -> ThemeEnum:
        try:
            theme = read_str(section, key_name, "").upper()
            if theme == "DARK":
                return ThemeEnum.DARK
            if theme == "LIGHT":
                return ThemeEnum.LIGHT
            if theme == "GENERIC":
                return ThemeEnum.GENERIC

            return fallback

        except Exception:
            log.warning(f"Failed to parse config item: {key_name}, using fallback: {fallback}", exc_info=True)
            return fallback
