from dataclasses import dataclass

from PySide6.QtCore import QCoreApplication

from clochette.application.service.provider.dto.ProviderDTO import ProviderDTO
from clochette.provider.basic.configuration.BasicAuthURLSourceConfigurationService import (
    BasicAuthURLSourceConfigurationService,
)
from clochette.provider.basic.download.BasicAuthCalendarDownloaderService import (
    BasicAuthCalendarDownloaderService,
)
from clochette.provider.basic.dto.BasicProviderType import BasicProviderType
from clochette.provider.basic.ui.QBasicAuthComponent import QBasicAuthComponent


@dataclass
class BasicProviderFactory:
    """Provider Factory for Basic Authentication calendars."""

    _download_calendar: BasicAuthCalendarDownloaderService
    _provider_configuration_mapper: BasicAuthURLSourceConfigurationService
    _authentication_component: QBasicAuthComponent

    def create(self) -> ProviderDTO:
        """Factory method to create a BasicProviderDTO with all dependencies."""
        return ProviderDTO(
            download_calendar=self._download_calendar,
            provider_type=BasicProviderType(),
            provider_configuration_mapper=self._provider_configuration_mapper,
            display_name=QCoreApplication.translate("BasicProviderFactory", "Basic Auth"),
            authentication_component=self._authentication_component,
        )
