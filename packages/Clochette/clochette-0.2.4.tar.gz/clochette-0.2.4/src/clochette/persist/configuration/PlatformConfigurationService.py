from pathlib import Path

import platformdirs


class PlatformConfigurationService:
    APP_NAME = "clochette"
    AUTHOR = "sketyl"
    CONFIG_FILE = "clochette.config"
    LOGGING_FILE = "logging.config"

    def __init__(self) -> None:
        self.application_configuration_path().mkdir(parents=True, exist_ok=True)
        self.application_data_path().mkdir(parents=True, exist_ok=True)

    def application_configuration_path(self) -> Path:
        config = platformdirs.user_config_dir(
            PlatformConfigurationService.APP_NAME, PlatformConfigurationService.AUTHOR
        )
        return Path(config)

    def application_data_path(self) -> Path:
        data = platformdirs.user_data_dir(PlatformConfigurationService.APP_NAME, PlatformConfigurationService.AUTHOR)
        return Path(data)

    def application_configuration_file(self) -> Path:
        return self.application_configuration_path() / PlatformConfigurationService.CONFIG_FILE

    def logging_configuration_file(self) -> Path:
        return self.application_configuration_path() / PlatformConfigurationService.LOGGING_FILE
