from dataclasses import dataclass

from clochette.application.service.provider.dto.ProviderDTO import ProviderDTO
from clochette.provider.microsoft.configuration.MicrosoftSourceConfigurationService import (
    MicrosoftSourceConfigurationService,
)
from clochette.provider.microsoft.download.MicrosoftCalendarDownloaderService import (
    MicrosoftCalendarDownloaderService,
)
from clochette.provider.microsoft.dto.MicrosoftProviderType import MicrosoftProviderType
from clochette.provider.microsoft.ui.QMicrosoftOAuth2Component import (
    QMicrosoftOAuth2Component,
)


@dataclass
class MicrosoftProviderFactory:
    """Provider Factory for Microsoft calendars."""

    _download_calendar: MicrosoftCalendarDownloaderService
    _provider_configuration_mapper: MicrosoftSourceConfigurationService
    _authentication_component: QMicrosoftOAuth2Component

    def create(self) -> ProviderDTO:
        """Factory method to create a MicrosoftProviderDTO with all dependencies."""
        return ProviderDTO(
            download_calendar=self._download_calendar,
            provider_type=MicrosoftProviderType(),
            provider_configuration_mapper=self._provider_configuration_mapper,
            display_name="Microsoft",
            authentication_component=self._authentication_component,
        )
