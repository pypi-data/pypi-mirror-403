from dataclasses import dataclass

from clochette.application.service.provider.dto.ProviderDTO import ProviderDTO
from clochette.provider.google.configuration.GoogleSourceConfigurationService import (
    GoogleSourceConfigurationService,
)
from clochette.provider.google.download.GoogleCalendarDownloaderService import (
    GoogleCalendarDownloaderService,
)
from clochette.provider.google.dto.GoogleProviderType import GoogleProviderType
from clochette.provider.google.ui.QGoogleOAuth2Component import QGoogleOAuth2Component


@dataclass
class GoogleProviderFactory:
    """Provider Factory for Google calendars."""

    _download_calendar: GoogleCalendarDownloaderService
    _provider_configuration_mapper: GoogleSourceConfigurationService
    _authentication_component: QGoogleOAuth2Component

    def create(self) -> ProviderDTO:
        """Factory method to create a GoogleProviderDTO with all dependencies."""
        return ProviderDTO(
            download_calendar=self._download_calendar,
            provider_type=GoogleProviderType(),
            provider_configuration_mapper=self._provider_configuration_mapper,
            display_name="Google",
            authentication_component=self._authentication_component,
        )
