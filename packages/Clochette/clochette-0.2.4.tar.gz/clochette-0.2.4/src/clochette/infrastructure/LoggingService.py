import logging
from dataclasses import dataclass
from logging.handlers import TimedRotatingFileHandler

from clochette import log
from clochette.persist.configuration.ConfigurationLoggingService import ConfigurationLoggingService
from clochette.persist.configuration.PlatformConfigurationService import PlatformConfigurationService


@dataclass
class LoggingService:
    _platform_configuration_service: PlatformConfigurationService
    _configuration_logging_service: ConfigurationLoggingService

    def setup(self) -> None:
        configuration = self._configuration_logging_service.configuration

        # set log level
        log.setLevel(configuration.log_level)
        logging.getLogger("urllib3").setLevel(configuration.log_level)

        # Handler and formatter setup
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s():%(lineno)d - %(message)s"
        )

        # File handler with daily rollover (keep only 1 day)
        log_file = self._platform_configuration_service.application_data_path() / "clochette.log"
        file_handler = TimedRotatingFileHandler(str(log_file), when="midnight", interval=1, backupCount=0)
        file_handler.setFormatter(formatter)
        log.addHandler(file_handler)

        # set console handler
        if configuration.log_console_enabled:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            log.addHandler(console_handler)
