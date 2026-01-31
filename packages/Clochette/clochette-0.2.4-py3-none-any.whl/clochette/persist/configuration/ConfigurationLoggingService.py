import configparser
from dataclasses import dataclass
from functools import cached_property

from clochette import log
from clochette.domain.entity.configuration.LoggingConfiguration import LoggingConfiguration
from clochette.persist.configuration.ConfigurationMigrationService import ConfigurationMigrationService
from clochette.persist.configuration.ConfigurationReadUtils import read_str, read_bool
from clochette.persist.configuration.PlatformConfigurationService import PlatformConfigurationService


@dataclass
class ConfigurationLoggingService:
    _platform_config: PlatformConfigurationService
    _configuration_migration_service: ConfigurationMigrationService
    CONFIG_SECTION = "Config"

    @cached_property
    def configuration(self) -> LoggingConfiguration:
        configuration_file = self._platform_config.logging_configuration_file()

        try:
            self._configuration_migration_service.init_logging_configuration()
            log.info(f"Start parsing configuration file: {configuration_file}", exc_info=True)
            configuration = configparser.ConfigParser(inline_comment_prefixes=("#", ";"), interpolation=None)
            configuration.read(configuration_file)
            section = configuration[ConfigurationLoggingService.CONFIG_SECTION]

            # logs config
            log_level = read_str(section, "log.level", "INFO").upper()
            enable_console_log = read_bool(section, "log.console.enabled", False)

            return LoggingConfiguration(log_level, enable_console_log)

        except Exception as e:
            log.error(f"Failed to parse config file: {configuration_file}", exc_info=True)
            raise e
