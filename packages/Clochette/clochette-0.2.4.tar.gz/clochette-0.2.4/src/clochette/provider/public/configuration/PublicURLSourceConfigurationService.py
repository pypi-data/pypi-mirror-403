from configparser import SectionProxy

from clochette.application.service.provider.dto.IProviderConfigurationMapper import IProviderConfigurationMapper
from clochette.persist.configuration.ConfigurationReadUtils import read_str
from clochette.provider.public.configuration.PublicURLSource import PublicURLSource


class PublicURLSourceConfigurationService(IProviderConfigurationMapper[PublicURLSource]):
    _PROVIDER_ID = "public"

    def match(self, section: SectionProxy) -> bool:
        """Check if this mapper can handle the given configuration section"""
        authentication = read_str(section, "authentication", "").lower()
        return authentication == self._PROVIDER_ID

    def read(self, section: SectionProxy) -> PublicURLSource:
        url = read_str(section, "url", "")
        return PublicURLSource(url)

    def write(self, source: PublicURLSource) -> dict[str, str]:
        return {
            "authentication": self._PROVIDER_ID,
            "url": source.url,
        }
