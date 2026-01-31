from dataclasses import dataclass

from clochette.application.service.provider.dto.IAuthenticationComponent import IAuthenticationComponent
from clochette.application.service.provider.dto.IDownloadCalendar import IDownloadCalendar
from clochette.application.service.provider.dto.IProviderConfigurationMapper import IProviderConfigurationMapper
from clochette.application.service.provider.dto.ProviderType import ProviderType


@dataclass
class ProviderDTO:
    download_calendar: IDownloadCalendar
    provider_type: ProviderType
    provider_configuration_mapper: IProviderConfigurationMapper
    display_name: str
    authentication_component: IAuthenticationComponent
