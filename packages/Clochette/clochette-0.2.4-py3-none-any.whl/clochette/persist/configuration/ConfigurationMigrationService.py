from dataclasses import dataclass

from clochette import log
from clochette.persist.configuration.ConfigurationWriterService import ConfigurationWriterService
from clochette.persist.configuration.PlatformConfigurationService import PlatformConfigurationService
from clochette.persist.configuration.dto.GlobalConfigurationDTO import GlobalConfigurationDTO


@dataclass
class ConfigurationMigrationService:
    _configuration_writer_service: ConfigurationWriterService
    _platform_configuration_service: PlatformConfigurationService

    def init_application_configuration(self) -> None:
        configuration_file = self._platform_configuration_service.application_configuration_file()

        if not configuration_file.exists():
            global_configuration = GlobalConfigurationDTO.default()
            self._configuration_writer_service.write(global_configuration).run()

    def init_logging_configuration(self) -> None:
        configuration_file = self._platform_configuration_service.logging_configuration_file()

        if not configuration_file.exists():
            configuration_content = """[Config]
# Set the desired log level. Default value is WARNING, possible values are: CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
# Use NOTSET if you want to completely disable the logs 
log.level=WARNING

# Enable the console logs. Default value is FALSE. Possible values are TRUE, FALSE
log.console.enabled=FALSE
"""

            configuration_file.write_text(configuration_content)
            log.info(f"Logging configuration file doesn't exist, creating it: {configuration_file}")
            # print in case logging hasn't been initialized yet
            print(f"Logging configuration file doesn't exist, creating it: {configuration_file}")
