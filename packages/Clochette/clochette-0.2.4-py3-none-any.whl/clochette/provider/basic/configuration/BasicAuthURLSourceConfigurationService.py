from configparser import SectionProxy

from clochette.application.service.provider.dto.IProviderConfigurationMapper import IProviderConfigurationMapper
from clochette.persist.configuration.ConfigurationReadUtils import read_str
from clochette.provider.basic.configuration.BasicAuthURLSource import BasicAuthURLSource


class BasicAuthURLSourceConfigurationService(IProviderConfigurationMapper[BasicAuthURLSource]):
    _PROVIDER_ID = "basic"

    def match(self, section: SectionProxy) -> bool:
        """Check if this mapper can handle the given configuration section"""
        authentication = read_str(section, "authentication", "").lower()
        return authentication == self._PROVIDER_ID

    def read(self, section: SectionProxy) -> BasicAuthURLSource:
        url = read_str(section, "url", "")
        return BasicAuthURLSource(url)

    def write(self, source: BasicAuthURLSource) -> dict[str, str]:
        return {
            "authentication": self._PROVIDER_ID,
            "url": source.url,
        }
