from dataclasses import dataclass

from PySide6.QtCore import QCoreApplication

from clochette.application.service.provider.dto.ProviderDTO import ProviderDTO
from clochette.provider.public.configuration.PublicURLSourceConfigurationService import (
    PublicURLSourceConfigurationService,
)
from clochette.provider.public.download.PublicCalendarDownloaderService import (
    PublicCalendarDownloaderService,
)
from clochette.provider.public.dto.PublicProviderType import PublicProviderType
from clochette.provider.public.ui.QPublicAuthComponent import QPublicAuthComponent


@dataclass
class PublicProviderFactory:
    """Provider Factory for Public URL calendars."""

    _download_calendar: PublicCalendarDownloaderService
    _provider_configuration_mapper: PublicURLSourceConfigurationService
    _authentication_component: QPublicAuthComponent

    def create(self) -> ProviderDTO:
        """Factory method to create a PublicProviderDTO with all dependencies."""
        return ProviderDTO(
            download_calendar=self._download_calendar,
            provider_type=PublicProviderType(),
            provider_configuration_mapper=self._provider_configuration_mapper,
            display_name=QCoreApplication.translate("PublicProviderFactory", "Public URL"),
            authentication_component=self._authentication_component,
        )
